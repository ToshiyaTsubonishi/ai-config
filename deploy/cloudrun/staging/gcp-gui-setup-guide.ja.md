# `abiding-aspect-457603-m8` 用 GCP GUI セットアップガイド

このガイドは、production と別 project の
`abiding-aspect-457603-m8` に selector/provider/Open WebUI の staging stack を
作るための最短手順です。

対象の Cloud Run service は次の 5 つです。

1. `ai-config-selector`
2. `ai-config-provider`
3. `ai-config-mcpo`
4. `ai-config-provider-mcpo`
5. `open-webui`

`ai-harness` は phase 1 では Cloud Run に載せません。future phase の thin HTTP
wrapper contract は sibling repo の `ai-harness/docs/remote-wrapper-contract.md`
を参照してください。

## 1. 先に決めること

- Project ID: `abiding-aspect-457603-m8`
- Region: `asia-northeast1`
- Cloud SQL instance: `open-web-ui`
- Open WebUI bucket: `open-webui-abiding-aspect-457603-m8`
- SearXNG bucket: `searxng-abiding-aspect-457603-m8`
- service account:
  `open-webui-runner@abiding-aspect-457603-m8.iam.gserviceaccount.com`

Cloud Console の「プロジェクト情報」から project number を確認し、
`deploy/cloudrun/staging/stack.example.yaml` の `project_number` に入れます。

## 2. Render 資材を作る

```bash
cd /Users/tsytbns/Documents/GitHub/ai-config
python deploy/cloudrun/staging/render_stack.py \
  --config deploy/cloudrun/staging/stack.example.yaml \
  --output-dir deploy/cloudrun/staging/rendered
```

`rendered/stack-metadata.json` に、Cloud Run URL、redirect URI、render 済みファイル一覧が出ます。

Open WebUI の secret にそのまま入れる JSON は次です。

- `deploy/cloudrun/staging/rendered/open-webui.tool-server-connections.json`

まだ `MCPO_API_KEY` を埋めていない場合は placeholder のままなので、Secret Manager に
入れる前に差し替えます。

## 3. Secret Manager を用意する

staging project に次の secrets を作成します。

- `MCPO_API_KEY`
- `OPENWEBUI_TOOL_SERVER_CONNECTIONS`
- `WEBUI_SECRET_KEY`
- `GEMINI_API_KEY`
- `open_webui_oauth_client_id`
- `open_webui_oauth_client_secret`
- `DATABASE_URL`
- `OPEN_TERMINAL_API_KEY`
- `SEARXNG_SECRET`

`OPENWEBUI_TOOL_SERVER_CONNECTIONS` の payload には selector/provider の 2 接続だけを入れます。
Open WebUI から `/mcp` を直接参照させず、必ず MCPO の `/openapi.json` を使います。

## 4. GUI で Cloud Run に適用する

render 済みファイルは次です。

- `ai-config-selector.service.yaml`
- `ai-config-provider.service.yaml`
- `ai-config-mcpo.service.yaml`
- `ai-config-provider-mcpo.service.yaml`
- `open-webui.service.mcpo.yaml`

Cloud Console の Cloud Run から `YAML で置換` を使うか、認証済み環境なら
`apply_rendered_stack.sh` を使います。

```bash
./deploy/cloudrun/staging/apply_rendered_stack.sh \
  deploy/cloudrun/staging/rendered \
  abiding-aspect-457603-m8 \
  asia-northeast1
```

## 5. GUI で確認すること

Cloud Run:

- `ai-config-selector` が `/healthz` と `/readyz` で healthy
- `ai-config-provider` が `/healthz` と `/readyz` で healthy
- `ai-config-mcpo` が起動している
- `ai-config-provider-mcpo` が起動している
- `open-webui` が separate project の DB / bucket / secrets を見ている

Secret Manager:

- `open-webui-runner@abiding-aspect-457603-m8.iam.gserviceaccount.com` に
  `Secret Manager Secret Accessor` が付いている
- `OPENWEBUI_TOOL_SERVER_CONNECTIONS` の JSON が 2 接続構成になっている

OAuth:

- redirect URI が
  `https://open-webui-<PROJECT_NUMBER>.asia-northeast1.run.app/oauth/google/callback`
  になっている

## 6. Open WebUI で確認すること

1. staging Open WebUI を開く
2. `+` メニューで `ai-config (MCPO)` と `ai-config-provider (MCPO)` が見える
3. 両方を有効化できる
4. selector で候補を探し、provider で skill/MCP 実体を読める

## 7. 失敗しやすい点

- project number を埋めずに render している
- `TOOL_SERVER_CONNECTIONS` に 1 接続しか入っていない
- Open WebUI から provider `/mcp` を直接つないでいる
- staging project なのに production の DB / bucket / secrets を参照している
- Google OAuth redirect URI が production URL のまま
