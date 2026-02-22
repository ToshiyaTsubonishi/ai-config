[CmdletBinding()]
param(
  [string]$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path,
  [string]$SourceRepo = "https://github.com/tsytbns/antigravity-awesome-skills",
  [string]$Ref = "main",
  [switch]$NoBackup,
  [switch]$KeepTemp,
  [switch]$DryRun
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Ensure-Directory {
  param([Parameter(Mandatory = $true)][string]$Path)

  if (Test-Path $Path) { return }

  if ($DryRun) {
    Write-Host "[dry-run] mkdir $Path"
    return
  }

  New-Item -ItemType Directory -Force -Path $Path | Out-Null
}

function Remove-DirectoryContents {
  param([Parameter(Mandatory = $true)][string]$Path)

  if (-not (Test-Path $Path)) { return }

  foreach ($item in Get-ChildItem -Path $Path -Force -ErrorAction SilentlyContinue) {
    if ($DryRun) {
      Write-Host "[dry-run] remove $($item.FullName)"
      continue
    }

    Remove-Item -LiteralPath $item.FullName -Recurse -Force
  }
}

function Backup-DirectoryContents {
  param(
    [Parameter(Mandatory = $true)][string]$Path,
    [Parameter(Mandatory = $true)][string]$Suffix
  )

  if ($NoBackup) { return }
  if (-not (Test-Path $Path)) { return }

  $children = @(Get-ChildItem -Path $Path -Force -ErrorAction SilentlyContinue)
  if ($children.Count -eq 0) { return }

  $backupPath = "$Path.bak.$Suffix"
  if ($DryRun) {
    Write-Host "[dry-run] backup $Path -> $backupPath"
    return
  }

  Ensure-Directory -Path $backupPath
  foreach ($child in $children) {
    Copy-Item -Path $child.FullName -Destination $backupPath -Recurse -Force
  }
}

function Copy-DirectoryContents {
  param(
    [Parameter(Mandatory = $true)][string]$Source,
    [Parameter(Mandatory = $true)][string]$Destination
  )

  Ensure-Directory -Path $Destination

  foreach ($item in Get-ChildItem -Path $Source -Force -ErrorAction SilentlyContinue) {
    $destPath = Join-Path $Destination $item.Name
    if ($DryRun) {
      Write-Host "[dry-run] copy $($item.FullName) -> $destPath"
      continue
    }

    Copy-Item -Path $item.FullName -Destination $destPath -Recurse -Force
  }
}

$repoRootPath = (Resolve-Path $RepoRoot).Path
$repoRootPath = $repoRootPath.TrimEnd('\', '/')
$sourceRepoPath = $SourceRepo.TrimEnd('/')
$downloadUrl = "$sourceRepoPath/archive/refs/heads/$Ref.zip"
$timestamp = Get-Date -Format "yyyyMMdd-HHmmss"

$profileMap = @(
  [pscustomobject]@{ source = "codex-cli"; target = "codex" },
  [pscustomobject]@{ source = "gemini-cli"; target = "gemini" },
  [pscustomobject]@{ source = "antigravity"; target = "antigravity" }
)

if ($DryRun) {
  Write-Host "[dry-run] download $downloadUrl"
  foreach ($entry in $profileMap) {
    $dest = Join-Path $repoRootPath ("skills/{0}" -f $entry.target)
    Write-Host "[dry-run] replace $dest from repo:skills/$($entry.source)"
  }
  return
}

$tempRoot = Join-Path ([System.IO.Path]::GetTempPath()) ("ai-config-antigravity-awesome-skills-{0}" -f $timestamp)
$zipPath = Join-Path $tempRoot "source.zip"
$extractRoot = Join-Path $tempRoot "extract"

try {
  Ensure-Directory -Path $tempRoot
  Ensure-Directory -Path $extractRoot

  Write-Host "[fetch] $downloadUrl"
  Invoke-WebRequest -Uri $downloadUrl -OutFile $zipPath

  Write-Host "[extract] $zipPath"
  Expand-Archive -Path $zipPath -DestinationPath $extractRoot -Force

  $extractedRepo = Get-ChildItem -Path $extractRoot -Directory | Select-Object -First 1
  if (-not $extractedRepo) {
    throw "Could not locate extracted repository root under: $extractRoot"
  }

  $skillsRoot = Join-Path $extractedRepo.FullName "skills"
  if (-not (Test-Path $skillsRoot)) {
    throw "skills directory not found in extracted repository: $skillsRoot"
  }

  foreach ($entry in $profileMap) {
    $sourceDir = Join-Path $skillsRoot $entry.source
    if (-not (Test-Path $sourceDir)) {
      throw "Source profile directory not found: $sourceDir"
    }

    $targetDir = Join-Path $repoRootPath ("skills/{0}" -f $entry.target)
    Ensure-Directory -Path $targetDir

    Backup-DirectoryContents -Path $targetDir -Suffix $timestamp
    Remove-DirectoryContents -Path $targetDir
    Copy-DirectoryContents -Source $sourceDir -Destination $targetDir

    Write-Host "[ok] imported $($entry.source) -> $targetDir"
  }

  Write-Host "Baseline skills import completed."
}
finally {
  if (-not $KeepTemp -and (Test-Path $tempRoot)) {
    Remove-Item -Path $tempRoot -Recurse -Force -ErrorAction SilentlyContinue
  }
}
