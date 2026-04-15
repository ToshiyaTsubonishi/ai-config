#!/usr/bin/env bash

set -euo pipefail

if [[ $# -lt 2 || $# -gt 3 ]]; then
  echo "Usage: $0 <rendered-dir> <project-id> [region]" >&2
  exit 1
fi

rendered_dir="$1"
project_id="$2"
region="${3:-asia-northeast1}"

for file in \
  ai-config-selector.service.yaml \
  ai-config-provider.service.yaml \
  ai-config-mcpo.service.yaml \
  ai-config-provider-mcpo.service.yaml \
  open-webui.service.mcpo.yaml
do
  path="${rendered_dir}/${file}"
  if [[ ! -f "${path}" ]]; then
    echo "Missing rendered file: ${path}" >&2
    exit 1
  fi

  echo "Applying ${file} to ${project_id}/${region}"
  gcloud run services replace "${path}" \
    --project "${project_id}" \
    --region "${region}"
done
