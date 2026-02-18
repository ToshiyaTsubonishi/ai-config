[CmdletBinding()]
param(
  [string]$WorkspaceRoot = $HOME,
  [string]$AiConfigRepoUrl = "https://github.com/ToshiyaTsubonishi/ai-config-sync.git",
  [string]$AiAgentCollectionRepoUrl = "https://github.com/ToshiyaTsubonishi/ai-agent-collection.git",
  [string]$ModernGalleryRepoUrl = "https://github.com/ToshiyaTsubonishi/ModernGallery.git",
  [string]$WindowsEnvSyncRepoUrl = "https://github.com/ToshiyaTsubonishi/windows-env-sync.git",
  [string]$GitPath = "git",
  [switch]$NoPull,
  [switch]$DryRun
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Resolve-GitExecutable {
  param([Parameter(Mandatory = $true)][string]$Candidate)

  if (-not [string]::IsNullOrWhiteSpace($Candidate)) {
    $cmd = Get-Command $Candidate -ErrorAction SilentlyContinue
    if ($cmd -and -not [string]::IsNullOrWhiteSpace($cmd.Source)) {
      return $cmd.Source
    }
  }

  $fallbacks = @(
    (Join-Path $env:ProgramFiles "Git/cmd/git.exe"),
    (Join-Path $env:ProgramFiles "Git/bin/git.exe"),
    (Join-Path $env:LOCALAPPDATA "Programs/Git/cmd/git.exe")
  )

  foreach ($path in $fallbacks) {
    if (-not [string]::IsNullOrWhiteSpace($path) -and (Test-Path $path)) {
      return $path
    }
  }

  return $null
}

function Invoke-Git {
  param(
    [Parameter(Mandatory = $true)][string[]]$Args,
    [string]$WorkingDirectory
  )

  $display = "git " + ($Args -join " ")
  if ($WorkingDirectory) {
    $display = "git -C $WorkingDirectory " + ($Args -join " ")
  }

  if ($DryRun) {
    Write-Host "[dry-run] $display"
    return ""
  }

  if ($WorkingDirectory) {
    & $script:GitExe -C $WorkingDirectory @Args
  } else {
    & $script:GitExe @Args
  }

  if ($LASTEXITCODE -ne 0) {
    throw "Git command failed: $display"
  }
}

$script:GitExe = Resolve-GitExecutable -Candidate $GitPath
if (-not $script:GitExe) {
  throw "git command not found. Install Git or set -GitPath."
}

$root = (Resolve-Path $WorkspaceRoot).Path

$repos = @(
  [pscustomobject]@{ Name = "ai-config"; Url = $AiConfigRepoUrl; Path = (Join-Path $root "ai-config") },
  [pscustomobject]@{ Name = "ai-agent-collection"; Url = $AiAgentCollectionRepoUrl; Path = (Join-Path $root "ai-agent-collection") },
  [pscustomobject]@{ Name = "ModernGallery"; Url = $ModernGalleryRepoUrl; Path = (Join-Path $root "ModernGallery") },
  [pscustomobject]@{ Name = "windows-env-sync"; Url = $WindowsEnvSyncRepoUrl; Path = (Join-Path $root "windows-env-sync") }
)

foreach ($repo in $repos) {
  if (-not (Test-Path $repo.Path)) {
    Write-Host "[clone] $($repo.Name)"
    Invoke-Git -Args @("clone", $repo.Url, $repo.Path)
    continue
  }

  if (-not (Test-Path (Join-Path $repo.Path ".git"))) {
    throw "Path exists but is not a git repository: $($repo.Path)"
  }

  if ($NoPull) {
    Write-Host "[skip] Pull skipped for $($repo.Name)"
    continue
  }

  Write-Host "[update] $($repo.Name)"
  Invoke-Git -Args @("fetch", "--all", "--prune") -WorkingDirectory $repo.Path

  $branch = ""
  if ($DryRun) {
    $branch = "(dry-run)"
  } else {
    $branch = (& $script:GitExe -C $repo.Path rev-parse --abbrev-ref HEAD).Trim()
  }

  if ($branch -eq "HEAD") {
    Write-Warning "Detached HEAD detected in $($repo.Name). Skip pull."
    continue
  }

  try {
    Invoke-Git -Args @("pull", "--ff-only") -WorkingDirectory $repo.Path
  } catch {
    Write-Warning "Could not fast-forward pull in $($repo.Name). Manual resolve may be required."
  }
}

Write-Host "Repository fetch/update completed."
