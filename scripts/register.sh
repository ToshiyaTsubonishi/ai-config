#!/usr/bin/env bash
# Register ai-config-selector MCP with AI coding tools.
# Writes the minimal MCP config so each tool can use dynamic tool selection.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
MCP_SERVER="$REPO_ROOT/.venv/bin/ai-config-mcp-server"

if [ ! -f "$MCP_SERVER" ]; then
  echo "ERROR: ai-config-mcp-server not found. Run scripts/setup.sh first."
  exit 1
fi

# ---------------------------------------------------------------------------
# Antigravity
# ---------------------------------------------------------------------------
ANTIGRAVITY_DIR="${HOME}/.gemini/antigravity"
ANTIGRAVITY_MCP="$ANTIGRAVITY_DIR/mcp_config.json"

register_antigravity() {
  mkdir -p "$ANTIGRAVITY_DIR"
  cat > "$ANTIGRAVITY_MCP" << EOF
{
  "mcpServers": {
    "ai-config-selector": {
      "command": "$MCP_SERVER",
      "args": ["--repo-root", "$REPO_ROOT"],
      "env": {}
    }
  }
}
EOF
  echo "[ok] Antigravity: $ANTIGRAVITY_MCP"
}

# ---------------------------------------------------------------------------
# Gemini CLI
# ---------------------------------------------------------------------------
GEMINI_SETTINGS="${HOME}/.gemini/settings.json"

register_gemini_cli() {
  local tmp
  if [ -f "$GEMINI_SETTINGS" ]; then
    # Merge into existing settings.json
    tmp=$(mktemp)
    python3 -c "
import json, sys
with open('$GEMINI_SETTINGS') as f:
    settings = json.load(f)
settings.setdefault('mcpServers', {})
settings['mcpServers']['ai-config-selector'] = {
    'command': '$MCP_SERVER',
    'args': ['--repo-root', '$REPO_ROOT'],
    'env': {}
}
with open('$tmp', 'w') as f:
    json.dump(settings, f, indent=2, ensure_ascii=False)
" && mv "$tmp" "$GEMINI_SETTINGS"
  else
    mkdir -p "$(dirname "$GEMINI_SETTINGS")"
    cat > "$GEMINI_SETTINGS" << EOF
{
  "mcpServers": {
    "ai-config-selector": {
      "command": "$MCP_SERVER",
      "args": ["--repo-root", "$REPO_ROOT"],
      "env": {}
    }
  }
}
EOF
  fi
  echo "[ok] Gemini CLI: $GEMINI_SETTINGS"
}

# ---------------------------------------------------------------------------
# Codex
# ---------------------------------------------------------------------------
CODEX_CONFIG="${HOME}/.codex/config.toml"

register_codex() {
  mkdir -p "$(dirname "$CODEX_CONFIG")"
  # Codex uses TOML format
  cat > "$CODEX_CONFIG" << EOF
[mcp_servers.ai-config-selector]
command = "$MCP_SERVER"
args = ["--repo-root", "$REPO_ROOT"]
EOF
  echo "[ok] Codex: $CODEX_CONFIG"
}

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
echo "=== Registering ai-config-selector MCP ==="
echo "Server: $MCP_SERVER"
echo "Repo:   $REPO_ROOT"
echo ""

TARGET="${1:-all}"

case "$TARGET" in
  antigravity) register_antigravity ;;
  gemini|gemini_cli) register_gemini_cli ;;
  codex) register_codex ;;
  all)
    register_antigravity
    register_gemini_cli
    register_codex
    ;;
  *)
    echo "Usage: $0 [antigravity|gemini_cli|codex|all]"
    exit 1
    ;;
esac

echo ""
echo "Done. Restart your AI tools to pick up the changes."
