#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
RENDERED_DIR="${1:-${SCRIPT_DIR}/rendered}"
PROJECT_ID="${2:-sbi-art-auction}"
REGION="${3:-asia-northeast1}"

exec "${SCRIPT_DIR}/../staging/apply_rendered_stack.sh" \
  "${RENDERED_DIR}" \
  "${PROJECT_ID}" \
  "${REGION}"
