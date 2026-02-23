[CmdletBinding(SupportsShouldProcess = $true)]
param(
  [string]$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "../..")).Path,
  [string]$ConfigPath,
  [string[]]$Targets,
  [switch]$NoBackup,
  [switch]$DryRun
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

if (-not $ConfigPath) {
  $ConfigPath = Join-Path $RepoRoot "config/master/ai-sync.yaml"
}

function ConvertTo-HashtableRecursive {
  param([AllowNull()]$Value)

  if ($null -eq $Value) { return $null }

  if ($Value -is [System.Collections.IDictionary]) {
    $result = @{}
    foreach ($key in $Value.Keys) {
      $result[[string]$key] = ConvertTo-HashtableRecursive -Value $Value[$key]
    }
    return $result
  }

  if (($Value -is [System.Collections.IEnumerable]) -and -not ($Value -is [string])) {
    $items = @()
    foreach ($item in $Value) {
      $items += , (ConvertTo-HashtableRecursive -Value $item)
    }
    return $items
  }

  return $Value
}

function Load-MasterConfig {
  param([Parameter(Mandatory = $true)][string]$Path)

  if (-not (Test-Path $Path)) {
    throw "Master config not found: $Path"
  }

  $raw = Get-Content -Path $Path -Raw
  $yamlCmd = Get-Command -Name ConvertFrom-Yaml -ErrorAction SilentlyContinue

  if ($yamlCmd) {
    $parsed = $raw | ConvertFrom-Yaml
    return ConvertTo-HashtableRecursive -Value $parsed
  }

  try {
    # JSON is valid YAML. This fallback keeps dependencies minimal.
    return ($raw | ConvertFrom-Json -AsHashtable -Depth 100)
  }
  catch {
    throw @"
Unable to parse '$Path' as YAML without ConvertFrom-Yaml.
Use PowerShell with ConvertFrom-Yaml available, or keep ai-sync.yaml JSON-compatible.
Original error: $($_.Exception.Message)
"@
  }
}

function Resolve-EnvExpressions {
  param([AllowNull()][string]$Value)

  if ($null -eq $Value) { return $null }

  $expanded = [System.Text.RegularExpressions.Regex]::Replace(
    $Value,
    '\$\{([A-Za-z_][A-Za-z0-9_]*)\}',
    {
      param($m)
      $name = $m.Groups[1].Value
      $envValue = [System.Environment]::GetEnvironmentVariable($name)
      if ([string]::IsNullOrEmpty($envValue)) { return "" }
      return $envValue
    }
  )

  $expanded = [System.Environment]::ExpandEnvironmentVariables($expanded)

  if ($expanded -eq "~") {
    return $HOME
  }

  if ($expanded.StartsWith("~/") -or $expanded.StartsWith('~\')) {
    return Join-Path $HOME $expanded.Substring(2)
  }

  return $expanded
}

function Get-PlatformProfileName {
  if ($IsWindows) { return "windows" }
  if ($IsMacOS) { return "darwin" }
  return "linux"
}

function Resolve-TargetSkillsPath {
  param(
    [Parameter(Mandatory = $true)][hashtable]$TargetConfig,
    [Parameter(Mandatory = $true)][string]$TargetName
  )

  if (-not $TargetConfig.ContainsKey("path_profiles")) {
    throw "Target '$TargetName' is missing path_profiles."
  }

  $profiles = ConvertTo-HashtableRecursive -Value $TargetConfig["path_profiles"]
  $platform = Get-PlatformProfileName

  if (-not $profiles.ContainsKey($platform)) {
    throw "Target '$TargetName' does not define path profile for '$platform'."
  }

  $profile = ConvertTo-HashtableRecursive -Value $profiles[$platform]
  if (-not $profile.ContainsKey("skills_dir")) {
    throw "Target '$TargetName' does not define skills_dir for '$platform'."
  }

  $path = [string]$profile["skills_dir"]

  if ($TargetConfig.ContainsKey("override_env")) {
    $overrideEnv = ConvertTo-HashtableRecursive -Value $TargetConfig["override_env"]
    if ($overrideEnv.ContainsKey("skills_dir")) {
      $envKey = [string]$overrideEnv["skills_dir"]
      $envValue = [System.Environment]::GetEnvironmentVariable($envKey)
      if (-not [string]::IsNullOrWhiteSpace($envValue)) {
        $path = $envValue
      }
    }
  }

  return Resolve-EnvExpressions -Value $path
}

function Get-LayerPatterns {
  param(
    [Parameter(Mandatory = $true)][hashtable]$Config,
    [Parameter(Mandatory = $true)][string]$TargetName,
    [Parameter(Mandatory = $true)][string]$LayerName
  )

  $skillSets = @{}
  if ($Config.ContainsKey("skill_sets")) {
    $skillSets = ConvertTo-HashtableRecursive -Value $Config["skill_sets"]
  }

  $lookupKey = $LayerName
  if ($LayerName -eq "target") {
    $lookupKey = $TargetName
  }

  if ($skillSets.ContainsKey($lookupKey)) {
    $arr = @($skillSets[$lookupKey])
    return @($arr | ForEach-Object { [string]$_ } | Where-Object { -not [string]::IsNullOrWhiteSpace($_) })
  }

  # Sensible defaults when skill_sets is omitted.
  if ($LayerName -eq "shared") {
    return @("skills/shared/*")
  }
  if ($LayerName -eq "target") {
    return @("skills/$TargetName/*")
  }

  return @()
}

function Resolve-SkillDirsFromPattern {
  param(
    [Parameter(Mandatory = $true)][string]$Pattern,
    [Parameter(Mandatory = $true)][string]$RepoRootPath
  )

  $expanded = Resolve-EnvExpressions -Value $Pattern
  if ([string]::IsNullOrWhiteSpace($expanded)) { return @() }

  if (-not [System.IO.Path]::IsPathRooted($expanded)) {
    $expanded = Join-Path $RepoRootPath $expanded
  }

  $hasWildcard = [System.Text.RegularExpressions.Regex]::IsMatch($expanded, '[\*\?\[]')
  if ($hasWildcard) {
    return @(Get-ChildItem -Path $expanded -Directory -ErrorAction SilentlyContinue)
  }

  if (-not (Test-Path $expanded)) {
    return @()
  }

  $item = Get-Item -LiteralPath $expanded -ErrorAction Stop
  if ($item.PSIsContainer) {
    return @($item)
  }

  return @()
}

function Ensure-Directory {
  param(
    [Parameter(Mandatory = $true)][string]$Path,
    [Parameter(Mandatory = $true)][bool]$IsDryRun
  )

  if (Test-Path $Path) { return }

  if ($IsDryRun) {
    Write-Host "[dry-run] create directory $Path"
    return
  }

  New-Item -Path $Path -ItemType Directory -Force | Out-Null
}

function Get-FileHashSafe {
  param([Parameter(Mandatory = $true)][string]$Path)

  if (-not (Test-Path $Path)) { return "" }
  return (Get-FileHash -Path $Path -Algorithm SHA256).Hash
}

function Sync-DirectoryOverlay {
  param(
    [Parameter(Mandatory = $true)][string]$SourceDir,
    [Parameter(Mandatory = $true)][string]$DestinationDir,
    [Parameter(Mandatory = $true)][bool]$IsDryRun,
    [Parameter(Mandatory = $true)][string]$LogPrefix
  )

  Ensure-Directory -Path $DestinationDir -IsDryRun $IsDryRun

  $sourceRoot = (Resolve-Path $SourceDir).Path

  foreach ($srcSubDir in Get-ChildItem -Path $sourceRoot -Directory -Recurse -ErrorAction SilentlyContinue) {
    $rel = [System.IO.Path]::GetRelativePath($sourceRoot, $srcSubDir.FullName)
    $dstSubDir = Join-Path $DestinationDir $rel
    Ensure-Directory -Path $dstSubDir -IsDryRun $IsDryRun
  }

  foreach ($srcFile in Get-ChildItem -Path $sourceRoot -File -Recurse -ErrorAction SilentlyContinue) {
    $relFile = [System.IO.Path]::GetRelativePath($sourceRoot, $srcFile.FullName)
    $dstFile = Join-Path $DestinationDir $relFile
    $dstParent = Split-Path -Path $dstFile -Parent
    Ensure-Directory -Path $dstParent -IsDryRun $IsDryRun

    if ((Test-Path $dstFile) -and (Test-Path $dstFile -PathType Container)) {
      if ($IsDryRun) {
        Write-Host "[dry-run] $LogPrefix remove conflicting directory $dstFile"
      }
      else {
        Remove-Item -Path $dstFile -Recurse -Force
      }
    }

    $copyNeeded = $true
    if (Test-Path $dstFile -PathType Leaf) {
      $srcHash = Get-FileHashSafe -Path $srcFile.FullName
      $dstHash = Get-FileHashSafe -Path $dstFile
      if ($srcHash -eq $dstHash) {
        $copyNeeded = $false
      }
    }

    if ($copyNeeded) {
      if ($IsDryRun) {
        Write-Host "[dry-run] $LogPrefix copy $relFile"
      }
      else {
        Copy-Item -Path $srcFile.FullName -Destination $dstFile -Force
        Write-Host "[ok] $LogPrefix copy $relFile"
      }
    }
  }
}

function Write-ManagedMarker {
  param(
    [Parameter(Mandatory = $true)][string]$SkillDir,
    [Parameter(Mandatory = $true)][string]$TargetName,
    [Parameter(Mandatory = $true)][string]$LayerName,
    [Parameter(Mandatory = $true)][string]$SourcePath,
    [Parameter(Mandatory = $true)][bool]$IsDryRun
  )

  $markerPath = Join-Path $SkillDir ".ai-config-managed.json"
  $markerObj = [ordered]@{
    managedBy   = "ai-config/scripts/sync/sync-skills.ps1"
    target      = $TargetName
    layer       = $LayerName
    source      = $SourcePath
    syncedAtUtc = (Get-Date).ToUniversalTime().ToString("o")
  }

  $next = ($markerObj | ConvertTo-Json -Depth 8)
  $current = ""
  if (Test-Path $markerPath -PathType Leaf) {
    $current = Get-Content -Path $markerPath -Raw
  }

  if ($current -eq $next) {
    return
  }

  if ($IsDryRun) {
    Write-Host "[dry-run] update marker $markerPath"
    return
  }

  Set-Content -Path $markerPath -Value $next -Encoding utf8NoBOM
}

function Backup-DirectoryContents {
  param(
    [Parameter(Mandatory = $true)][string]$Path,
    [Parameter(Mandatory = $true)][bool]$IsDryRun,
    [Parameter(Mandatory = $true)][bool]$CreateBackup
  )

  if (-not $CreateBackup) { return }
  if (-not (Test-Path $Path)) { return }

  $children = @(Get-ChildItem -Path $Path -Force -ErrorAction SilentlyContinue)
  if ($children.Count -eq 0) { return }

  $stamp = Get-Date -Format "yyyyMMdd-HHmmss"
  $backupPath = "$Path.bak.$stamp"

  if ($IsDryRun) {
    Write-Host "[dry-run] backup $Path -> $backupPath"
    return
  }

  New-Item -Path $backupPath -ItemType Directory -Force | Out-Null
  foreach ($item in $children) {
    Copy-Item -Path $item.FullName -Destination $backupPath -Recurse -Force
  }
  Write-Host "[ok] backup created: $backupPath"
}

$config = Load-MasterConfig -Path $ConfigPath
if (-not $config.ContainsKey("targets")) {
  throw "Master config must include top-level 'targets'."
}

$targetsMap = ConvertTo-HashtableRecursive -Value $config["targets"]
$availableTargets = @($targetsMap.Keys)

if ($Targets -and $Targets.Count -gt 0) {
  $effectiveTargets = @($Targets | ForEach-Object { $_.Trim() } | Where-Object { $_ } | Select-Object -Unique)
}
else {
  $effectiveTargets = @()
  foreach ($targetName in $availableTargets) {
    $targetCfg = ConvertTo-HashtableRecursive -Value $targetsMap[$targetName]
    if ($targetCfg.ContainsKey("enabled") -and [bool]$targetCfg["enabled"]) {
      $effectiveTargets += $targetName
    }
  }
}

if (-not $effectiveTargets -or $effectiveTargets.Count -eq 0) {
  Write-Host "No enabled targets selected. Nothing to do."
  exit 0
}

$defaults = @{}
if ($config.ContainsKey("defaults")) {
  $defaults = ConvertTo-HashtableRecursive -Value $config["defaults"]
}

$backupEnabled = $true
if ($defaults.ContainsKey("backup")) {
  $backupEnabled = [bool]$defaults["backup"]
}
$createBackup = $backupEnabled -and (-not $NoBackup)

$defaultDryRun = $false
if ($defaults.ContainsKey("dry_run")) {
  $defaultDryRun = [bool]$defaults["dry_run"]
}
$isDryRun = $defaultDryRun -or $DryRun

foreach ($targetName in $effectiveTargets) {
  if (-not $targetsMap.ContainsKey($targetName)) {
    $supported = ($availableTargets | Sort-Object) -join ", "
    throw "Unknown target '$targetName'. Supported targets: $supported"
  }

  $targetCfg = ConvertTo-HashtableRecursive -Value $targetsMap[$targetName]
  if ($targetCfg.ContainsKey("enabled") -and (-not [bool]$targetCfg["enabled"])) {
    Write-Host "[skip] target '$targetName' is disabled."
    continue
  }

  $targetSkillsDir = Resolve-TargetSkillsPath -TargetConfig $targetCfg -TargetName $targetName
  Ensure-Directory -Path $targetSkillsDir -IsDryRun $isDryRun

  $skillsMode = "overlay"
  $skillLayers = @("shared", "target")
  if ($targetCfg.ContainsKey("sync")) {
    $syncCfg = ConvertTo-HashtableRecursive -Value $targetCfg["sync"]
    if ($syncCfg.ContainsKey("skills_mode") -and -not [string]::IsNullOrWhiteSpace([string]$syncCfg["skills_mode"])) {
      $skillsMode = [string]$syncCfg["skills_mode"]
    }
    if ($syncCfg.ContainsKey("skill_layers")) {
      $skillLayers = @($syncCfg["skill_layers"] | ForEach-Object { [string]$_ } | Where-Object { -not [string]::IsNullOrWhiteSpace($_) })
    }
  }

  if ($skillLayers.Count -eq 0) {
    Write-Warning "[$targetName] skill_layers is empty. Skipping."
    continue
  }

  if ($skillsMode -eq "replace") {
    Backup-DirectoryContents -Path $targetSkillsDir -IsDryRun $isDryRun -CreateBackup $createBackup

    $existingChildren = @(Get-ChildItem -Path $targetSkillsDir -Force -ErrorAction SilentlyContinue)
    foreach ($child in $existingChildren) {
      if ($PSCmdlet.ShouldProcess($child.FullName, "Remove existing item for replace mode")) {
        if ($isDryRun) {
          Write-Host "[dry-run] [$targetName] remove $($child.Name)"
        }
        else {
          Remove-Item -Path $child.FullName -Recurse -Force
          Write-Host "[ok] [$targetName] removed $($child.Name)"
        }
      }
    }
  }

  foreach ($layerName in $skillLayers) {
    $patterns = @(Get-LayerPatterns -Config $config -TargetName $targetName -LayerName $layerName)
    if ($patterns.Count -eq 0) {
      Write-Host "[info] [$targetName][$layerName] no patterns."
      continue
    }

    foreach ($pattern in $patterns) {
      $sourceDirs = @(Resolve-SkillDirsFromPattern -Pattern $pattern -RepoRootPath $RepoRoot)
      if ($sourceDirs.Count -eq 0) {
        Write-Host "[info] [$targetName][$layerName] no skill dirs matched: $pattern"
        continue
      }

      foreach ($sourceDir in @($sourceDirs | Sort-Object Name)) {
        $skillName = $sourceDir.Name
        $destSkillDir = Join-Path $targetSkillsDir $skillName
        $logPrefix = "[$targetName][$layerName][$skillName]"

        if ($PSCmdlet.ShouldProcess($destSkillDir, "Sync skills directory")) {
          Sync-DirectoryOverlay -SourceDir $sourceDir.FullName -DestinationDir $destSkillDir -IsDryRun $isDryRun -LogPrefix $logPrefix
          Write-ManagedMarker -SkillDir $destSkillDir -TargetName $targetName -LayerName $layerName -SourcePath $sourceDir.FullName -IsDryRun $isDryRun
        }
      }
    }
  }
}

Write-Host "Skills sync completed."
