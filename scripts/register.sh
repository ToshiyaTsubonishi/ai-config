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

merge_json_mcp_server() {
  local config_path="$1"
  local parent_dir
  parent_dir="$(dirname "$config_path")"
  mkdir -p "$parent_dir"

  CONFIG_PATH="$config_path" MCP_SERVER="$MCP_SERVER" REPO_ROOT="$REPO_ROOT" python3 - <<'PY'
import json
import os
from pathlib import Path

config_path = Path(os.environ["CONFIG_PATH"])
payload = {
    "command": os.environ["MCP_SERVER"],
    "args": ["--repo-root", os.environ["REPO_ROOT"]],
    "env": {},
}

data = {}
if config_path.exists():
    try:
        data = json.loads(config_path.read_text(encoding="utf-8"))
    except Exception:
        data = {}

if not isinstance(data, dict):
    data = {}

data.setdefault("mcpServers", {})
data["mcpServers"]["ai-config-selector"] = payload
config_path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
PY
}

merge_codex_mcp_server() {
  mkdir -p "$(dirname "$CODEX_CONFIG")"
  CONFIG_PATH="$CODEX_CONFIG" MCP_SERVER="$MCP_SERVER" REPO_ROOT="$REPO_ROOT" python3 - <<'PY'
from pathlib import Path
import os
import re

config_path = Path(os.environ["CONFIG_PATH"])
block = (
    "[mcp_servers.ai-config-selector]\n"
    f'command = "{os.environ["MCP_SERVER"]}"\n'
    f'args = ["--repo-root", "{os.environ["REPO_ROOT"]}"]\n'
)

text = config_path.read_text(encoding="utf-8") if config_path.exists() else ""
pattern = re.compile(
    r"(?ms)^" + re.escape("[mcp_servers.ai-config-selector]") + r"\n(?:.*?\n)*(?=^\[|\Z)"
)
if pattern.search(text):
    updated = pattern.sub(block, text)
else:
    updated = text.rstrip()
    if updated:
        updated += "\n\n"
    updated += block
config_path.write_text(updated.rstrip() + "\n", encoding="utf-8")
PY
}

# ---------------------------------------------------------------------------
# Antigravity
# ---------------------------------------------------------------------------
ANTIGRAVITY_DIR="${HOME}/.gemini/antigravity"
ANTIGRAVITY_MCP="$ANTIGRAVITY_DIR/mcp_config.json"

register_antigravity() {
  merge_json_mcp_server "$ANTIGRAVITY_MCP"
  echo "[ok] Antigravity: $ANTIGRAVITY_MCP"
}

# ---------------------------------------------------------------------------
# Gemini CLI
# ---------------------------------------------------------------------------
GEMINI_SETTINGS="${HOME}/.gemini/settings.json"

register_gemini_cli() {
  merge_json_mcp_server "$GEMINI_SETTINGS"
  echo "[ok] Gemini CLI: $GEMINI_SETTINGS"
}

# ---------------------------------------------------------------------------
# Claude Code
# ---------------------------------------------------------------------------
CLAUDE_CONFIG="${HOME}/.claude.json"

register_claude() {
  merge_json_mcp_server "$CLAUDE_CONFIG"
  echo "[ok] Claude Code: $CLAUDE_CONFIG"
}

# ---------------------------------------------------------------------------
# Codex
# ---------------------------------------------------------------------------
CODEX_CONFIG="${HOME}/.codex/config.toml"

register_codex() {
  merge_codex_mcp_server
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
  claude) register_claude ;;
  codex) register_codex ;;
  all)
    register_claude
    register_antigravity
    register_gemini_cli
    register_codex
    ;;
  *)
    echo "Usage: $0 [claude|antigravity|gemini_cli|codex|all]"
    exit 1
    ;;
esac

echo ""
echo "Done. Restart your AI tools to pick up the changes."
