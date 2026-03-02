#!/usr/bin/env bash
# ai-config-sync setup script
# Creates venv, installs dependencies, and builds the tool index.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO_ROOT"

echo "=== ai-config-sync setup ==="
echo "Repo root: $REPO_ROOT"

# 1. Create venv
if [ ! -d ".venv" ]; then
  echo "Creating virtual environment..."
  python3 -m venv .venv
fi

# 2. Activate
source .venv/bin/activate

# 3. Install
echo "Installing ai-config..."
pip install -e ".[dev]" --quiet

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
