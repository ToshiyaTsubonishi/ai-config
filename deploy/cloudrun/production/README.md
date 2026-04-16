# Production Cloud Run Stack

This directory contains production-oriented Cloud Run assets for the existing
project `sbi-art-auction` in `asia-northeast1`.

Phase 1 keeps the same five-service topology used in staging:

1. `ai-config-selector`
2. `ai-config-provider`
3. `ai-config-mcpo`
4. `ai-config-provider-mcpo`
5. `open-webui`

`ai-harness` remains out of the Cloud Run runtime for this phase. Its remote
wrapper contract stays documented in the sibling repo.

## Why This Exists

The repository root already contains fixed Cloud Run reference YAMLs for the
production project. This directory adds a reproducible render path that is
better aligned with the constrained-production release flow:

- selector/provider images come from prebuilt GHCR digests
- provenance can be copied from `ghcr-release-manifest.json`
- the current production project values are captured in one value file

## Inputs

Start from `stack.example.yaml` and replace at least:

- `images.selector`
- `images.provider`
- `tool_server_connections.mcpo_api_key_placeholder` if you want a ready-made
  secret payload
- the optional `provenance` block with values from
  `deploy/cloudrun/release/ghcr-release-manifest.json`

The recommended source of truth is the manifest produced by:

```bash
python deploy/cloudrun/release/publish_ghcr_release.py \
  --github-owner tsytbns \
  --provider-repo ../ai-config-provider \
  --push \
  --output .artifacts/ghcr-release-manifest.json
```

Copy these fields into the production stack file:

- `cloudrun.images.selector`
- `cloudrun.images.provider`
- `cloudrun.provenance.selector_commit_sha`
- `cloudrun.provenance.provider_commit_sha`
- `cloudrun.provenance.provider_bundle_version`
- `cloudrun.provenance.provider_bundle_source_commit_sha`

If the production environment cannot authenticate to GHCR, temporarily make the
GHCR packages public during deploy, then switch them back afterward.

## Render

```bash
cd /Users/tsytbns/Documents/GitHub/ai-config

.venv/bin/python deploy/cloudrun/production/render_stack.py
```

To inject an actual MCPO key into the rendered Open WebUI secret payload:

```bash
.venv/bin/python deploy/cloudrun/production/render_stack.py \
  --mcpo-api-key "$MCPO_API_KEY"
```

The wrapper defaults to:

- config: `deploy/cloudrun/production/stack.example.yaml`
- output: `deploy/cloudrun/production/rendered`

The rendered output contains:

- `ai-config-selector.service.yaml`
- `ai-config-provider.service.yaml`
- `ai-config-mcpo.service.yaml`
- `ai-config-provider-mcpo.service.yaml`
- `open-webui.service.mcpo.yaml`
- `open-webui.tool-server-connections.json`
- `stack-metadata.json`

## Apply

```bash
bash deploy/cloudrun/production/apply_rendered_stack.sh
```

Or explicitly:

```bash
bash deploy/cloudrun/production/apply_rendered_stack.sh \
  deploy/cloudrun/production/rendered \
  sbi-art-auction \
  asia-northeast1
```

## Current Production Defaults

The example values are derived from the current production project and exported
service configuration:

- project: `sbi-art-auction`
- project number: `424287527578`
- service account: `open-webui-runner@sbi-art-auction.iam.gserviceaccount.com`
- Cloud SQL instance: `open-web-ui`
- Open WebUI bucket: `open-webui-sbiaa`
- SearXNG bucket: `searxng-sbiaa`

The production stack intentionally keeps Open WebUI on env-driven tool-server
configuration with `ENABLE_PERSISTENT_CONFIG=False`, so the Cloud Run revision
remains the source of truth for selector/provider tool wiring.
