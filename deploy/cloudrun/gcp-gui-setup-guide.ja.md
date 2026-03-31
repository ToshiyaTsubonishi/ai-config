# GCP コンソールで進める Open WebUI + MCPO + ai-config セットアップガイド

このガイドを最後まで終えると、Open WebUI の入力欄横にある `＋` メニューから `ai-config (MCPO)` を有効化できるようになります。

やることは大きく 4 つです。

1. `ai-config-selector-serving` のコンテナイメージを用意する
2. Cloud Run に `ai-config-selector` と `ai-config-mcpo` を作る
3. 既存の `open-webui` サービスに接続設定を追加する
4. Open WebUI 画面から接続できることを確認する

このガイドは「できるだけ GCP コンソール GUI で進めたい」人向けに書いています。今回の会社環境を前提に、GitHub を GCP に接続しない、`gcloud` は使いません、という条件で組み直しています。

つまり、この版のガイドでは GCP の中で build はしません。`ai-config-selector-serving` は事前にコンテナイメージを用意して、そのイメージ URL を Cloud Run に入れる方式で進めます。

## 0. 先に全体像をつかむ

今回の接続は次の流れです。

1. Open WebUI は `ai-config-mcpo` に接続する
2. `ai-config-mcpo` は `ai-config-selector` の `/mcp` に接続する
3. `ai-config-selector` は repo に入っている `.index` を使って selector の tool を返す

サービスの役割は次のとおりです。

- `open-webui`
  既存の本体。今回ここに接続設定だけ追加します
- `ai-config-selector`
  `ai-config-selector-serving` を Cloud Run で動かすサービスです
- `ai-config-mcpo`
  MCPO を Cloud Run で動かすサービスです。Open WebUI からはこの URL だけを使います

## 1. このガイドで使う値

まず、今回のセットアップで使う値を整理します。

| 項目 | 値 |
|---|---|
| GCP Project ID | `sbi-art-auction` |
| GCP Project Number | `424287527578` |
| Region | `asia-northeast1` |
| Open WebUI のサービス名 | `open-webui` |
| ai-config selector のサービス名 | `ai-config-selector` |
| MCPO のサービス名 | `ai-config-mcpo` |
| 既存の Service Account | `open-webui-runner@sbi-art-auction.iam.gserviceaccount.com` |
| ai-config selector image URL | あなたが事前に用意したイメージ URL |
| ai-config selector URL | `https://ai-config-selector-424287527578.asia-northeast1.run.app` |
| ai-config selector MCP URL | `https://ai-config-selector-424287527578.asia-northeast1.run.app/mcp` |
| MCPO URL | `https://ai-config-mcpo-424287527578.asia-northeast1.run.app` |

今回新しく作る Secret は 2 つです。

- `MCPO_API_KEY`
- `OPENWEBUI_TOOL_SERVER_CONNECTIONS`

すでに `open-webui` が動いているので、次の Secret は既存のまま使う想定です。

- `WEBUI_SECRET_KEY`
- `GEMINI_API_KEY`
- `open_webui_oauth_client_id`
- `open_webui_oauth_client_secret`
- `DATABASE_URL`
- `OPEN_TERMINAL_API_KEY`
- `SEARXNG_SECRET`

## 2. 先に確認しておくこと

GCP コンソールで、次の API が有効か確認します。

1. GCP コンソールで `API とサービス` を開きます
2. `有効な API とサービス` を開きます
3. 次が有効になっているか確認します

- Cloud Run Admin API
- Secret Manager API

次の API は、あなたのイメージ置き場に応じて必要なら確認してください。

- Artifact Registry API

もし無効なものがあれば `ライブラリ` から検索して有効化してください。

次に、今回使うサービスアカウントを確認します。

1. `IAM と管理` → `サービス アカウント` を開きます
2. `open-webui-runner@sbi-art-auction.iam.gserviceaccount.com` があることを確認します

このサービスアカウントは、Cloud Run から Secret を読むために使います。

## 3. `ai-config-selector-serving` のイメージを事前に用意する

ここが今回のいちばん大事な前提です。

このガイドでは GitHub を GCP に接続しない、`gcloud` は使いません、という条件なので、GCP コンソールの中だけでこの repo の Dockerfile を build する流れは main route にしません。

その代わり、`ai-config-selector-serving` は事前にコンテナイメージを用意しておきます。

使える置き場の例:

- GHCR
- Docker Hub
- 社内レジストリ
- すでにあなたの project で使える Artifact Registry

いちばん大事なのは「Cloud Run が pull できる完成済みイメージ URL を 1 本持っていること」です。

### 3-1. まず決めること

あなたが使うイメージ URL を 1 つ決めて、手元にメモしてください。

例:

```text
ghcr.io/your-org/ai-config-selector-serving:main
```

または

```text
docker.io/your-org/ai-config-selector-serving:main
```

または

```text
asia-northeast1-docker.pkg.dev/sbi-art-auction/cloud-run/ai-config-selector-serving:main
```

### 3-2. どのイメージ URL を使えばいいかわからないとき

次のどれかが現実的です。

1. すでに別の許可された環境で build 済みのイメージ URL をもらう
2. 社内の CI/CD や社内レジストリに一度だけ image を置いてもらう
3. すでに GCP 側にある Artifact Registry の書き込み権限を持つ人に初回 build だけ依頼する

この guide の残りは、イメージ URL が 1 本決まっていれば、そのまま進められます。

### 3-3. `ghcr` リポジトリについて

以前のメモでは `asia-northeast1-docker.pkg.dev/sbi-art-auction/ghcr/ai-config/ai-config-selector-serving:main` を例にしていました。

これはそのまま使える場合もありますが、会社環境では次のどちらかです。

1. すでにそのパスへ push 済みで、そのまま使える
2. `ghcr` がミラー用や read-only で使えない

後者なら無理に合わせず、あなたが実際に pull できるイメージ URL を優先してください。GUI で Cloud Run に入れる値は、YAML 例よりも「実際に存在する image URL」のほうが優先です。

## 4. Secret Manager で新しい Secret を作る

今回は新しく 2 つ作ります。

- `MCPO_API_KEY`
- `OPENWEBUI_TOOL_SERVER_CONNECTIONS`

### 4-1. `MCPO_API_KEY` を作る

1. GCP コンソールで `Secret Manager` を開きます
2. `シークレットを作成` を押します
3. `名前` に `MCPO_API_KEY` を入れます
4. `シークレットの値` に十分長いランダム文字列を入れます

おすすめ:

- 32 文字以上
- 英数字ベースで OK
- パスワードマネージャーの「強いパスワード生成」を使うのが簡単

例:

```text
4f3e0e3b92284d7f9a3f6d5fca2f6b29d6b0e4d58c4a8f9d8d4a72a3b3f95c10
```

5. `作成` を押します

### 4-2. `OPENWEBUI_TOOL_SERVER_CONNECTIONS` を作る

Open WebUI は、MCPO への接続設定を JSON で受け取ります。

この repo にはサンプルファイルがあります。

- `deploy/cloudrun/open-webui.tool-server-connections.example.json`

中身はこれです。

```json
[
  {
    "type": "openapi",
    "url": "https://ai-config-mcpo-424287527578.asia-northeast1.run.app",
    "spec_type": "url",
    "spec": "",
    "path": "openapi.json",
    "auth_type": "bearer",
    "key": "__REPLACE_WITH_MCPO_API_KEY__",
    "config": {
      "enable": true
    },
    "info": {
      "id": "ai-config-mcpo",
      "name": "ai-config (MCPO)",
      "description": "ai-config selector tools exposed through MCPO on Cloud Run"
    }
  }
]
```

この `key` の値だけを、さっき作った `MCPO_API_KEY` の実値に置き換えてください。

そのうえで次の手順で Secret を作ります。

1. `Secret Manager` で `シークレットを作成` を押します
2. `名前` に `OPENWEBUI_TOOL_SERVER_CONNECTIONS` を入れます
3. `シークレットの値` に、置き換え済み JSON 全体をそのまま貼り付けます
4. `作成` を押します

### 4-3. サービスアカウントに Secret 読み取り権限をつける

これは忘れやすいです。

Cloud Run から Secret を読むには、サービスアカウントに `Secret Manager Secret Accessor` が必要です。

対象の Secret は次の 2 つです。

- `MCPO_API_KEY`
- `OPENWEBUI_TOOL_SERVER_CONNECTIONS`

手順:

1. `Secret Manager` で `MCPO_API_KEY` を開きます
2. `権限` タブを開きます
3. `アクセスを許可` を押します
4. プリンシパルに `open-webui-runner@sbi-art-auction.iam.gserviceaccount.com` を入れます
5. ロールに `Secret Manager Secret Accessor` を選びます
6. 保存します
7. `OPENWEBUI_TOOL_SERVER_CONNECTIONS` でも同じ操作をします

## 5. Cloud Run に `ai-config-selector` を作る

ここでは `deploy/cloudrun/ai-config-selector.service.yaml` の内容を GUI で手入力するイメージです。

### 5-1. サービスを新規作成する

1. GCP コンソールで `Cloud Run` を開きます
2. `サービスを作成` を押します
3. `既存のコンテナ イメージをデプロイ` を選びます
4. 次の値を入れます

| 項目 | 値 |
|---|---|
| サービス名 | `ai-config-selector` |
| リージョン | `asia-northeast1` |
| コンテナ イメージ URL | 3 章で決めた `ai-config-selector-serving` のイメージ URL |

もし迷ったら、「今あなたの環境で本当に pull できる完成済み image URL」をそのまま入れてください。

### 5-2. 認証とネットワーク

1. `認証` は `未認証の呼び出しを許可` にします
2. `Ingress` は `すべて` にします

今回の設計では `ai-config-selector` 自体は public にし、アプリ利用時の入口認証は MCPO の API key に寄せています。

### 5-3. コンテナ設定

`コンテナ` の詳細で次を確認します。

| 項目 | 値 |
|---|---|
| コンテナポート | `8080` |
| コマンド | 空欄のままで OK |
| 引数 | 空欄のままで OK |
| 環境変数 | 追加不要 |
| メモリ | `1 GiB` |
| CPU | `1` |

### 5-4. 自動スケールとリクエスト

`コンテナ、ボリューム、ネットワーキング、セキュリティ` の詳細で、できれば次に合わせます。

| 項目 | 値 |
|---|---|
| 最大インスタンス数 | `1` |
| 同時実行数 | `5` |
| タイムアウト | `900` 秒 |
| サービス アカウント | `open-webui-runner@sbi-art-auction.iam.gserviceaccount.com` |

### 5-5. ヘルスチェック

GUI で設定できる場合は、次に合わせておくと後で見やすいです。

| 種類 | 値 |
|---|---|
| Liveness | HTTP GET `/healthz` on `8080` |
| Startup | TCP on `8080` |

### 5-6. デプロイする

1. `作成` もしくは `デプロイ` を押します
2. デプロイが終わったらサービス URL を開きます
3. `https://ai-config-selector-424287527578.asia-northeast1.run.app/healthz` にアクセスして `{"status":"ok"}` が見えれば OK です

`/readyz` も `200` ならさらに安心です。

## 6. Cloud Run に `ai-config-mcpo` を作る

次は MCPO です。Open WebUI はこのサービスを見に行きます。

### 6-1. サービスを新規作成する

1. `Cloud Run` → `サービスを作成`
2. `既存のコンテナ イメージをデプロイ`
3. 次の値を入れます

| 項目 | 値 |
|---|---|
| サービス名 | `ai-config-mcpo` |
| リージョン | `asia-northeast1` |
| コンテナ イメージ URL | `ghcr.io/open-webui/mcpo:v0.0.20` |

### 6-2. 認証とネットワーク

1. `認証` は `未認証の呼び出しを許可` にします
2. `Ingress` は `すべて` にします

### 6-3. コマンドと引数を設定する

MCPO はそのままでは `ai-config-selector` につながらないので、起動コマンドを入れます。

`コンテナ` 設定で次を入れてください。

| 項目 | 値 |
|---|---|
| コンテナポート | `8080` |
| コマンド | `/bin/sh` |
| 引数 1 | `-c` |
| 引数 2 | `exec mcpo --host 0.0.0.0 --port "${PORT:-8080}" --api-key "$MCPO_API_KEY" --strict-auth --server-type "streamable-http" -- "$AI_CONFIG_SELECTOR_MCP_URL"` |

### 6-4. 環境変数と Secret を設定する

`変数とシークレット` で次を設定します。

通常の環境変数:

| 名前 | 値 |
|---|---|
| `AI_CONFIG_SELECTOR_MCP_URL` | `https://ai-config-selector-424287527578.asia-northeast1.run.app/mcp` |

Secret 参照:

| 環境変数名 | Secret | バージョン |
|---|---|---|
| `MCPO_API_KEY` | `MCPO_API_KEY` | `latest` |

### 6-5. リソース設定

`ai-config-selector` と同じく、まずは次で十分です。

| 項目 | 値 |
|---|---|
| メモリ | `1 GiB` |
| CPU | `1` |
| 最大インスタンス数 | `1` |
| 同時実行数 | `5` |
| タイムアウト | `900` 秒 |
| サービス アカウント | `open-webui-runner@sbi-art-auction.iam.gserviceaccount.com` |

### 6-6. デプロイして確認する

1. `作成` もしくは `デプロイ` を押します
2. Cloud Run のログにエラーが出ていないことを確認します
3. できればブラウザで `https://ai-config-mcpo-424287527578.asia-northeast1.run.app` を開きます

`--strict-auth` を付けているので、そのままでは OpenAPI ドキュメントは見えないか、認証エラーになります。これは正常です。

## 7. 既存の `open-webui` サービスに接続設定を追加する

ここが一番大事です。しかも `open-webui` はマルチコンテナなので、必ず `open-webui-1` のコンテナにだけ設定を入れてください。

### 7-1. 既存サービスを編集する

1. `Cloud Run` で `open-webui` を開きます
2. `編集して新しいリビジョンをデプロイ` を押します
3. `コンテナ` 一覧から `open-webui-1` を選びます

`open-terminal-1` と `searxng-1` は今回触りません。

### 7-2. 追加する環境変数

`変数とシークレット` で、次の通常環境変数を追加します。

| 名前 | 値 |
|---|---|
| `ENABLE_PERSISTENT_CONFIG` | `False` |
| `ENABLE_OAUTH_PERSISTENT_CONFIG` | `False` |
| `ENABLE_LOGIN_FORM` | `False` |
| `ENABLE_DIRECT_CONNECTIONS` | `True` |

意味は次のとおりです。

- `ENABLE_PERSISTENT_CONFIG=False`
  Open WebUI の一部設定を DB ではなく env から毎回読むようにします
- `ENABLE_OAUTH_PERSISTENT_CONFIG=False`
  OAuth 関連も env を正にします
- `ENABLE_LOGIN_FORM=False`
  `ENABLE_OAUTH_SIGNUP=True` と両立させるために必要です。これが `True` のままだとログイン不能になることがあります
- `ENABLE_DIRECT_CONNECTIONS=True`
  OpenAPI / MCPO 系の接続定義を使えるようにします

### 7-3. 追加する Secret 参照

同じ画面で、次の Secret を環境変数として追加します。

| 環境変数名 | Secret | バージョン |
|---|---|---|
| `TOOL_SERVER_CONNECTIONS` | `OPENWEBUI_TOOL_SERVER_CONNECTIONS` | `latest` |

この 1 行が、Open WebUI に `ai-config (MCPO)` を見せるための本体です。

### 7-4. 既存設定は変えない

次の既存設定はそのままにしてください。

- Google OAuth の設定
- Cloud SQL の設定
- GCS の設定
- SearXNG の設定
- Open Terminal の設定

この repo の `deploy/cloudrun/open-webui.service.mcpo.yaml` は、現在の exported YAML に今回必要な差分だけ足したものです。不安ならそのファイルを横に置きながら GUI を埋めると迷いにくいです。

### 7-5. デプロイする

1. `デプロイ` を押します
2. 新しいリビジョンが `Ready` になるまで待ちます
3. Open WebUI にブラウザで入り直します

## 8. Open WebUI の画面で接続を確認する

ここは「設定したのに見えない」と思いやすいポイントです。

Open WebUI の global tool server は、管理者が登録していてもユーザー画面では最初から常時表示されません。ユーザーごとに明示的に有効化する必要があります。

### 8-1. まずログインする

1. `https://open-webui-424287527578.asia-northeast1.run.app` を開きます
2. Google OAuth でログインします

`ENABLE_LOGIN_FORM=False` にしたので、メールアドレス / パスワード入力欄が消えていても正常です。

### 8-2. `ai-config (MCPO)` を有効化する

1. 新しいチャットを開きます
2. 入力欄の横にある `＋` を押します
3. Global Tool Servers の一覧に `ai-config (MCPO)` が出ることを確認します
4. それを ON にします

この操作をしないと、global tool server は隠れたままです。

### 8-3. 試しに使ってみる

最初の確認としては、次のような軽い依頼がおすすめです。

```text
この環境で使える ai-config 系のツールを教えて
```

または

```text
Cloud Run デプロイに関係するツールを探して
```

うまくいけば、Open WebUI から MCPO 経由で ai-config のツール呼び出しが走ります。

## 9. 詰まりやすいポイントと対処

### 症状 1. `ai-config-selector` が Ready にならない

よくある原因:

- 受け取ったイメージが古い
- イメージ自体が正しく build されていない
- イメージ URL が違う

見る場所:

1. image を用意した担当者に、どの image URL / tag を使うべきか確認する
2. `Cloud Run` → `ai-config-selector` → `ログ`

### 症状 2. `ai-config-mcpo` は動くが Open WebUI から接続できない

よくある原因:

- `AI_CONFIG_SELECTOR_MCP_URL` の値が間違っている
- `MCPO_API_KEY` が空
- `TOOL_SERVER_CONNECTIONS` の `key` が MCPO の API key と一致していない

まず確認する場所:

1. `Cloud Run` → `ai-config-mcpo` → `変数とシークレット`
2. `Secret Manager` → `MCPO_API_KEY`
3. `Secret Manager` → `OPENWEBUI_TOOL_SERVER_CONNECTIONS`

### 症状 3. Open WebUI にログインできなくなった

よくある原因:

- `ENABLE_OAUTH_SIGNUP=True` のまま `ENABLE_LOGIN_FORM=False` を入れていない
- OAuth 設定が DB 側と env 側で食い違っている

今回の推奨値:

- `ENABLE_PERSISTENT_CONFIG=False`
- `ENABLE_OAUTH_PERSISTENT_CONFIG=False`
- `ENABLE_LOGIN_FORM=False`
- `ENABLE_OAUTH_SIGNUP=True`

### 症状 4. `ai-config (MCPO)` が UI に見えない

よくある原因:

- `TOOL_SERVER_CONNECTIONS` の JSON が壊れている
- `open-webui-1` ではなく別コンテナに設定してしまった
- まだ `＋` メニューで有効化していない

確認する順番:

1. `Cloud Run` の `open-webui` で `open-webui-1` にだけ設定したか確認する
2. `Secret Manager` で JSON が valid か見る
3. Open WebUI で `＋` を押して global tool server を ON にする

### 症状 5. Secret が読めない

よくある原因:

- `MCPO_API_KEY` または `OPENWEBUI_TOOL_SERVER_CONNECTIONS` に権限がない

確認する場所:

1. `Secret Manager` → 対象 Secret → `権限`
2. `open-webui-runner@sbi-art-auction.iam.gserviceaccount.com` に `Secret Manager Secret Accessor` が付いているかを見る

## 10. 最低限のチェックリスト

ここまで終わったら、次だけ確認してください。

- `ai-config-selector-serving` の image URL が 1 本決まっている
- Cloud Run の `ai-config-selector` が `Ready`
- Cloud Run の `ai-config-mcpo` が `Ready`
- `Secret Manager` に `MCPO_API_KEY` がある
- `Secret Manager` に `OPENWEBUI_TOOL_SERVER_CONNECTIONS` がある
- `open-webui` の `open-webui-1` に `TOOL_SERVER_CONNECTIONS` Secret が入っている
- Open WebUI 画面の `＋` から `ai-config (MCPO)` を ON にできる

## 11. この guide で参照している repo 内ファイル

設定の正本として見るファイルは次です。

- `deploy/cloudrun/ai-config-selector.service.yaml`
- `deploy/cloudrun/ai-config-mcpo.service.yaml`
- `deploy/cloudrun/open-webui.service.mcpo.yaml`
- `deploy/cloudrun/open-webui.tool-server-connections.example.json`
- `deploy/cloudrun/README.md`

## 12. 参考ドキュメント

外部ドキュメント:

- Cloud Run deploy: `https://cloud.google.com/run/docs/deploying`
- Cloud Run secrets: `https://cloud.google.com/run/docs/configuring/services/secrets`
- Artifact Registry Docker images: `https://cloud.google.com/artifact-registry/docs/docker/store-docker-container-images`
- Open WebUI env config: `https://docs.openwebui.com/reference/env-configuration/`
- Open WebUI MCP / OpenAPI tools: `https://docs.openwebui.com/features/extensibility/plugin/tools/openapi-servers/open-webui/`
- MCPO README: `https://github.com/open-webui/mcpo`

もし途中で画面項目の場所が少し違って見えたら、GCP コンソールの UI 更新によることがあります。その場合でも、サービス名、Secret 名、環境変数名、URL、コマンドはこのガイドの値を正として進めれば大きくは外れません。
