[CmdletBinding()]
param(
  [string]$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path,
  [string]$ConfigPath,
  [string[]]$Targets = @("codex", "gemini_cli", "antigravity"),
  [switch]$OverwriteExisting,
  [switch]$PruneManaged,
  [switch]$NoBackup,
  [switch]$DryRun
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Resolve-TargetAliases {
  param([string[]]$RawTargets)

  $resolved = @()
  foreach ($target in $RawTargets) {
    $raw = ""
    if ($null -ne $target) {
      $raw = [string]$target
    }
    $name = $raw.Trim().ToLowerInvariant()
    if (-not $name) { continue }

    switch ($name) {
      "gemini" { $resolved += "gemini_cli"; continue }
      "gemini_shell" { $resolved += "gemini_cli"; continue }
      "gemini-cli" { $resolved += "gemini_cli"; continue }
      default { $resolved += $name; continue }
    }
  }

  return @($resolved | Select-Object -Unique)
}

$syncScript = Join-Path $RepoRoot "scripts/sync/sync-skills.ps1"
if (-not (Test-Path $syncScript)) {
  throw "Sync script not found: $syncScript"
}

if ($OverwriteExisting) {
  Write-Warning "-OverwriteExisting is deprecated in this wrapper. Use ai-sync.yaml sync.skills_mode to control behavior."
}

if ($PruneManaged) {
  Write-Warning "-PruneManaged is deprecated in this wrapper. Use ai-sync.yaml sync.skills_mode='replace' when full replacement is required."
}

$resolvedTargets = Resolve-TargetAliases -RawTargets $Targets

$syncArgs = @{
  RepoRoot = $RepoRoot
  Targets  = $resolvedTargets
}

if ($ConfigPath) {
  $syncArgs["ConfigPath"] = $ConfigPath
}

if ($NoBackup) {
  $syncArgs["NoBackup"] = $true
}

if ($DryRun) {
  $syncArgs["DryRun"] = $true
}

& $syncScript @syncArgs
