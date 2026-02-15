[CmdletBinding()]
param(
  [string]$InputDir,
  [string]$AntigravityUserDir = (Join-Path $env:APPDATA "Antigravity/User"),
  [string]$AntigravityCliPath = (Join-Path $env:LOCALAPPDATA "Programs/Antigravity/bin/antigravity.cmd"),
  [switch]$SkipSettings,
  [switch]$SkipSnippets,
  [switch]$SkipExtensions,
  [switch]$SkipGlobalStorage,
  [switch]$ForceExtensions,
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

function Replace-DirectoryIfExists {
  param(
    [Parameter(Mandatory = $true)][string]$Source,
    [Parameter(Mandatory = $true)][string]$Destination
  )
  if (-not (Test-Path $Source)) {
    return $false
  }

  if ($DryRun) {
    Write-Host "[dry-run] replace dir $Destination <- $Source"
    return $true
  }

  if (Test-Path $Destination) {
    Remove-Item -Path $Destination -Recurse -Force
  }
  Copy-Item -Path $Source -Destination $Destination -Recurse -Force
  return $true
}

function Get-ExtensionEntries {
  param([Parameter(Mandatory = $true)][string]$BaseDir)

  $manifestPath = Join-Path $BaseDir "extensions-manifest.txt"
  if (Test-Path $manifestPath) {
    $lines = Get-Content -Path $manifestPath |
      ForEach-Object { $_.Trim() } |
      Where-Object { -not [string]::IsNullOrWhiteSpace($_) } |
      Where-Object { -not $_.StartsWith("#") }
    if ($lines.Count -gt 0) {
      return $lines
    }
  }

  $extensionsJsonPath = Join-Path $BaseDir "extensions.json"
  if (-not (Test-Path $extensionsJsonPath)) {
    return @()
  }

  $raw = Get-Content -Path $extensionsJsonPath -Raw
  if ([string]::IsNullOrWhiteSpace($raw)) {
    return @()
  }

  $rows = ConvertFrom-Json -InputObject $raw
  if (-not $rows) {
    return @()
  }

  $map = [ordered]@{}
  foreach ($row in $rows) {
    if ($null -eq $row.identifier -or [string]::IsNullOrWhiteSpace($row.identifier.id)) {
      continue
    }

    $id = $row.identifier.id.Trim()
    $version = ""
    if ($null -ne $row.version -and -not [string]::IsNullOrWhiteSpace([string]$row.version)) {
      $version = ([string]$row.version).Trim()
    }

    if ([string]::IsNullOrWhiteSpace($version)) {
      $map[$id] = $id
    } else {
      $map[$id] = "$id@$version"
    }
  }

  return @($map.Values)
}

if ([string]::IsNullOrWhiteSpace($InputDir)) {
  $repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
  $InputDir = Join-Path $repoRoot "inventory/antigravity/latest"
}

if (-not (Test-Path $InputDir)) {
  throw "Input directory not found: $InputDir"
}
$InputDir = (Resolve-Path $InputDir).Path

Ensure-Directory -Path $AntigravityUserDir

$sourceUserDir = Join-Path $InputDir "user"
if (Test-Path $sourceUserDir) {
  if (-not $SkipSettings) {
    [void](Copy-FileIfExists `
      -Source (Join-Path $sourceUserDir "settings.json") `
      -Destination (Join-Path $AntigravityUserDir "settings.json"))
    [void](Copy-FileIfExists `
      -Source (Join-Path $sourceUserDir "keybindings.json") `
      -Destination (Join-Path $AntigravityUserDir "keybindings.json"))
  }

  if (-not $SkipSnippets) {
    [void](Replace-DirectoryIfExists `
      -Source (Join-Path $sourceUserDir "snippets") `
      -Destination (Join-Path $AntigravityUserDir "snippets"))
  }

  if (-not $SkipGlobalStorage) {
    [void](Replace-DirectoryIfExists `
      -Source (Join-Path $sourceUserDir "globalStorage") `
      -Destination (Join-Path $AntigravityUserDir "globalStorage"))
  }
}

if (-not $SkipExtensions) {
  if (-not (Test-Path $AntigravityCliPath)) {
    throw "Antigravity CLI not found: $AntigravityCliPath"
  }

  $entries = Get-ExtensionEntries -BaseDir $InputDir
  foreach ($entry in $entries) {
    if ([string]::IsNullOrWhiteSpace($entry)) {
      continue
    }

    $args = @("--install-extension", $entry)
    if ($ForceExtensions) {
      $args += "--force"
    }

    if ($DryRun) {
      Write-Host "[dry-run] $AntigravityCliPath $($args -join ' ')"
      continue
    }

    & $AntigravityCliPath @args
    if ($LASTEXITCODE -ne 0) {
      throw "Failed to install extension: $entry"
    }
  }
}

Write-Host "Antigravity import completed from: $InputDir"
