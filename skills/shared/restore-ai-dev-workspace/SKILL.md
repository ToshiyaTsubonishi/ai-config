---
name: restore-ai-dev-workspace
description: Recreate this full AI dev workspace on a new machine (ai-config, ai-agent-collection, ModernGallery), including interactive env setup, MCP/skills sync, build/run smoke checks, and Open WebUI export import.
---

# Restore AI Dev Workspace

Use this workflow when the user wants to rebuild the current local AI development setup from scratch.

## 1) Ask for required inputs

Collect these once:

- Target root path (default: `$HOME`)
- Whether to run core stack or full stack (`core` is default and avoids GPU-only services)
- Whether Open WebUI exports should be applied now
- If exports should be applied: export folder path and optional Open WebUI admin API key
- Whether Antigravity settings/extensions should be restored now

## 2) Run one command

```powershell
cd $HOME/ai-config
pwsh ./scripts/restore-ai-workspace.ps1 \
  -WorkspaceRoot $HOME \
  -AiPlatformProfile core \
  -ApplyOpenWebUiExport \
  -ApplyAntigravityImport
```

Notes:

- The script calls interactive `.env` setup and asks for required variables.
- It clones/pulls `ai-config`, `ai-agent-collection`, and `ModernGallery`.
- It runs `sync-all.ps1`, builds/runs containers, and executes HTTP smoke checks.
- If needed, skip parts of Open WebUI import with:
  - `-SkipOpenWebUiConfig`
  - `-SkipOpenWebUiModels`
  - `-SkipOpenWebUiToolServers`
- If needed, skip parts of Antigravity import with:
  - `-SkipAntigravitySettings`
  - `-SkipAntigravitySnippets`
  - `-SkipAntigravityExtensions`
  - `-SkipAntigravityGlobalStorage`

## 3) Keep Open WebUI state in sync after new exports

Whenever a new Open WebUI export is downloaded:

```powershell
cd $HOME/ai-config
pwsh ./scripts/sync-open-webui-export.ps1 \
  -ExportDir "<path-to-export-folder>" \
  -UseLatestFiles
```

This imports latest `config-*.json`, `models-export-*.json`, and `tool-server-*.json` into Open WebUI via API.

## 4) Fast MCP/Skills refresh only

If only `ai-config` changed and repos are already present:

```powershell
cd $HOME/ai-config
pwsh ./scripts/sync-all.ps1
```

## 5) Keep Antigravity state in sync

When local Antigravity settings/extensions change:

```powershell
cd $HOME/ai-config
pwsh ./scripts/export-antigravity.ps1
```

This updates:
- `inventory/antigravity/latest` (used for restore)
- `inventory/antigravity/snapshot-*` (history)

## 6) Dry-run mode for safe validation

All new scripts support `-DryRun`.

```powershell
pwsh ./scripts/restore-ai-workspace.ps1 -DryRun
```
