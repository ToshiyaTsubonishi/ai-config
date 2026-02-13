[CmdletBinding()]
param(
  [string]$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path,
  [string]$SkillsShUrl = "https://skills.sh/",
  [int]$TopN = 500,
  [string]$Agent = "codex",
  [int]$ChunkSize = 20,
  [switch]$OverwriteImported,
  [switch]$SkipInstall
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

if ($TopN -lt 1) {
  throw "TopN must be >= 1"
}

if ($ChunkSize -lt 1) {
  throw "ChunkSize must be >= 1"
}

function Parse-SkillsFromHtml {
  param([Parameter(Mandatory = $true)][string]$Html)

  $pattern = 'initialSkills\\":\[(?<skills>.+?)\],\\"totalSkills\\":(?<total>\d+),\\"allTimeTotal\\":(?<all>\d+),\\"view\\":\\"(?<view>[^\\"]+)\\"'
  $match = [regex]::Match($Html, $pattern, [System.Text.RegularExpressions.RegexOptions]::Singleline)

  if (-not $match.Success) {
    throw "Could not parse initialSkills from skills.sh HTML"
  }

  $skillsJson = "[" + $match.Groups["skills"].Value + "]"
  $skillsJson = $skillsJson -replace '\\"', '"' -replace '\\\\/', '/'
  $skills = $skillsJson | ConvertFrom-Json

  return [pscustomobject]@{
    Skills = @($skills)
    TotalSkills = [int]$match.Groups["total"].Value
    AllTimeTotal = [int]$match.Groups["all"].Value
    View = $match.Groups["view"].Value
  }
}

function Chunk-Array {
  param(
    [Parameter(Mandatory = $true)][object[]]$InputArray,
    [Parameter(Mandatory = $true)][int]$Size
  )

  $chunks = @()
  for ($i = 0; $i -lt $InputArray.Count; $i += $Size) {
    $end = [Math]::Min($i + $Size - 1, $InputArray.Count - 1)
    $segment = @($InputArray[$i..$end])
    $chunks += ,$segment
  }
  return $chunks
}

function Resolve-StagedSkillDir {
  param(
    [Parameter(Mandatory = $true)][string]$StageSkillsRoot,
    [Parameter(Mandatory = $true)][string]$SkillId
  )

  $exact = Join-Path $StageSkillsRoot $SkillId
  if (Test-Path $exact) {
    return $exact
  }

  $normalized = ($SkillId -replace '[^A-Za-z0-9._-]', '-')
  $normalized = ($normalized -replace '-{2,}', '-').Trim('-')
  if (-not [string]::IsNullOrWhiteSpace($normalized)) {
    $normalizedPath = Join-Path $StageSkillsRoot $normalized
    if (Test-Path $normalizedPath) {
      return $normalizedPath
    }
  }

  $candidates = @(Get-ChildItem -Path $StageSkillsRoot -Directory | Where-Object { $_.Name -like "$normalized*" })
  if ($candidates.Count -eq 1) {
    return $candidates[0].FullName
  }

  return $null
}

function Get-SafeDirectoryName {
  param([Parameter(Mandatory = $true)][string]$Name)

  $safe = $Name -replace '[<>:"/\\|?*]', '-'
  $safe = ($safe -replace '\s+', '-')
  $safe = ($safe -replace '-{2,}', '-').Trim('-')

  if ([string]::IsNullOrWhiteSpace($safe)) {
    return "_"
  }

  return $safe
}

function Get-DisplayNameFromSkillId {
  param([Parameter(Mandatory = $true)][string]$SkillId)

  $raw = ($SkillId -replace '[:_-]+', ' ').Trim()
  if ([string]::IsNullOrWhiteSpace($raw)) {
    return $SkillId
  }

  $parts = @()
  foreach ($token in ($raw -split '\s+')) {
    if ($token.Length -le 3) {
      $parts += $token.ToUpperInvariant()
      continue
    }

    $parts += ($token.Substring(0, 1).ToUpperInvariant() + $token.Substring(1).ToLowerInvariant())
  }

  return ($parts -join ' ')
}

$importRoot = Join-Path $RepoRoot "skills/imported/skills-sh"
$sourcesRoot = Join-Path $importRoot "sources"
$statePath = Join-Path $importRoot ("import-state.top{0}.json" -f $TopN)
$manifestPath = Join-Path $importRoot ("manifest.top{0}.json" -f $TopN)
$summaryPath = Join-Path $importRoot ("summary.top{0}.json" -f $TopN)

$stageRoot = Join-Path $RepoRoot ".skills-import-stage/skills-sh"
$stageProjectRoot = Join-Path $stageRoot ("top{0}" -f $TopN)
$stageSkillsRoot = Join-Path $stageProjectRoot ".agents/skills"

foreach ($dir in @($importRoot, $sourcesRoot, $stageProjectRoot)) {
  if (-not (Test-Path $dir)) {
    New-Item -ItemType Directory -Force -Path $dir | Out-Null
  }
}

Write-Host "[fetch] $SkillsShUrl"
$html = (curl.exe -L -s $SkillsShUrl | Out-String)
if ([string]::IsNullOrWhiteSpace($html)) {
  throw "Failed to fetch skills.sh HTML"
}

$parsed = Parse-SkillsFromHtml -Html $html
$allSkills = @($parsed.Skills | Sort-Object installs -Descending)
$topSkills = @($allSkills | Select-Object -First $TopN)

$rank = 1
$topWithRank = foreach ($skill in $topSkills) {
  [pscustomobject]@{
    rank = $rank
    source = [string]$skill.source
    skillId = [string]$skill.skillId
    name = [string]$skill.name
    installs = [int]$skill.installs
  }
  $rank++
}

$manifest = [pscustomobject]@{
  generatedAt = (Get-Date).ToString("o")
  sourceUrl = $SkillsShUrl
  view = $parsed.View
  totalSkills = $parsed.TotalSkills
  allTimeTotal = $parsed.AllTimeTotal
  topN = $TopN
  count = @($topWithRank).Count
  skills = $topWithRank
}
$manifest | ConvertTo-Json -Depth 8 | Set-Content -Path $manifestPath -Encoding utf8NoBOM
Write-Host "[ok] manifest -> $manifestPath"

$state = @{}
if (Test-Path $statePath) {
  try {
    $existingState = Get-Content -Raw $statePath | ConvertFrom-Json -AsHashtable
    if ($existingState.ContainsKey("completed") -and $existingState["completed"] -is [hashtable]) {
      $state = $existingState["completed"]
    }
  }
  catch {
    Write-Warning "Could not parse existing state file. A new state will be created."
  }
}

$bySource = $topWithRank | Group-Object source | Sort-Object Name
$installed = 0
$skipped = 0
$failed = @()

foreach ($sourceGroup in $bySource) {
  $source = [string]$sourceGroup.Name
  $entries = @($sourceGroup.Group | Sort-Object rank)

  $pendingEntries = @()
  foreach ($entry in $entries) {
    $key = "{0}::{1}" -f $entry.source, $entry.skillId
    if ($state.ContainsKey($key) -and -not $OverwriteImported) {
      $skipped++
      continue
    }
    $pendingEntries += $entry
  }

  if (@($pendingEntries).Count -eq 0) {
    Write-Host "[skip] $source (already imported)"
    continue
  }

  $skillIds = @($pendingEntries | ForEach-Object { $_.skillId })
  $chunks = Chunk-Array -InputArray $skillIds -Size $ChunkSize

  foreach ($chunk in $chunks) {
    if (-not $SkipInstall) {
      $chunkItems = @($chunk)
      Write-Host "[install] $source ($($chunkItems.Count) skill(s))"
      $args = @("--yes", "skills", "add", $source, "--agent", $Agent, "-y")
      foreach ($skillId in $chunkItems) {
        $args += @("--skill", $skillId)
      }

      Push-Location $stageProjectRoot
      try {
        & npx.cmd @args
      }
      catch {
        $msg = $_.Exception.Message
        Write-Warning "Install failed for source '$source': $msg"
        foreach ($skillId in $chunkItems) {
          $failed += [pscustomobject]@{
            source = $source
            skillId = $skillId
            error = $msg
          }
        }
      }
      finally {
        Pop-Location
      }
    }
  }

  $sourceKey = ($source -replace '[^A-Za-z0-9._-]', '__')
  $targetSourceRoot = Join-Path $sourcesRoot $sourceKey
  if (-not (Test-Path $targetSourceRoot)) {
    New-Item -ItemType Directory -Force -Path $targetSourceRoot | Out-Null
  }

  foreach ($entry in $pendingEntries) {
    $stagedSkillDir = Resolve-StagedSkillDir -StageSkillsRoot $stageSkillsRoot -SkillId $entry.skillId
    if (-not $stagedSkillDir -and -not $SkipInstall) {
      $displayName = Get-DisplayNameFromSkillId -SkillId $entry.skillId
      if (-not [string]::Equals($displayName, $entry.skillId, [System.StringComparison]::Ordinal)) {
        Write-Host "[retry] $($entry.source) skillId='$($entry.skillId)' displayName='$displayName'"
        Push-Location $stageProjectRoot
        try {
          & npx.cmd --yes skills add $entry.source --agent $Agent -y --skill $displayName | Out-Null
        }
        catch {
          # Continue and mark as unresolved below if still not found.
        }
        finally {
          Pop-Location
        }

        $stagedSkillDir = Resolve-StagedSkillDir -StageSkillsRoot $stageSkillsRoot -SkillId $entry.skillId
        if (-not $stagedSkillDir) {
          $stagedSkillDir = Resolve-StagedSkillDir -StageSkillsRoot $stageSkillsRoot -SkillId $displayName
        }
      }
    }

    if (-not $stagedSkillDir) {
      $failed += [pscustomobject]@{
        source = $entry.source
        skillId = $entry.skillId
        error = "Skill directory not found in stage after install"
      }
      continue
    }

    $destName = Get-SafeDirectoryName -Name $entry.skillId
    $destDir = Join-Path $targetSourceRoot $destName
    try {
      if (Test-Path -LiteralPath $destDir -PathType Leaf) {
        Remove-Item -LiteralPath $destDir -Force
      }
      if (-not (Test-Path -LiteralPath $destDir)) {
        New-Item -ItemType Directory -Force -Path $destDir | Out-Null
      }

      Copy-Item -Path (Join-Path $stagedSkillDir "*") -Destination $destDir -Recurse -Force

      $metaPath = Join-Path $destDir ".skills-sh-meta.json"
      [pscustomobject]@{
        importedAt = (Get-Date).ToString("o")
        source = $entry.source
        sourceKey = $sourceKey
        skillId = $entry.skillId
        directoryName = $destName
        name = $entry.name
        installs = $entry.installs
        rank = $entry.rank
        topN = $TopN
      } | ConvertTo-Json -Depth 5 | Set-Content -Path $metaPath -Encoding utf8NoBOM

      $key = "{0}::{1}" -f $entry.source, $entry.skillId
      $state[$key] = [pscustomobject]@{
        importedAt = (Get-Date).ToString("o")
        targetPath = $destDir
        rank = $entry.rank
        installs = $entry.installs
      }

      $installed++
    }
    catch {
      $failed += [pscustomobject]@{
        source = $entry.source
        skillId = $entry.skillId
        error = $_.Exception.Message
      }
      continue
    }
  }

  [pscustomobject]@{
    updatedAt = (Get-Date).ToString("o")
    topN = $TopN
    completed = $state
  } | ConvertTo-Json -Depth 8 | Set-Content -Path $statePath -Encoding utf8NoBOM
}

$topKeys = @($topWithRank | ForEach-Object { "{0}::{1}" -f $_.source, $_.skillId } | Sort-Object -Unique)
$completedTopCount = @($topKeys | Where-Object { $state.ContainsKey($_) }).Count
$unresolvedTopCount = $topKeys.Count - $completedTopCount

$summary = [pscustomobject]@{
  generatedAt = (Get-Date).ToString("o")
  topN = $TopN
  requested = @($topWithRank).Count
  installed = $installed
  skipped = $skipped
  failedCount = @($failed).Count
  failed = $failed
  topUniqueCount = $topKeys.Count
  completedInTopCount = $completedTopCount
  unresolvedInTopCount = $unresolvedTopCount
  completedCount = $state.Count
  unresolvedCount = $unresolvedTopCount
  manifestPath = $manifestPath
  statePath = $statePath
  importRoot = $importRoot
}
$summary | ConvertTo-Json -Depth 8 | Set-Content -Path $summaryPath -Encoding utf8NoBOM

Write-Host "[ok] summary -> $summaryPath"
Write-Host "Done. installed=$installed skipped=$skipped failed=$(@($failed).Count)"
