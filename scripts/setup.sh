#!/usr/bin/env bash
# ai-config-sync setup script
# Creates venv, installs dependencies, and builds the tool index.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO_ROOT"

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

# 4. Build index
echo "Building tool index..."
ai-config-index --repo-root "$REPO_ROOT"

echo ""
echo "=== Setup complete ==="
echo "To start the MCP server:"
echo "  $REPO_ROOT/.venv/bin/ai-config-mcp-server --repo-root $REPO_ROOT"
echo ""
echo "To register with your AI tools, run:"
echo "  bash scripts/register.sh"
