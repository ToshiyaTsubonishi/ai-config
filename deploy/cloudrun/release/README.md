# GHCR Release Path

企業環境の production で `docker login` / `gcloud auth` / GitHub login ができない前提では、
deploy 前に別の build-capable environment で image を完成させ、digest 固定で渡す必要があります。

このディレクトリの `publish_ghcr_release.py` は、次の 2 image をまとめて build / publish します。

- `ai-config-selector-serving`
- `ai-config-provider`

さらに、Cloud Run へ貼るための pinned digest と provenance を
`ghcr-release-manifest.json` にまとめて出力します。

## 使いどころ

- staging で成功した repo state を production 用に凍結したい
- production 環境では build も registry login もできない
- deploy 時は GitHub Packages を一時的に public にして pull させる

## 前提

- build を実行するマシンでは Docker と Node.js が使える
- `ghcr.io` へ push できる token で事前に `docker login ghcr.io` 済み
- sibling repo `../ai-config-provider` が存在する
- `ai-config-provider` の private checkout が必要な GitHub Actions では、
  `AI_CONFIG_PROVIDER_REPO_TOKEN` secret を設定する

## ローカル publish

```bash
cd /Users/tsytbns/Documents/GitHub/ai-config

python deploy/cloudrun/release/publish_ghcr_release.py \
  --github-owner ToshiyaTsubonishi \
  --provider-repo ../ai-config-provider \
  --push \
  --output .artifacts/ghcr-release-manifest.json
```

このコマンドは次を順番に実行します。

1. `ai-config-provider` で `npm ci`
2. `npm run bundle:from-ai-config -- --ai-config-dir ../ai-config --output-dir provider-bundle`
3. selector/provider image を `docker buildx build --push`
4. pushed digest と commit SHA / provider-bundle version を manifest に保存

step 2 では `provider-bundle/.index/provider-bundle-metadata.json` も更新され、
manifest にはその `bundle_version` と source `ai-config` commit SHA が入ります。

clean checkout で `ai-config/.index/records.json` が存在しない場合でも、
script は selector index を先に bootstrap してから provider bundle を作ります。

もし local Docker が `DOCKER_CONFIG` の都合で `buildx` を見失う環境でも、
script は `docker build` + `docker push` へ fallback します。

## 生成物

manifest には次が入ります。

- selector/provider の `ghcr.io/...@sha256:...`
- selector/provider commit SHA
- provider-bundle version
- provider-bundle source `ai-config` commit SHA
- Cloud Run renderer にそのまま入れられる `cloudrun.images` / `cloudrun.provenance`

例:

```json
{
  "selector": {
    "image_ref": "ghcr.io/toshiyatsubonishi/ai-config-selector-serving@sha256:..."
  },
  "provider": {
    "image_ref": "ghcr.io/toshiyatsubonishi/ai-config-provider@sha256:...",
    "bundle_version": "0fa50eb0b1ea-7c12f6aae5b8"
  },
  "cloudrun": {
    "images": {
      "selector": "ghcr.io/toshiyatsubonishi/ai-config-selector-serving@sha256:...",
      "provider": "ghcr.io/toshiyatsubonishi/ai-config-provider@sha256:..."
    },
    "provenance": {
      "selector_commit_sha": "...",
      "provider_commit_sha": "...",
      "provider_bundle_version": "...",
      "provider_bundle_source_commit_sha": "..."
    }
  },
  "distribution": {
    "temporary_public_required_for_constrained_production": true
  }
}
```

## Cloud Run への渡し方

- `deploy/cloudrun/staging/stack.example.yaml` または
  `deploy/cloudrun/production/stack.example.yaml` の
  `images.selector` / `images.provider` には manifest の digest ref を入れる
- provenance も manifest の `cloudrun.provenance` をそのまま移す
- production が GHCR に認証できない場合は、GitHub Packages の package visibility を
  一時的に `public` にして deploy し、完了後に戻す

GUI deploy だけで進める場合も、Cloud Run に貼る image URL は tag ではなく
`@sha256:` の digest ref を使ってください。

`--github-owner` は GitHub owner 名をそのまま渡して問題ありませんが、
GHCR 上の repository path は release script が lowercase に正規化します。

## GitHub Actions

`ai-config` repo には `publish-ghcr-release.yml` を用意しています。
GitHub Actions から実行する場合も、最終的な source of truth は
upload artifact された `ghcr-release-manifest.json` です。
