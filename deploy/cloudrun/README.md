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
- startup 前に `.index/summary.json`、`.index/records.json`、`.index/bm25.pkl`、`.index/keyword_index.json`、`.index/faiss.bin` を検証します
- artifact 欠落や index contract mismatch がある場合は fail-fast で起動失敗します
- runtime では `ai-config-vendor-skills sync-manifest` と `ai-config-index` を実行しません

## Smoke checks

```bash
curl -fsS https://SERVICE_URL/healthz
curl -fsS https://SERVICE_URL/readyz
```

MCP client 側は `https://SERVICE_URL/mcp` を streamable HTTP endpoint として指定してください。
