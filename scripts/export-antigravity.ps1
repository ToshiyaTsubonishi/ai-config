[CmdletBinding()]
param(
  [string]$OutputRoot,
  [string]$AntigravityUserDir = (Join-Path $env:APPDATA "Antigravity/User"),
  [string]$AntigravityExtensionsDir = (Join-Path $HOME ".antigravity/extensions"),
  [string]$AntigravityCliPath = (Join-Path $env:LOCALAPPDATA "Programs/Antigravity/bin/antigravity.cmd"),
  [switch]$IncludeGlobalStorage,
  [switch]$DryRun
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Ensure-Directory {
  param([Parameter(Mandatory = $true)][string]$Path)
  if ($DryRun) {
    Write-Host "[dry-run] mkdir $Path"
    return
  }
  New-Item -ItemType Directory -Path $Path -Force | Out-Null
}

function Remove-DirectoryIfExists {
  param([Parameter(Mandatory = $true)][string]$Path)
  if (-not (Test-Path $Path)) {
    return
  }
  if ($DryRun) {
    Write-Host "[dry-run] rmdir $Path"
    return
  }
  Remove-Item -Path $Path -Recurse -Force
}

function Copy-FileIfExists {
  param(
    [Parameter(Mandatory = $true)][string]$Source,
    [Parameter(Mandatory = $true)][string]$Destination
  )
  if (-not (Test-Path $Source)) {
    return $false
  }

  if ($DryRun) {
    Write-Host "[dry-run] copy file $Source -> $Destination"
    return $true
  }

  $destParent = Split-Path -Parent $Destination
  if (-not [string]::IsNullOrWhiteSpace($destParent)) {
    New-Item -ItemType Directory -Path $destParent -Force | Out-Null
  }

  Copy-Item -Path $Source -Destination $Destination -Force
  return $true
}

function Copy-DirectoryIfExists {
  param(
    [Parameter(Mandatory = $true)][string]$Source,
    [Parameter(Mandatory = $true)][string]$Destination
  )
  if (-not (Test-Path $Source)) {
    return $false
  }

  if ($DryRun) {
    Write-Host "[dry-run] copy dir $Source -> $Destination"
    return $true
  }

  $destParent = Split-Path -Parent $Destination
  if (-not [string]::IsNullOrWhiteSpace($destParent)) {
    New-Item -ItemType Directory -Path $destParent -Force | Out-Null
  }

  Copy-Item -Path $Source -Destination $Destination -Recurse -Force
  return $true
}

function Write-TextFile {
  param(
    [Parameter(Mandatory = $true)][string]$Path,
    [Parameter(Mandatory = $true)][string]$Content
  )
  if ($DryRun) {
    Write-Host "[dry-run] write text $Path"
    return
  }

  $destParent = Split-Path -Parent $Path
  if (-not [string]::IsNullOrWhiteSpace($destParent)) {
    New-Item -ItemType Directory -Path $destParent -Force | Out-Null
  }

  $Content | Set-Content -Path $Path -Encoding UTF8
}

if ([string]::IsNullOrWhiteSpace($OutputRoot)) {
  $repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
  $OutputRoot = Join-Path $repoRoot "inventory/antigravity"
}

$timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
$snapshotDir = Join-Path $OutputRoot ("snapshot-" + $timestamp)
$latestDir = Join-Path $OutputRoot "latest"

if (-not (Test-Path $AntigravityUserDir)) {
  throw "Antigravity user directory not found: $AntigravityUserDir"
}

Ensure-Directory -Path $snapshotDir
Remove-DirectoryIfExists -Path $latestDir
Ensure-Directory -Path $latestDir

$snapshotUserDir = Join-Path $snapshotDir "user"
$latestUserDir = Join-Path $latestDir "user"
Ensure-Directory -Path $snapshotUserDir
Ensure-Directory -Path $latestUserDir

$copiedSettings = Copy-FileIfExists `
  -Source (Join-Path $AntigravityUserDir "settings.json") `
  -Destination (Join-Path $snapshotUserDir "settings.json")
[void](Copy-FileIfExists `
  -Source (Join-Path $AntigravityUserDir "settings.json") `
  -Destination (Join-Path $latestUserDir "settings.json"))

$copiedKeybindings = Copy-FileIfExists `
  -Source (Join-Path $AntigravityUserDir "keybindings.json") `
  -Destination (Join-Path $snapshotUserDir "keybindings.json")
[void](Copy-FileIfExists `
  -Source (Join-Path $AntigravityUserDir "keybindings.json") `
  -Destination (Join-Path $latestUserDir "keybindings.json"))

$copiedSnippets = Copy-DirectoryIfExists `
  -Source (Join-Path $AntigravityUserDir "snippets") `
  -Destination (Join-Path $snapshotUserDir "snippets")
[void](Copy-DirectoryIfExists `
  -Source (Join-Path $AntigravityUserDir "snippets") `
  -Destination (Join-Path $latestUserDir "snippets"))

$copiedGlobalStorage = $false
if ($IncludeGlobalStorage) {
  $copiedGlobalStorage = Copy-DirectoryIfExists `
    -Source (Join-Path $AntigravityUserDir "globalStorage") `
    -Destination (Join-Path $snapshotUserDir "globalStorage")
  [void](Copy-DirectoryIfExists `
    -Source (Join-Path $AntigravityUserDir "globalStorage") `
    -Destination (Join-Path $latestUserDir "globalStorage"))
}

[void](Copy-FileIfExists `
  -Source (Join-Path $AntigravityExtensionsDir "extensions.json") `
  -Destination (Join-Path $snapshotDir "extensions.json"))
[void](Copy-FileIfExists `
  -Source (Join-Path $AntigravityExtensionsDir "extensions.json") `
  -Destination (Join-Path $latestDir "extensions.json"))

$extensionManifestLines = @()
if (Test-Path $AntigravityCliPath) {
  if ($DryRun) {
    Write-Host "[dry-run] $AntigravityCliPath --list-extensions --show-versions"
  } else {
    $extensionManifestLines = & $AntigravityCliPath --list-extensions --show-versions
    if ($LASTEXITCODE -ne 0) {
      throw "Failed to list extensions via Antigravity CLI."
    }
  }
} else {
  Write-Warning "Antigravity CLI not found. Skip extension manifest export: $AntigravityCliPath"
}

if ($DryRun -or $extensionManifestLines.Count -gt 0) {
  $manifestBody = if ($DryRun) {
    "# dry-run"
  } else {
    ($extensionManifestLines -join [Environment]::NewLine)
  }
  Write-TextFile -Path (Join-Path $snapshotDir "extensions-manifest.txt") -Content $manifestBody
  Write-TextFile -Path (Join-Path $latestDir "extensions-manifest.txt") -Content $manifestBody
}

$metadata = [ordered]@{
  exportedAtUtc = (Get-Date).ToUniversalTime().ToString("o")
  source = [ordered]@{
    userDir = $AntigravityUserDir
    extensionsDir = $AntigravityExtensionsDir
    cliPath = $AntigravityCliPath
  }
  copied = [ordered]@{
    settings = $copiedSettings
    keybindings = $copiedKeybindings
    snippets = $copiedSnippets
    globalStorage = $copiedGlobalStorage
    includeGlobalStorage = [bool]$IncludeGlobalStorage
    extensionManifestCount = if ($DryRun) { 0 } else { $extensionManifestLines.Count }
  }
}

$metadataJson = $metadata | ConvertTo-Json -Depth 5
Write-TextFile -Path (Join-Path $snapshotDir "metadata.json") -Content $metadataJson
Write-TextFile -Path (Join-Path $latestDir "metadata.json") -Content $metadataJson

Write-Host "Antigravity export completed."
Write-Host "  snapshot: $snapshotDir"
Write-Host "  latest:   $latestDir"
