param(
    [ValidateSet("all", "codex", "gemini", "gemini_cli", "antigravity")]
    [string]$Target = "all"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$RepoRoot = Split-Path -Parent $PSScriptRoot
$VenvPython = Join-Path $RepoRoot ".venv\Scripts\python.exe"
$McpServer = Join-Path $RepoRoot ".venv\Scripts\ai-config-mcp-server.cmd"

if (-not (Test-Path $McpServer)) {
    $McpServer = Join-Path $RepoRoot ".venv\Scripts\ai-config-mcp-server.exe"
}

if (-not (Test-Path $VenvPython) -or -not (Test-Path $McpServer)) {
    throw "ai-config runtime not found. Run scripts/setup.ps1 first."
}

function Merge-JsonMcpServer {
    param([string]$ConfigPath)

    $script = @'
import json
import sys
from pathlib import Path

config_path = Path(sys.argv[1])
server_path = sys.argv[2]
repo_root = sys.argv[3]

payload = {
    "command": server_path,
    "args": ["--repo-root", repo_root],
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
config_path.parent.mkdir(parents=True, exist_ok=True)
config_path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
'@
    $script | & $VenvPython - $ConfigPath $McpServer $RepoRoot
    if ($LASTEXITCODE -ne 0) {
        throw "Failed to update JSON MCP config: $ConfigPath"
    }
}

function Merge-CodexMcpServer {
    param([string]$ConfigPath)

    $script = @'
import re
import sys
from pathlib import Path

def toml_literal(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"

config_path = Path(sys.argv[1])
server_path = sys.argv[2]
repo_root = sys.argv[3]

block = (
    "[mcp_servers.ai-config-selector]\n"
    f"command = {toml_literal(server_path)}\n"
    f"args = [{toml_literal('--repo-root')}, {toml_literal(repo_root)}]\n"
)

text = config_path.read_text(encoding="utf-8") if config_path.exists() else ""
pattern = re.compile(r"(?ms)^\[mcp_servers\.ai-config-selector\]\n(?:.*?\n)*(?=^\[|\Z)")
if pattern.search(text):
    updated = pattern.sub(lambda _: block, text)
else:
    updated = text.rstrip()
    if updated:
        updated += "\n\n"
    updated += block

config_path.parent.mkdir(parents=True, exist_ok=True)
config_path.write_text(updated.rstrip() + "\n", encoding="utf-8")
'@
    $script | & $VenvPython - $ConfigPath $McpServer $RepoRoot
    if ($LASTEXITCODE -ne 0) {
        throw "Failed to update Codex MCP config: $ConfigPath"
    }
}

function Register-Codex {
    $configPath = Join-Path $HOME ".codex\config.toml"
    Merge-CodexMcpServer -ConfigPath $configPath
    Write-Host "[ok] Codex: $configPath"
}

function Register-Gemini {
    $configPath = Join-Path $HOME ".gemini\settings.json"
    Merge-JsonMcpServer -ConfigPath $configPath
    Write-Host "[ok] Gemini CLI: $configPath"
}

function Register-Antigravity {
    $configPath = Join-Path $HOME ".gemini\antigravity\mcp_config.json"
    Merge-JsonMcpServer -ConfigPath $configPath
    Write-Host "[ok] Antigravity: $configPath"
}

Write-Host "=== Registering ai-config-selector MCP ==="
Write-Host "Server: $McpServer"
Write-Host "Repo:   $RepoRoot"
Write-Host ""

switch ($Target) {
    "codex" { Register-Codex }
    "gemini" { Register-Gemini }
    "gemini_cli" { Register-Gemini }
    "antigravity" { Register-Antigravity }
    "all" {
        Register-Codex
        Register-Gemini
        Register-Antigravity
    }
}

Write-Host ""
Write-Host "Done. Restart your AI tools to pick up the changes."
