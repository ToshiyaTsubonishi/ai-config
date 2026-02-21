[CmdletBinding()]
param(
  [string]$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "../..")).Path,
  [string]$ConfigPath,
  [string[]]$Targets,
  [switch]$NoBackup,
  [switch]$DryRun
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$legacyScript = Join-Path $PSScriptRoot "sync-gemini-context.ps1"
if (-not (Test-Path $legacyScript)) {
  throw "Required script not found: $legacyScript"
}

$args = @{
  RepoRoot = $RepoRoot
}

if ($PSBoundParameters.ContainsKey("ConfigPath")) {
  $args["ConfigPath"] = $ConfigPath
}

if ($PSBoundParameters.ContainsKey("Targets")) {
  $args["Targets"] = $Targets
}

if ($NoBackup) {
  $args["NoBackup"] = $true
}

if ($DryRun) {
  $args["DryRun"] = $true
}

& $legacyScript @args
