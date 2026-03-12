#!/usr/bin/env bash
# ai-config-sync setup script
# Creates venv, installs dependencies, and builds the tool index.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO_ROOT"

SKIP_VENDOR_SYNC=0
while [ "$#" -gt 0 ]; do
  case "$1" in
    --skip-vendor-sync)
      SKIP_VENDOR_SYNC=1
      shift
      ;;
    *)
      echo "ERROR: Unknown argument: $1"
      echo "Usage: bash scripts/setup.sh [--skip-vendor-sync]"
      exit 1
      ;;
  esac
done

echo "=== ai-config-sync setup ==="
echo "Repo root: $REPO_ROOT"

# Resolve a Python interpreter that satisfies requires-python (>=3.11).
pick_python() {
  for candidate in python3.13 python3.12 python3.11 python3; do
    if ! command -v "$candidate" >/dev/null 2>&1; then
      continue
    fi
    if "$candidate" -c 'import sys; raise SystemExit(0 if sys.version_info >= (3, 11) else 1)' >/dev/null 2>&1; then
      echo "$candidate"
      return 0
    fi
  done
  return 1
}

if ! PYTHON_BIN="$(pick_python)"; then
  echo "ERROR: Python 3.11+ was not found. Install Python 3.11 or newer and retry."
  exit 1
fi

NEEDS_VENV_RECREATE=0
if [ ! -x ".venv/bin/python" ]; then
  NEEDS_VENV_RECREATE=1
elif ! .venv/bin/python -c 'import sys; raise SystemExit(0 if sys.version_info >= (3, 11) else 1)' >/dev/null 2>&1; then
  NEEDS_VENV_RECREATE=1
fi

# 1. Create or refresh venv
if [ "$NEEDS_VENV_RECREATE" -eq 1 ]; then
  echo "Creating virtual environment with $PYTHON_BIN..."
  "$PYTHON_BIN" -m venv --clear .venv
fi

# 2. Activate
source .venv/bin/activate

# 3. Install
echo "Installing ai-config..."
# This project uses hatchling (PEP 517); editable installs are not supported here.
python -m pip install --upgrade pip --quiet
python -m pip install ".[dev]" --quiet

# 4. Materialize vendor-managed external skills
if [ "$SKIP_VENDOR_SYNC" -eq 1 ]; then
  echo "WARNING: Skipping vendor manifest sync. External skill coverage may be incomplete."
else
  echo "Syncing vendor-managed external skills..."
  if ! .venv/bin/ai-config-vendor-skills --repo-root "$REPO_ROOT" sync-manifest; then
    echo "ERROR: Vendor manifest sync failed."
    echo "The pinned ref materialization step did not complete."
    echo "Retry with network access or rerun with --skip-vendor-sync if you intentionally want partial external coverage."
    exit 1
  fi
fi

# 5. Build index
echo "Building tool index..."
ai-config-index --repo-root "$REPO_ROOT" --profile default

echo ""
echo "=== Setup complete ==="
echo "To start the MCP server:"
echo "  $REPO_ROOT/.venv/bin/ai-config-mcp-server --repo-root $REPO_ROOT"
echo ""
echo "To register with your AI tools, run:"
echo "  bash scripts/register.sh"
