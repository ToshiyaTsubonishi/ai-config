# Cloud Run selector-serving

Cloud Run runtime は `skills/`、`config/`、`.index/` を read-only に使うだけです。`sync-manifest` と `ai-config-index` は runtime では実行せず、image build 時に完了させます。

## Build

```bash
docker build -f deploy/cloudrun/Dockerfile -t ai-config-selector-serving:local .
```

Cloud Build を使う場合:

```bash
gcloud builds submit \
  --tag REGION-docker.pkg.dev/PROJECT_ID/REPOSITORY/ai-config-selector-serving:TAG \
  -f deploy/cloudrun/Dockerfile \
  .
```

## Deploy

```bash
gcloud run deploy ai-config-selector \
  --image REGION-docker.pkg.dev/PROJECT_ID/REPOSITORY/ai-config-selector-serving:TAG \
  --region REGION \
  --platform managed \
  --port 8080
```

認証、ingress、perimeter 制御はこの repo の scope 外です。production では Cloud Run 側の policy を別途設定してください。

## Runtime contract

- entrypoint は `ai-config-selector-serving`
- MCP endpoint は `/mcp`
- liveness は `/healthz`
- readiness は `/readyz`
- provider bridge は `/catalog/tool-detail?tool_id=...`
- startup 前に `.index/summary.json`、`.index/records.json`、`.index/bm25.pkl`、`.index/keyword_index.json`、`.index/faiss.bin` を検証します
- artifact 欠落や index contract mismatch がある場合は fail-fast で起動失敗します
- runtime では `ai-config-vendor-skills sync-manifest` と `ai-config-index` を実行しません

`ai-config-provider` を別 Cloud Run service として置く場合は、provider 側に `AI_CONFIG_SELECTOR_BASE_URL=https://...run.app` を渡し、この route から選択済み `tool_id` の detail を引かせます。

## Production dispatch verification

`deploy/cloudrun/Dockerfile` は selector-serving 用の image で、`ai-config` 本体と build 済み `.index` は入れますが、`ai-config-dispatch` は install しません。
そのため、この image だけでは production の `dispatch_resolution` 証跡は取りません。

approved plan execution の production-safe path を GCP / Cloud Run で確認したい場合は、`ai-config-dispatch` も install した validation image か build step を別途用意して、次を実行します。

```bash
AI_CONFIG_DISPATCH_RUNTIME_MODE=production \
ai-config-doctor --repo-root /app --json
```

確認条件:

- `dispatch_resolution.details.source` が `installed_binary` か `installed_module`
- `AI_CONFIG_DISPATCH_ALLOW_IN_REPO_FALLBACK` は設定しない
- sibling checkout 解決に依存しない

`AI_CONFIG_DISPATCH_CMD` は explicit override としては使えますが、production proof の主系は installed runtime に置きます。

## Smoke checks

```bash
curl -fsS https://SERVICE_URL/healthz
curl -fsS https://SERVICE_URL/readyz
```

MCP client 側は `https://SERVICE_URL/mcp` を streamable HTTP endpoint として指定してください。

## Open WebUI + MCPO topology

このディレクトリには、Open WebUI から `ai-config` を MCPO 経由で使うための Cloud Run テンプレートも置いています。

GUI 中心で進める詳しい手順は `gcp-gui-setup-guide.ja.md` を参照してください。

- `ai-config-selector.service.yaml`
  `ai-config-selector-serving` をそのまま `/mcp` で公開する Cloud Run Service
- `ai-config-mcpo.service.yaml`
  `ghcr.io/open-webui/mcpo:v0.0.20` で `ai-config-selector` の `/mcp` を OpenAPI 化する Cloud Run Service
- `open-webui.service.mcpo.yaml`
  2026-03-31 時点の `open-webui` export をベースに、`ENABLE_PERSISTENT_CONFIG=False`、`ENABLE_LOGIN_FORM=False`、`ENABLE_DIRECT_CONNECTIONS=True`、`TOOL_SERVER_CONNECTIONS` secret を追加した再適用用テンプレート
- `open-webui.tool-server-connections.example.json`
  `OPENWEBUI_TOOL_SERVER_CONNECTIONS` secret に入れる JSON のサンプル

この構成では Cloud Run の公開面は次の 2 つです。

- `https://ai-config-selector-424287527578.asia-northeast1.run.app/mcp`
- `https://ai-config-mcpo-424287527578.asia-northeast1.run.app`

Open WebUI は MCPO だけを OpenAPI tool server として参照します。

## Secrets

前提:

```bash
export PROJECT_ID=sbi-art-auction
export PROJECT_NUMBER=424287527578
export REGION=asia-northeast1
export MCPO_API_KEY="$(openssl rand -hex 32)"
```

`MCPO_API_KEY` を作成します。

```bash
printf '%s' "$MCPO_API_KEY" > /tmp/MCPO_API_KEY.txt

gcloud secrets create MCPO_API_KEY \
  --project "$PROJECT_ID" \
  --replication-policy="automatic" \
  --data-file=/tmp/MCPO_API_KEY.txt || true

gcloud secrets versions add MCPO_API_KEY \
  --project "$PROJECT_ID" \
  --data-file=/tmp/MCPO_API_KEY.txt
```

`OPENWEBUI_TOOL_SERVER_CONNECTIONS` は `open-webui.tool-server-connections.example.json` をベースに、`key` を実際の MCPO key に置き換えて作成します。

```bash
python3 - <<'PY'
import json
from pathlib import Path
payload = json.loads(Path("deploy/cloudrun/open-webui.tool-server-connections.example.json").read_text(encoding="utf-8"))
payload[0]["key"] = __import__("os").environ["MCPO_API_KEY"]
Path("/tmp/open-webui.tool-server-connections.json").write_text(
    json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
    encoding="utf-8",
)
PY

gcloud secrets create OPENWEBUI_TOOL_SERVER_CONNECTIONS \
  --project "$PROJECT_ID" \
  --replication-policy="automatic" \
  --data-file=/tmp/open-webui.tool-server-connections.json || true

gcloud secrets versions add OPENWEBUI_TOOL_SERVER_CONNECTIONS \
  --project "$PROJECT_ID" \
  --data-file=/tmp/open-webui.tool-server-connections.json
```

## Build and Deploy

`ai-config-selector-serving` image を build して Artifact Registry へ push します。

```bash
gcloud builds submit \
  --project "$PROJECT_ID" \
  --tag "${REGION}-docker.pkg.dev/${PROJECT_ID}/ghcr/ai-config/ai-config-selector-serving:main" \
  -f deploy/cloudrun/Dockerfile \
  .
```

その後、Cloud Run Service を順番に apply します。

```bash
gcloud run services replace deploy/cloudrun/ai-config-selector.service.yaml \
  --project "$PROJECT_ID" \
  --region "$REGION"

gcloud run services replace deploy/cloudrun/ai-config-mcpo.service.yaml \
  --project "$PROJECT_ID" \
  --region "$REGION"

gcloud run services replace deploy/cloudrun/open-webui.service.mcpo.yaml \
  --project "$PROJECT_ID" \
  --region "$REGION"
```

## Verification

`ai-config-selector` の health / readiness:

```bash
curl -fsS "https://ai-config-selector-424287527578.asia-northeast1.run.app/healthz"
curl -fsS "https://ai-config-selector-424287527578.asia-northeast1.run.app/readyz"
```

MCPO の OpenAPI schema:

```bash
curl -fsS \
  -H "Authorization: Bearer ${MCPO_API_KEY}" \
  "https://ai-config-mcpo-424287527578.asia-northeast1.run.app/openapi.json"
```

dispatch runtime の production proof を取る場合:

```bash
AI_CONFIG_DISPATCH_RUNTIME_MODE=production \
ai-config-doctor --repo-root /app --json
```

この確認では `AI_CONFIG_DISPATCH_ALLOW_IN_REPO_FALLBACK` を使いません。`dispatch_resolution` が `installed_binary` か `installed_module` であることだけを許容します。

Open WebUI 側の注意点:

- `ENABLE_PERSISTENT_CONFIG=False` を入れているため、Admin UI で行った persistent config の変更は再起動で保持されません
- `ENABLE_LOGIN_FORM=False` を追加して、`ENABLE_OAUTH_SIGNUP=True` と両立するようにしています
- `TOOL_SERVER_CONNECTIONS` は Cloud Run env では部分補間できないため、`OPENWEBUI_TOOL_SERVER_CONNECTIONS` secret に完成済み JSON を保存する前提です
