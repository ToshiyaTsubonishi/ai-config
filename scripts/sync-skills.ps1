[CmdletBinding()]
param(
  [string]$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path,
  [string[]]$Targets = @("codex", "gemini", "antigravity"),
  [switch]$OverwriteExisting,
  [switch]$PruneManaged
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$ManagedMarker = ".ai-config-managed"

function Read-DotEnv {
  param([Parameter(Mandatory = $true)][string]$Path)

  $vars = @{}
  if (-not (Test-Path $Path)) {
    return $vars
  }

  foreach ($rawLine in Get-Content $Path) {
    $line = $rawLine.Trim()
    if (-not $line -or $line.StartsWith("#")) { continue }
    if ($line.StartsWith("export ")) {
      $line = $line.Substring(7).Trim()
    }

    $idx = $line.IndexOf("=")
    if ($idx -lt 1) { continue }

    $key = $line.Substring(0, $idx).Trim()
    $value = $line.Substring($idx + 1).Trim()

    if (((($value.StartsWith('"')) -and ($value.EndsWith('"'))) -or (($value.StartsWith("'")) -and ($value.EndsWith("'")))) -and $value.Length -ge 2) {
      $value = $value.Substring(1, $value.Length - 2)
    }

    if ($key) {
      $vars[$key] = $value
    }
  }

  return $vars
}

function Resolve-TargetPath {
  param(
    [Parameter(Mandatory = $true)][string]$DefaultPath,
    [string]$PathVarName,
    [Parameter(Mandatory = $true)][hashtable]$Variables
  )

  if ($PathVarName -and $Variables.ContainsKey($PathVarName) -and -not [string]::IsNullOrWhiteSpace([string]$Variables[$PathVarName])) {
    return [System.Environment]::ExpandEnvironmentVariables([string]$Variables[$PathVarName])
  }

  return [System.Environment]::ExpandEnvironmentVariables($DefaultPath)
}

$dotenvPath = Join-Path $RepoRoot ".env"
$fromDotEnv = Read-DotEnv -Path $dotenvPath

$vars = @{}
foreach ($entry in $fromDotEnv.GetEnumerator()) {
  $vars[$entry.Key] = $entry.Value
}
foreach ($entry in Get-ChildItem Env:) {
  $vars[$entry.Name] = $entry.Value
}

$targetsMap = @{
  codex = @{
    DefaultTarget = (Join-Path $HOME ".codex/skills")
    PathVar = "CODEX_SKILLS_PATH"
  }
  gemini = @{
    DefaultTarget = (Join-Path $HOME ".gemini/skills")
    PathVar = "GEMINI_SKILLS_PATH"
  }
  antigravity = @{
    DefaultTarget = (Join-Path $HOME ".gemini/antigravity/skills")
    PathVar = "ANTIGRAVITY_SKILLS_PATH"
  }
}

$sharedRoot = Join-Path $RepoRoot "skills/shared"
if (-not (Test-Path $sharedRoot)) {
  throw "Shared skills directory not found: $sharedRoot"
}

$sourceSkills = @(Get-ChildItem -Path $sharedRoot -Directory | Sort-Object Name)
$sourceSkillNames = @($sourceSkills | ForEach-Object { $_.Name })

if ($sourceSkills.Count -eq 0) {
  Write-Warning "No shared skills found under $sharedRoot"
}

foreach ($target in $Targets) {
  if (-not $targetsMap.ContainsKey($target)) {
    $supported = ($targetsMap.Keys | Sort-Object) -join ", "
    throw "Unknown target: $target. Supported targets: $supported"
  }

  $item = $targetsMap[$target]
  $targetRoot = Resolve-TargetPath -DefaultPath $item.DefaultTarget -PathVarName $item.PathVar -Variables $vars

  if (-not (Test-Path $targetRoot)) {
    New-Item -ItemType Directory -Force -Path $targetRoot | Out-Null
  }

  foreach ($skill in $sourceSkills) {
    $dest = Join-Path $targetRoot $skill.Name
    $markerPath = Join-Path $dest $ManagedMarker

    if (Test-Path $dest) {
      $isManaged = Test-Path $markerPath
      if (-not $isManaged -and -not $OverwriteExisting) {
        Write-Warning "[skip:$target] Existing unmanaged skill: $($skill.Name). Use -OverwriteExisting to replace."
        continue
      }

      Remove-Item -Path $dest -Recurse -Force
    }

    Copy-Item -Path $skill.FullName -Destination $dest -Recurse -Force
    Set-Content -Path (Join-Path $dest $ManagedMarker) -Value "Managed by ai-config sync-skills.ps1" -Encoding utf8NoBOM
    Write-Host "[ok:$target] $($skill.Name)"
  }

  if ($PruneManaged) {
    $existing = @(Get-ChildItem -Path $targetRoot -Directory)
    foreach ($dir in $existing) {
      $managedFlag = Join-Path $dir.FullName $ManagedMarker
      if ((Test-Path $managedFlag) -and ($sourceSkillNames -notcontains $dir.Name)) {
        Remove-Item -Path $dir.FullName -Recurse -Force
        Write-Host "[prune:$target] $($dir.Name)"
      }
    }
  }
}

Write-Host "Done."
