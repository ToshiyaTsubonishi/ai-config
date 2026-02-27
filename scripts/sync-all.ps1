[CmdletBinding()]
param(
  [string]$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path,
  [string]$ConfigPath,
  [string[]]$Targets = @("codex", "gemini_cli", "antigravity"),
  [string[]]$McpTargets,
  [string[]]$SkillTargets,
  [switch]$SkipWindowsEnvSync,
  [switch]$SkipEnvSync,
  [switch]$SkipBaselineSkillImport,
  [switch]$NoBackup,
  [switch]$StrictVariables,
  [switch]$OverwriteExistingSkills,
  [switch]$PruneManagedSkills,
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

$syncMcpScript = Join-Path $RepoRoot "scripts/sync/sync-mcp.ps1"
$syncSkillsScript = Join-Path $RepoRoot "scripts/sync/sync-skills.ps1"
$syncAgentContextScript = Join-Path $RepoRoot "scripts/sync/sync-agent-context.ps1"
$importBaselineSkillsScript = Join-Path $RepoRoot "scripts/import-antigravity-awesome-skills.ps1"
$inventoryScript = Join-Path $RepoRoot "scripts/export-inventory.ps1"
$syncEnvScript = Join-Path $RepoRoot "scripts/sync-env-files.ps1"
$workspaceRoot = Split-Path -Path $RepoRoot -Parent
$windowsEnvSyncScript = Join-Path $workspaceRoot "windows-env-sync/scripts/sync-windows-env.ps1"

foreach ($requiredScript in @($syncMcpScript, $syncSkillsScript, $syncAgentContextScript, $importBaselineSkillsScript, $inventoryScript, $syncEnvScript)) {
  if (-not (Test-Path $requiredScript)) {
    throw "Required script not found: $requiredScript"
  }
}

if ($StrictVariables) {
  Write-Warning "-StrictVariables is deprecated in sync-all.ps1 and ignored. Missing template variables are handled by scripts/sync/sync-mcp.ps1."
}

if ($OverwriteExistingSkills) {
  Write-Warning "-OverwriteExistingSkills is deprecated. Use ai-sync.yaml sync.skills_mode to control replacement behavior."
}

if ($PruneManagedSkills) {
  Write-Warning "-PruneManagedSkills is deprecated. Use ai-sync.yaml sync.skills_mode='replace' when full replacement is required."
}

if (-not $SkipBaselineSkillImport) {
  $baselineArgs = @{
    RepoRoot = $RepoRoot
  }

  if ($NoBackup) {
    $baselineArgs["NoBackup"] = $true
  }
  if ($DryRun) {
    $baselineArgs["DryRun"] = $true
  }

  & $importBaselineSkillsScript @baselineArgs
}

$defaultTargets = @(Resolve-TargetAliases -RawTargets $Targets)
$effectiveMcpTargets = @($defaultTargets)
$effectiveSkillTargets = @($defaultTargets)

if ($PSBoundParameters.ContainsKey("McpTargets")) {
  $effectiveMcpTargets = @(Resolve-TargetAliases -RawTargets $McpTargets)
}

if ($PSBoundParameters.ContainsKey("SkillTargets")) {
  $effectiveSkillTargets = @(Resolve-TargetAliases -RawTargets $SkillTargets)
}

$isWindowsPlatform = $false
if (Get-Variable -Name IsWindows -ErrorAction SilentlyContinue) {
  $isWindowsPlatform = [bool]$IsWindows
}
elseif ($env:OS -eq "Windows_NT") {
  $isWindowsPlatform = $true
}

if (-not $SkipEnvSync) {
  if ($DryRun) {
    Write-Host "[dry-run] skip env sync: $syncEnvScript"
  }
  else {
    & $syncEnvScript -RepoRoot $RepoRoot
  }
}

if (-not $SkipWindowsEnvSync -and $isWindowsPlatform) {
  if (Test-Path $windowsEnvSyncScript) {
    if ($DryRun) {
      Write-Host "[dry-run] skip windows env sync: $windowsEnvSyncScript"
    }
    else {
      & $windowsEnvSyncScript -NonInteractive
    }
  }
  else {
    Write-Warning "windows-env-sync not found at $windowsEnvSyncScript. Run scripts/fetch-repos.ps1 first."
  }
}

if ($effectiveMcpTargets.Count -gt 0) {
  $mcpArgs = @{
    RepoRoot = $RepoRoot
    Targets  = $effectiveMcpTargets
  }

  if ($ConfigPath) {
    $mcpArgs["ConfigPath"] = $ConfigPath
  }
  if ($NoBackup) {
    $mcpArgs["NoBackup"] = $true
  }
  if ($DryRun) {
    $mcpArgs["DryRun"] = $true
  }

  & $syncMcpScript @mcpArgs
}
else {
  Write-Host "[skip] MCP sync target list is empty."
}

if ($effectiveSkillTargets.Count -gt 0) {
  $skillsArgs = @{
    RepoRoot = $RepoRoot
    Targets  = $effectiveSkillTargets
  }

  if ($ConfigPath) {
    $skillsArgs["ConfigPath"] = $ConfigPath
  }
  if ($NoBackup) {
    $skillsArgs["NoBackup"] = $true
  }
  if ($DryRun) {
    $skillsArgs["DryRun"] = $true
  }

  & $syncSkillsScript @skillsArgs
}
else {
  Write-Host "[skip] Skills sync target list is empty."
}

$contextTargets = @($effectiveMcpTargets + $effectiveSkillTargets | Select-Object -Unique)
if ($null -eq $contextTargets) { $contextTargets = @() }
if ($contextTargets.Count -gt 0) {
  $contextArgs = @{
    RepoRoot = $RepoRoot
    Targets  = $contextTargets
  }

  if ($ConfigPath) {
    $contextArgs["ConfigPath"] = $ConfigPath
  }
  if ($NoBackup) {
    $contextArgs["NoBackup"] = $true
  }
  if ($DryRun) {
    $contextArgs["DryRun"] = $true
  }

  & $syncAgentContextScript @contextArgs
}
else {
  Write-Host "[skip] Agent context sync target list is empty."
}

if ($DryRun) {
  Write-Host "[dry-run] skip inventory export: $inventoryScript"
  Write-Host "[dry-run] skip ai_config dynamic index build"
}
else {
  & $inventoryScript -RepoRoot $RepoRoot

  # Build ai_config dynamic index
  Write-Host "Building ai_config dynamic tool index..."
  $pythonPath = Join-Path $RepoRoot ".venv/bin/python"
  if (Test-Path $pythonPath) {
    & $pythonPath -m ai_config.build_index --repo-root $RepoRoot
  }
  else {
    Write-Warning "Python environment not found at $pythonPath. Skipping dynamic index build."
  }
}

Write-Host "All sync operations completed."
