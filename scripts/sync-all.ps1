[CmdletBinding()]
param(
  [string]$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path,
  [string[]]$McpTargets = @("codex", "gemini", "antigravity"),
  [string[]]$SkillTargets = @("codex", "gemini", "antigravity"),
  [switch]$SkipWindowsEnvSync,
  [switch]$SkipEnvSync,
  [switch]$NoBackup,
  [switch]$StrictVariables,
  [switch]$OverwriteExistingSkills,
  [switch]$PruneManagedSkills
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$applyScript = Join-Path $RepoRoot "scripts/apply-mcp.ps1"
$syncSkillsScript = Join-Path $RepoRoot "scripts/sync-skills.ps1"
$inventoryScript = Join-Path $RepoRoot "scripts/export-inventory.ps1"
$syncEnvScript = Join-Path $RepoRoot "scripts/sync-env-files.ps1"
$workspaceRoot = Split-Path -Path $RepoRoot -Parent
$windowsEnvSyncScript = Join-Path $workspaceRoot "windows-env-sync/scripts/sync-windows-env.ps1"

$applyArgs = @{
  RepoRoot = $RepoRoot
  Targets = $McpTargets
}
if ($NoBackup) {
  $applyArgs["NoBackup"] = $true
}
if ($StrictVariables) {
  $applyArgs["StrictVariables"] = $true
}

$syncArgs = @{
  RepoRoot = $RepoRoot
  Targets = $SkillTargets
}
if ($OverwriteExistingSkills) {
  $syncArgs["OverwriteExisting"] = $true
}
if ($PruneManagedSkills) {
  $syncArgs["PruneManaged"] = $true
}

if (-not $SkipEnvSync) {
  & $syncEnvScript -RepoRoot $RepoRoot
}

if (-not $SkipWindowsEnvSync -and $IsWindows) {
  if (Test-Path $windowsEnvSyncScript) {
    & $windowsEnvSyncScript -NonInteractive
  } else {
    Write-Warning "windows-env-sync not found at $windowsEnvSyncScript. Run scripts/fetch-repos.ps1 first."
  }
}

& $applyScript @applyArgs
& $syncSkillsScript @syncArgs
& $inventoryScript -RepoRoot $RepoRoot

Write-Host "All sync operations completed."
