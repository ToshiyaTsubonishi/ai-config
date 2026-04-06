# Cloud Run selector-serving

Cloud Run runtime は `skills/`、`config/`、`.index/` を read-only に使うだけです。`sync-manifest` と `ai-config-index` は runtime では実行せず、image build 時に完了させます。

## Build

```bash
docker build -f deploy/cloudrun/Dockerfile -t ai-config-selector-serving:local .
```

builder image には `cargo` / `rustc` / `build-essential` を入れているため、Apple Silicon などで `SudachiPy` が source build に落ちても Docker build で完走できます。

Cloud Build を使う場合は、`gcloud builds submit --tag ... -f ...` ではなく `deploy/cloudrun/cloudbuild.selector.yaml` を使います。

```bash
export PROJECT_ID=YOUR_PROJECT_ID
export REGION=asia-northeast1
export IMAGE="${REGION}-docker.pkg.dev/${PROJECT_ID}/cloud-run-source-deploy/ai-config-selector-serving:$(date +%Y%m%d-%H%M%S)"

gcloud builds submit \
  --project "$PROJECT_ID" \
  --config deploy/cloudrun/cloudbuild.selector.yaml \
  --substitutions "_IMAGE=${IMAGE}" \
  .
```

## Deploy

```bash
export PROJECT_NUMBER=YOUR_PROJECT_NUMBER
export SERVICE_NAME=ai-config-selector
export SERVICE_ACCOUNT="optional-service-account@${PROJECT_ID}.iam.gserviceaccount.com"

python3 deploy/cloudrun/render_selector_service.py \
  --project-id "$PROJECT_ID" \
  --project-number "$PROJECT_NUMBER" \
  --region "$REGION" \
  --image "$IMAGE" \
  --service-name "$SERVICE_NAME" \
  --service-account "$SERVICE_ACCOUNT" \
  --output /tmp/ai-config-selector.service.yaml

gcloud run services replace /tmp/ai-config-selector.service.yaml \
  --project "$PROJECT_ID" \
  --region "$REGION"
```

認証、ingress、perimeter 制御はこの repo の scope 外です。production では Cloud Run 側の policy を別途設定してください。

## Runtime contract

- entrypoint は `ai-config-selector-serving`
- MCP endpoint は `/mcp`
- liveness は `/livez`（`/healthz` も互換のため残すが、Cloud Run の外形確認は `/livez` を使う）
- readiness は `/readyz`
- startup 前に `.index/summary.json`、`.index/records.json`、`.index/bm25.pkl`、`.index/keyword_index.json`、`.index/faiss.bin` を検証します
- artifact 欠落や index contract mismatch がある場合は fail-fast で起動失敗します
- runtime では `ai-config-vendor-skills sync-manifest` と `ai-config-index` を実行しません

## Smoke checks

```bash
curl -fsS https://SERVICE_URL/livez
curl -fsS https://SERVICE_URL/readyz
```

MCP client 側は `https://SERVICE_URL/mcp` を streamable HTTP endpoint として指定してください。

## Open WebUI + MCPO topology

このディレクトリには、Open WebUI から `ai-config` を MCPO 経由で使うための Cloud Run テンプレートも置いています。

GUI 中心で進める詳しい手順は `gcp-gui-setup-guide.ja.md` を参照してください。

- `ai-config-selector.service.yaml`
  `ai-config-selector-serving` をそのまま `/mcp` で公開する Cloud Run Service
- `render_selector_service.py`
  `ai-config-selector.service.yaml` をベースに、project / region / image / service account を差し替えた manifest を生成する helper
- `cloudbuild.selector.yaml`
  `deploy/cloudrun/Dockerfile` を Cloud Build から build するための config。`gcloud builds submit --tag ... -f ...` の代わりに使う
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
  --config deploy/cloudrun/cloudbuild.selector.yaml \
  --substitutions "_IMAGE=${REGION}-docker.pkg.dev/${PROJECT_ID}/ghcr/ai-config/ai-config-selector-serving:main" \
  .
```

その後、`ai-config-selector` は render helper で project 固有の YAML を作ってから apply します。

```bash
python3 deploy/cloudrun/render_selector_service.py \
  --project-id "$PROJECT_ID" \
  --project-number "$PROJECT_NUMBER" \
  --region "$REGION" \
  --image "${REGION}-docker.pkg.dev/${PROJECT_ID}/ghcr/ai-config/ai-config-selector-serving:main" \
  --service-name ai-config-selector \
  --service-account "open-webui-runner@${PROJECT_ID}.iam.gserviceaccount.com" \
  --output /tmp/ai-config-selector.service.yaml

gcloud run services replace /tmp/ai-config-selector.service.yaml \
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
curl -fsS "https://ai-config-selector-424287527578.asia-northeast1.run.app/livez"
curl -fsS "https://ai-config-selector-424287527578.asia-northeast1.run.app/readyz"
```

MCPO の OpenAPI schema:

```bash
curl -fsS \
  -H "Authorization: Bearer ${MCPO_API_KEY}" \
  "https://ai-config-mcpo-424287527578.asia-northeast1.run.app/openapi.json"
```

Open WebUI 側の注意点:

- `ENABLE_PERSISTENT_CONFIG=False` を入れているため、Admin UI で行った persistent config の変更は再起動で保持されません
- `ENABLE_LOGIN_FORM=False` を追加して、`ENABLE_OAUTH_SIGNUP=True` と両立するようにしています
- `TOOL_SERVER_CONNECTIONS` は Cloud Run env では部分補間できないため、`OPENWEBUI_TOOL_SERVER_CONNECTIONS` secret に完成済み JSON を保存する前提です
