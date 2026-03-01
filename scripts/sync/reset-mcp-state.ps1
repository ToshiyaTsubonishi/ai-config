[CmdletBinding(SupportsShouldProcess = $true)]
param(
  [string]$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "../..")).Path,
  [switch]$NoBackup,
  [switch]$DryRun
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Get-UserHome {
  $userProfile = [System.Environment]::GetEnvironmentVariable("USERPROFILE")
  if (-not [string]::IsNullOrWhiteSpace($userProfile)) {
    return $userProfile
  }
  return $HOME
}

function Get-SafeRelativePath {
  param(
    [Parameter(Mandatory = $true)][string]$BasePath,
    [Parameter(Mandatory = $true)][string]$TargetPath
  )

  $baseFull = [System.IO.Path]::GetFullPath($BasePath)
  $targetFull = [System.IO.Path]::GetFullPath($TargetPath)

  $baseUri = New-Object System.Uri(($baseFull.TrimEnd('\') + '\'))
  $targetUri = New-Object System.Uri($targetFull)
  $relativeUri = $baseUri.MakeRelativeUri($targetUri).ToString()
  $relative = [System.Uri]::UnescapeDataString($relativeUri).Replace('/', [System.IO.Path]::DirectorySeparatorChar)

  if ([string]::IsNullOrWhiteSpace($relative) -or $relative.StartsWith("..")) {
    return ($targetFull -replace "[:\\\/]", "_")
  }

  return $relative
}

$userHome = Get-UserHome
if ([string]::IsNullOrWhiteSpace($userHome)) {
  throw "Could not resolve user home directory."
}

$isDryRun = [bool]$DryRun
$createBackup = -not [bool]$NoBackup
$timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
$backupRoot = Join-Path $userHome ".mcp-reset-backups"
$sessionBackupRoot = Join-Path $backupRoot $timestamp

$pathsToReset = @(
  (Join-Path $userHome ".codex\config.toml"),
  (Join-Path $userHome ".gemini\settings.json"),
  (Join-Path $userHome ".gemini\antigravity\mcp_config.json"),
  (Join-Path $userHome ".agent\mcp_config.json")
)

$claudeDir = Join-Path $userHome ".claude"
if (Test-Path $claudeDir) {
  $claudeMcpFiles = Get-ChildItem -Path $claudeDir -Recurse -File -ErrorAction SilentlyContinue |
    Where-Object { $_.FullName -match "(?i)mcp" } |
    Select-Object -ExpandProperty FullName

  if ($claudeMcpFiles) {
    $pathsToReset += $claudeMcpFiles
  }
}

$uniquePaths = @($pathsToReset | Where-Object { -not [string]::IsNullOrWhiteSpace($_) } | Select-Object -Unique)
if (-not $uniquePaths -or $uniquePaths.Count -eq 0) {
  Write-Host "No MCP state targets resolved. Nothing to reset."
  exit 0
}

foreach ($targetPath in $uniquePaths) {
  if (-not (Test-Path $targetPath)) {
    Write-Host "[skip] not found: $targetPath"
    continue
  }

  if ($createBackup) {
    $relativePath = Get-SafeRelativePath -BasePath $userHome -TargetPath $targetPath
    $backupPath = Join-Path $sessionBackupRoot $relativePath
    $backupDir = Split-Path -Path $backupPath -Parent

    if ($isDryRun) {
      Write-Host "[dry-run] backup $targetPath -> $backupPath"
    }
    else {
      if (-not (Test-Path $backupDir)) {
        New-Item -Path $backupDir -ItemType Directory -Force | Out-Null
      }
      Copy-Item -LiteralPath $targetPath -Destination $backupPath -Force
      Write-Host "[ok] backup -> $backupPath"
    }
  }

  if ($PSCmdlet.ShouldProcess($targetPath, "Reset MCP state file")) {
    if ($isDryRun) {
      Write-Host "[dry-run] remove $targetPath"
    }
    else {
      Remove-Item -LiteralPath $targetPath -Force
      Write-Host "[ok] removed $targetPath"
    }
  }
}

if ($createBackup -and -not $isDryRun -and (Test-Path $sessionBackupRoot)) {
  Write-Host "Backup root: $sessionBackupRoot"
}

Write-Host "MCP state reset completed."
