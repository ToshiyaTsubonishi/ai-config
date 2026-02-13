[CmdletBinding()]
param(
  [string]$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Add-SkillsFromRoot {
  param(
    [Parameter(Mandatory = $true)][object]$Bucket,
    [Parameter(Mandatory = $true)][string]$RootPath,
    [Parameter(Mandatory = $true)][string]$Scope,
    [string]$SourceRepo
  )

  if (-not (Test-Path $RootPath)) {
    return
  }

  $skillDirs = @(Get-ChildItem -Path $RootPath -Directory)
  foreach ($dir in $skillDirs) {
    $skillMd = Join-Path $dir.FullName "SKILL.md"
    if (-not (Test-Path $skillMd)) {
      continue
    }

    $meta = $null
    $metaPath = Join-Path $dir.FullName ".skills-sh-meta.json"
    if (Test-Path $metaPath) {
      try {
        $meta = Get-Content -Raw $metaPath | ConvertFrom-Json
      }
      catch {
        $meta = $null
      }
    }

    $null = $Bucket.Add([pscustomobject]@{
      skillName = $dir.Name
      skillNameLower = $dir.Name.ToLowerInvariant()
      scope = $Scope
      sourceRepo = if ($meta -and $meta.source) { [string]$meta.source } elseif ($SourceRepo) { $SourceRepo } else { "" }
      installs = if ($meta -and $meta.installs) { [int]$meta.installs } else { $null }
      rank = if ($meta -and $meta.rank) { [int]$meta.rank } else { $null }
      path = $dir.FullName
    })
  }
}

$inventoryDir = Join-Path $RepoRoot "inventory"
if (-not (Test-Path $inventoryDir)) {
  New-Item -ItemType Directory -Force -Path $inventoryDir | Out-Null
}

$all = New-Object 'System.Collections.Generic.List[object]'

Add-SkillsFromRoot -Bucket $all -RootPath (Join-Path $RepoRoot "skills/shared") -Scope "shared"
Add-SkillsFromRoot -Bucket $all -RootPath (Join-Path $RepoRoot "skills/codex") -Scope "codex-specific"
Add-SkillsFromRoot -Bucket $all -RootPath (Join-Path $RepoRoot "skills/gemini") -Scope "gemini-specific"
Add-SkillsFromRoot -Bucket $all -RootPath (Join-Path $RepoRoot "skills/antigravity") -Scope "antigravity-specific"

$importSourcesRoot = Join-Path $RepoRoot "skills/imported/skills-sh/sources"
if (Test-Path $importSourcesRoot) {
  foreach ($sourceDir in Get-ChildItem -Path $importSourcesRoot -Directory) {
    Add-SkillsFromRoot -Bucket $all -RootPath $sourceDir.FullName -Scope "imported" -SourceRepo $sourceDir.Name
  }
}

$groups = $all | Group-Object skillNameLower | Sort-Object Name
$duplicates = @()

foreach ($group in $groups) {
  if ($group.Count -lt 2) {
    continue
  }

  $items = @($group.Group | Sort-Object @{Expression = { if ($_.installs -ne $null) { -1 * $_.installs } else { [int]::MaxValue } }}, scope, skillName)

  $recommended = $null
  $sharedCandidate = $items | Where-Object { $_.scope -eq "shared" } | Select-Object -First 1
  if ($sharedCandidate) {
    $recommended = $sharedCandidate
  }
  else {
    $recommended = $items | Sort-Object @{Expression = { if ($_.installs -ne $null) { -1 * $_.installs } else { [int]::MaxValue } }} | Select-Object -First 1
  }

  $duplicates += [pscustomobject]@{
    skillName = $items[0].skillName
    occurrences = $group.Count
    recommendation = [pscustomobject]@{
      keepPath = $recommended.path
      keepScope = $recommended.scope
      keepSource = $recommended.sourceRepo
      reason = if ($sharedCandidate) { "shared takes precedence" } elseif ($recommended.installs -ne $null) { "highest installs in imported set" } else { "first deterministic entry" }
    }
    candidates = @($items)
  }
}

$jsonOutPath = Join-Path $inventoryDir "skill-duplicates.json"
$mdOutPath = Join-Path $inventoryDir "skill-duplicates.md"

$result = [pscustomobject]@{
  generatedAt = (Get-Date).ToString("o")
  totalSkillsScanned = $all.Count
  duplicateNameCount = $duplicates.Count
  duplicates = $duplicates
}
$result | ConvertTo-Json -Depth 8 | Set-Content -Path $jsonOutPath -Encoding utf8NoBOM

$lines = New-Object 'System.Collections.Generic.List[string]'
$lines.Add("# Skill Duplicate Audit") | Out-Null
$lines.Add("") | Out-Null
$lines.Add("- Generated: " + (Get-Date).ToString("u")) | Out-Null
$lines.Add("- Total scanned: " + $all.Count) | Out-Null
$lines.Add("- Duplicate names: " + $duplicates.Count) | Out-Null
$lines.Add("") | Out-Null

if ($duplicates.Count -eq 0) {
  $lines.Add("No duplicate skill names found.") | Out-Null
}
else {
  foreach ($dup in $duplicates) {
    $lines.Add("## " + $dup.skillName) | Out-Null
    $lines.Add("") | Out-Null
    $lines.Add("- Occurrences: " + $dup.occurrences) | Out-Null
    $lines.Add("- Recommended keep: " + $dup.recommendation.keepPath.Replace('\\', '/')) | Out-Null
    $lines.Add("- Reason: " + $dup.recommendation.reason) | Out-Null
    $lines.Add("") | Out-Null
    $lines.Add("Candidates:") | Out-Null
    foreach ($c in $dup.candidates) {
      $installsText = if ($c.installs -ne $null) { $c.installs } else { "n/a" }
      $sourceText = if ([string]::IsNullOrWhiteSpace($c.sourceRepo)) { "n/a" } else { $c.sourceRepo }
      $lines.Add(("{0} | scope={1} | source={2} | installs={3}" -f $c.path.Replace('\\', '/'), $c.scope, $sourceText, $installsText)) | Out-Null
    }
    $lines.Add("") | Out-Null
  }
}

$lines | Set-Content -Path $mdOutPath -Encoding utf8NoBOM

Write-Host "[ok] $jsonOutPath"
Write-Host "[ok] $mdOutPath"
Write-Host "Done. duplicates=$($duplicates.Count)"
