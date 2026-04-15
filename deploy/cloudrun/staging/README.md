# Separate-Project Staging Stack

This directory contains reproducible assets for a separate-project Cloud Run
staging stack that mirrors the selector/provider/Open WebUI topology without
reusing production resources.

Phase 1 targets project `abiding-aspect-457603-m8` in `asia-northeast1` and
keeps the same five Cloud Run service names:

1. `ai-config-selector`
2. `ai-config-provider`
3. `ai-config-mcpo`
4. `ai-config-provider-mcpo`
5. `open-webui`

`ai-harness` is intentionally out of Cloud Run execution for this phase. Its
remote wrapper is documented separately in the sibling repo:
`ai-harness/docs/remote-wrapper-contract.md`.

## Files

- `stack.example.yaml`
  Value file with staging defaults for `abiding-aspect-457603-m8`
- `render_stack.py`
  Renders Cloud Run YAMLs, tool-server connection JSON, and computed metadata
- `apply_rendered_stack.sh`
  Sequential `gcloud run services replace` helper for rendered output
- `gcp-gui-setup-guide.ja.md`
  Console-oriented setup flow for the separate-project stack
- `templates/`
  Template sources for the five services and the Open WebUI tool-server secret

## Inputs You Must Fill In

Before rendering, copy `stack.example.yaml` and replace at least these fields:

- `project_number`
- `images.selector`
- `images.provider`
- any secret names that differ from the defaults in your staging project

`images.selector` / `images.provider` には tag ではなく `ghcr.io/...@sha256:...` のような
pinned digest を入れるのを推奨します。
constrained production / staging 向けに GHCR へ publish する場合は
`../release/publish_ghcr_release.py` が出力する `ghcr-release-manifest.json` の
`cloudrun.images.selector` / `cloudrun.images.provider` をそのまま貼ってください。

The project number is not derivable from the repository. Look it up in the GCP
Console or with:

```bash
gcloud projects describe abiding-aspect-457603-m8 --format='value(projectNumber)'
```

## Render

```bash
cd /Users/tsytbns/Documents/GitHub/ai-config

python deploy/cloudrun/staging/render_stack.py \
  --config deploy/cloudrun/staging/stack.example.yaml \
  --output-dir deploy/cloudrun/staging/rendered
```

If you already have the actual MCPO API key and want a ready-to-upload secret
payload:

```bash
python deploy/cloudrun/staging/render_stack.py \
  --config deploy/cloudrun/staging/stack.example.yaml \
  --output-dir deploy/cloudrun/staging/rendered \
  --mcpo-api-key "$MCPO_API_KEY"
```

The renderer writes:

- `ai-config-selector.service.yaml`
- `ai-config-provider.service.yaml`
- `ai-config-mcpo.service.yaml`
- `ai-config-provider-mcpo.service.yaml`
- `open-webui.service.mcpo.yaml`
- `open-webui.tool-server-connections.json`
- `stack-metadata.json`

`stack-metadata.json` contains the computed run.app URLs derived from the
project number and service names, plus provenance fields for commit SHA and
provider-bundle version.

release manifest を使う場合は、同じく `cloudrun.provenance` をこの value file の
`provenance` block に移すと、rendered revision annotation と `/readyz` の情報が
publish 時点と揃います。

## Deploy

Once the images and secrets exist in the staging project:

```bash
./deploy/cloudrun/staging/apply_rendered_stack.sh \
  deploy/cloudrun/staging/rendered \
  abiding-aspect-457603-m8 \
  asia-northeast1
```

The deployment order is fixed so that downstream services reference already
known selector/provider URLs.

## Secrets and Resources

The staging stack assumes separate-project resources and does not reuse
production buckets, database, or secrets.

Defaults in `stack.example.yaml`:

- Cloud SQL instance: `open-web-ui`
- Open WebUI bucket: `open-webui-abiding-aspect-457603-m8`
- SearXNG bucket: `searxng-abiding-aspect-457603-m8`
- service account:
  `open-webui-runner@abiding-aspect-457603-m8.iam.gserviceaccount.com`

Secret names intentionally match the current logical names but remain isolated
because they live in a different GCP project.

Important secret names in this stack:

- `MCPO_API_KEY`
- `OPENWEBUI_TOOL_SERVER_CONNECTIONS`
- `WEBUI_SECRET_KEY`
- `DATABASE_URL`

## Provenance

The staging renderer carries provenance into both rendered output and runtime:

- selector commit SHA
- provider commit SHA
- provider-bundle version
- image ref for selector/provider

Rendered service YAMLs write these values into revision annotations and
container env vars. After deploy, selector/provider `/readyz` can expose the
same provenance so runtime drift is easier to spot.

## Verification

After deployment, use `stack-metadata.json` or the computed URLs below:

- selector: `https://ai-config-selector-<PROJECT_NUMBER>.asia-northeast1.run.app`
- provider: `https://ai-config-provider-<PROJECT_NUMBER>.asia-northeast1.run.app`
- selector MCPO: `https://ai-config-mcpo-<PROJECT_NUMBER>.asia-northeast1.run.app`
- provider MCPO:
  `https://ai-config-provider-mcpo-<PROJECT_NUMBER>.asia-northeast1.run.app`
- Open WebUI: `https://open-webui-<PROJECT_NUMBER>.asia-northeast1.run.app`

Verify:

```bash
curl -fsS "https://ai-config-selector-<PROJECT_NUMBER>.asia-northeast1.run.app/healthz"
curl -fsS "https://ai-config-selector-<PROJECT_NUMBER>.asia-northeast1.run.app/readyz"
curl -fsS "https://ai-config-provider-<PROJECT_NUMBER>.asia-northeast1.run.app/healthz"
curl -fsS "https://ai-config-provider-<PROJECT_NUMBER>.asia-northeast1.run.app/readyz"
curl -fsS -H "Authorization: Bearer $MCPO_API_KEY" \
  "https://ai-config-mcpo-<PROJECT_NUMBER>.asia-northeast1.run.app/openapi.json"
curl -fsS -H "Authorization: Bearer $MCPO_API_KEY" \
  "https://ai-config-provider-mcpo-<PROJECT_NUMBER>.asia-northeast1.run.app/openapi.json"
```
