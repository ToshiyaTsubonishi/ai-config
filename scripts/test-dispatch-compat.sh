#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
DISPATCH_ROOT="${AI_CONFIG_DISPATCH_REPO_ROOT:-$REPO_ROOT/../ai-config-dispatch}"
PYTHON_BIN="${AI_CONFIG_PYTHON_BIN:-$REPO_ROOT/.venv/bin/python}"

if [ ! -d "$DISPATCH_ROOT/src/ai_config_dispatch" ]; then
  echo "ERROR: ai-config-dispatch checkout not found at $DISPATCH_ROOT" >&2
  exit 1
fi

if ! command -v "$PYTHON_BIN" >/dev/null 2>&1; then
  echo "ERROR: Python interpreter not found: $PYTHON_BIN" >&2
  exit 1
fi

export PYTHONPATH="$DISPATCH_ROOT/src:$REPO_ROOT/src${PYTHONPATH:+:$PYTHONPATH}"

"$PYTHON_BIN" -m ai_config_dispatch.cli --list-workflows >/dev/null
"$PYTHON_BIN" -m pytest \
  tests/test_plan_boundary.py \
  tests/test_dispatch_import_guard.py \
  tests/test_cli_smoke.py \
  tests/test_doctor.py -q
