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

  if ($null -eq $Value) {
    return $null
  }

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
    # JSON is valid YAML. This fallback avoids hard dependency on external YAML modules.
    $parsed = $raw | ConvertFrom-Json -AsHashtable -Depth 100
    return $parsed
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

  if ($null -eq $Value) {
    return $null
  }

  $expanded = [System.Text.RegularExpressions.Regex]::Replace(
    $Value,
    '\$\{([A-Za-z_][A-Za-z0-9_]*)\}',
    {
      param($m)
      $name = $m.Groups[1].Value
      $envValue = [System.Environment]::GetEnvironmentVariable($name)
      if ([string]::IsNullOrEmpty($envValue)) {
        Write-Verbose "Environment variable '$name' is not defined. Expanding to empty string."
        return ""
      }
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
  $isWindowsPlatform = $false
  if (Get-Variable -Name IsWindows -ErrorAction SilentlyContinue) {
    $isWindowsPlatform = [bool]$IsWindows
  }
  elseif ($env:OS -eq "Windows_NT") {
    $isWindowsPlatform = $true
  }

  if ($isWindowsPlatform) { return "windows" }

  $isMacPlatform = $false
  if (Get-Variable -Name IsMacOS -ErrorAction SilentlyContinue) {
    $isMacPlatform = [bool]$IsMacOS
  }

  if ($isMacPlatform) { return "darwin" }
  return "linux"
}

function Normalize-Text {
  param([AllowNull()][string]$Text)

  if ($null -eq $Text) {
    return ""
  }

  $normalized = $Text -replace "`r`n", "`n"
  $normalized = $normalized.TrimEnd("`n")
  return "$normalized`n"
}

function Write-ContentIfChanged {
  param(
    [Parameter(Mandatory = $true)][string]$Path,
    [Parameter(Mandatory = $true)][string]$Content,
    [Parameter(Mandatory = $true)][bool]$CreateBackup,
    [Parameter(Mandatory = $true)][bool]$IsDryRun,
    [Parameter(Mandatory = $true)][string]$Label
  )

  $targetDir = Split-Path -Path $Path -Parent
  if (-not (Test-Path $targetDir)) {
    if ($IsDryRun) {
      Write-Host "[dry-run] create directory $targetDir"
    }
    else {
      New-Item -Path $targetDir -ItemType Directory -Force | Out-Null
    }
  }

  $next = Normalize-Text -Text $Content
  $current = ""
  if (Test-Path $Path) {
    $current = Normalize-Text -Text (Get-Content -Path $Path -Raw)
  }

  if ($current -eq $next) {
    Write-Host "[skip] $Label is already up-to-date: $Path"
    return
  }

  if ($IsDryRun) {
    Write-Host "[dry-run] update $Label -> $Path"
    return
  }

  if ($CreateBackup -and (Test-Path $Path)) {
    $stamp = Get-Date -Format "yyyyMMdd-HHmmss"
    Copy-Item -Path $Path -Destination "$Path.bak.$stamp"
  }

  Set-Content -Path $Path -Value $next -Encoding utf8NoBOM
  Write-Host "[ok] $Label -> $Path"
}

function Resolve-TargetRootDir {
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
  if (-not $profile.ContainsKey("root_dir")) {
    throw "Target '$TargetName' does not define root_dir for '$platform'."
  }

  return Resolve-EnvExpressions -Value ([string]$profile["root_dir"])
}

function Resolve-TemplatePath {
  param(
    [Parameter(Mandatory = $true)][string]$TemplatePathRaw,
    [Parameter(Mandatory = $true)][string]$RepoRootPath,
    [Parameter(Mandatory = $true)][string]$TargetName
  )

  $templatePath = Resolve-EnvExpressions -Value $TemplatePathRaw
  if (-not [System.IO.Path]::IsPathRooted($templatePath)) {
    $templatePath = Join-Path $RepoRootPath $templatePath
  }

  if (-not (Test-Path $templatePath)) {
    throw "Template file not found for target '$TargetName': $templatePath"
  }

  return $templatePath
}

$targetFileSpecs = @{
  "codex"       = @(
    @{
      label        = "AGENTS.md"
      template     = "config/targets/codex/AGENTS.md.tmpl"
      file_name    = "AGENTS.md"
      override_env = "CODEX_AGENTS_PATH"
    },
    @{
      label        = "AGENTS_RULES.md"
      template     = "config/targets/codex/AGENTS_RULES.md.tmpl"
      file_name    = "AGENTS_RULES.md"
      override_env = "CODEX_AGENTS_RULES_PATH"
    }
  )
  "gemini_cli"  = @(
    @{
      label        = "GEMINI.md"
      template     = "config/targets/gemini-cli/GEMINI.md.tmpl"
      file_name    = "GEMINI.md"
      override_env = "GEMINI_SYSTEM_PROMPT_PATH"
    },
    @{
      label        = "GEMINI_RULES.md"
      template     = "config/targets/gemini-cli/GEMINI_RULES.md.tmpl"
      file_name    = "GEMINI_RULES.md"
      override_env = "GEMINI_RULES_PATH"
    }
  )
  "antigravity" = @(
    @{
      label        = "GEMINI.md"
      template     = "config/targets/antigravity/GEMINI.md.tmpl"
      file_name    = "GEMINI.md"
      override_env = "ANTIGRAVITY_SYSTEM_PROMPT_PATH"
    },
    @{
      label        = "GEMINI_RULES.md"
      template     = "config/targets/antigravity/GEMINI_RULES.md.tmpl"
      file_name    = "GEMINI_RULES.md"
      override_env = "ANTIGRAVITY_RULES_PATH"
    }
  )
}

$config = Load-MasterConfig -Path $ConfigPath

if (-not $config.ContainsKey("targets")) {
  throw "Master config must include top-level 'targets'."
}

$allTargets = ConvertTo-HashtableRecursive -Value $config["targets"]
$availableTargets = @($allTargets.Keys)

if ($Targets -and $Targets.Count -gt 0) {
  $effectiveTargets = @($Targets | ForEach-Object { $_.Trim() } | Where-Object { $_ } | Select-Object -Unique)
}
else {
  $effectiveTargets = @()
  foreach ($targetName in $availableTargets) {
    $targetCfg = ConvertTo-HashtableRecursive -Value $allTargets[$targetName]
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
  if (-not $allTargets.ContainsKey($targetName)) {
    $supported = ($availableTargets | Sort-Object) -join ", "
    throw "Unknown target '$targetName'. Supported targets: $supported"
  }

  if (-not $targetFileSpecs.ContainsKey($targetName)) {
    Write-Host "[skip] target '$targetName' has no Gemini context templates."
    continue
  }

  $targetCfg = ConvertTo-HashtableRecursive -Value $allTargets[$targetName]
  if ($targetCfg.ContainsKey("enabled") -and (-not [bool]$targetCfg["enabled"])) {
    Write-Host "[skip] target '$targetName' is disabled."
    continue
  }

  $rootDir = Resolve-TargetRootDir -TargetConfig $targetCfg -TargetName $targetName
  foreach ($spec in $targetFileSpecs[$targetName]) {
    $templatePath = Resolve-TemplatePath -TemplatePathRaw ([string]$spec.template) -RepoRootPath $RepoRoot -TargetName $targetName
    $targetPath = Join-Path $rootDir ([string]$spec.file_name)

    $envVarName = [string]$spec.override_env
    if (-not [string]::IsNullOrWhiteSpace($envVarName)) {
      $overrideValue = [System.Environment]::GetEnvironmentVariable($envVarName)
      if (-not [string]::IsNullOrWhiteSpace($overrideValue)) {
        $targetPath = $overrideValue
      }
    }
    $targetPath = Resolve-EnvExpressions -Value $targetPath

    $templateRaw = Get-Content -Path $templatePath -Raw

    if ($PSCmdlet.ShouldProcess($targetPath, "Sync $([string]$spec.label) for '$targetName'")) {
      Write-ContentIfChanged -Path $targetPath -Content $templateRaw -CreateBackup $createBackup -IsDryRun $isDryRun -Label "$targetName/$([string]$spec.label)"
    }
  }
}

Write-Host "Agent context sync completed."
