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
  if ($IsWindows) { return "windows" }
  if ($IsMacOS) { return "darwin" }
  return "linux"
}

function Build-TemplateVariables {
  $vars = @{}
  foreach ($entry in Get-ChildItem Env:) {
    $vars[$entry.Name] = $entry.Value
  }

  if (-not $vars.ContainsKey("MCP_LOCAL_TIMEZONE") -or [string]::IsNullOrWhiteSpace([string]$vars["MCP_LOCAL_TIMEZONE"])) {
    $vars["MCP_LOCAL_TIMEZONE"] = [System.TimeZoneInfo]::Local.Id
  }

  if (-not $vars.ContainsKey("PORT_INFERENCE_PROXY_MCP") -or [string]::IsNullOrWhiteSpace([string]$vars["PORT_INFERENCE_PROXY_MCP"])) {
    $vars["PORT_INFERENCE_PROXY_MCP"] = "9030"
  }

  $defaultWebflowMcpCommand = "npx"
  $defaultWebflowMcpArgs = '["-y", "mcp-remote", "https://mcp.webflow.com/mcp"]'

  if ($IsWindows) {
    $defaultWebflowMcpCommand = "C:/Windows/System32/cmd.exe"
    $defaultWebflowMcpArgs = '["/d", "/c", "set PATH=C:/Progra~1/nodejs;%PATH% ^&^& C:/Progra~1/nodejs/npx.cmd -y mcp-remote https://mcp.webflow.com/mcp"]'
  }

  if (-not $vars.ContainsKey("WEBFLOW_MCP_COMMAND") -or [string]::IsNullOrWhiteSpace([string]$vars["WEBFLOW_MCP_COMMAND"])) {
    $vars["WEBFLOW_MCP_COMMAND"] = $defaultWebflowMcpCommand
  }

  if (-not $vars.ContainsKey("WEBFLOW_MCP_ARGS") -or [string]::IsNullOrWhiteSpace([string]$vars["WEBFLOW_MCP_ARGS"])) {
    $vars["WEBFLOW_MCP_ARGS"] = $defaultWebflowMcpArgs
  }

  if ($IsWindows -and $vars.ContainsKey("WEBFLOW_MCP_COMMAND")) {
    $vars["WEBFLOW_MCP_COMMAND"] = ([string]$vars["WEBFLOW_MCP_COMMAND"]) -replace "\\", "/"
  }

  return $vars
}

function Expand-Template {
  param(
    [Parameter(Mandatory = $true)][string]$Content,
    [Parameter(Mandatory = $true)][hashtable]$Variables
  )

  $missing = [System.Collections.Generic.HashSet[string]]::new()

  $expanded = [System.Text.RegularExpressions.Regex]::Replace(
    $Content,
    '\{\{([A-Za-z0-9_]+)\}\}',
    {
      param($m)
      $name = $m.Groups[1].Value
      if ($Variables.ContainsKey($name)) {
        return [string]$Variables[$name]
      }
      $missing.Add($name) | Out-Null
      return ""
    }
  )

  [pscustomobject]@{
    Content = $expanded
    Missing = @($missing)
  }
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

function Resolve-TemplatePath {
  param(
    [Parameter(Mandatory = $true)][hashtable]$TargetConfig,
    [Parameter(Mandatory = $true)][string]$RepoRootPath,
    [Parameter(Mandatory = $true)][string]$TargetName
  )

  if (-not $TargetConfig.ContainsKey("templates")) {
    throw "Target '$TargetName' is missing 'templates'."
  }

  $templates = ConvertTo-HashtableRecursive -Value $TargetConfig["templates"]
  $templatePath = $null

  if ($templates.ContainsKey("mcp_template")) {
    $templatePath = [string]$templates["mcp_template"]
  }
  elseif ($templates.ContainsKey("config_template")) {
    $templatePath = [string]$templates["config_template"]
  }

  if ([string]::IsNullOrWhiteSpace($templatePath)) {
    throw "Target '$TargetName' does not define templates.mcp_template or templates.config_template."
  }

  $templatePath = Resolve-EnvExpressions -Value $templatePath

  if (-not [System.IO.Path]::IsPathRooted($templatePath)) {
    $templatePath = Join-Path $RepoRootPath $templatePath
  }

  if (-not (Test-Path $templatePath)) {
    throw "Template file not found for target '$TargetName': $templatePath"
  }

  return $templatePath
}

function Resolve-TargetMcpPath {
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
  $path = $null

  if ($profile.ContainsKey("mcp_file")) {
    $path = [string]$profile["mcp_file"]
  }
  elseif ($profile.ContainsKey("config_file")) {
    # Gemini CLI stores MCP settings in settings.json.
    $path = [string]$profile["config_file"]
  }

  if ([string]::IsNullOrWhiteSpace($path)) {
    throw "Target '$TargetName' does not define mcp_file/config_file for '$platform'."
  }

  if ($TargetConfig.ContainsKey("override_env")) {
    $overrideEnv = ConvertTo-HashtableRecursive -Value $TargetConfig["override_env"]
    if ($overrideEnv.ContainsKey("mcp_file")) {
      $mcpEnvVarName = [string]$overrideEnv["mcp_file"]
      $mcpEnvValue = [System.Environment]::GetEnvironmentVariable($mcpEnvVarName)
      if (-not [string]::IsNullOrWhiteSpace($mcpEnvValue)) {
        $path = $mcpEnvValue
      }
    }
  }

  return Resolve-EnvExpressions -Value $path
}

function Merge-McpJsonContent {
  param(
    [Parameter(Mandatory = $true)][string]$TemplateContent,
    [Parameter(Mandatory = $true)][string]$TargetPath
  )

  $templateObj = ConvertTo-HashtableRecursive -Value ($TemplateContent | ConvertFrom-Json -AsHashtable -Depth 100)

  if ($templateObj.ContainsKey("mcpServers")) {
    $templateMcpServers = $templateObj["mcpServers"]
  }
  elseif ($templateObj.ContainsKey("mcp_servers")) {
    $templateMcpServers = $templateObj["mcp_servers"]
  }
  else {
    throw "JSON merge mode requires 'mcpServers' or 'mcp_servers' in template."
  }

  $targetObj = @{}
  if (Test-Path $TargetPath) {
    $existingRaw = Get-Content -Path $TargetPath -Raw
    if (-not [string]::IsNullOrWhiteSpace($existingRaw)) {
      $targetObj = ConvertTo-HashtableRecursive -Value ($existingRaw | ConvertFrom-Json -AsHashtable -Depth 100)
    }
  }

  $targetObj["mcpServers"] = $templateMcpServers
  return ($targetObj | ConvertTo-Json -Depth 100)
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

$vars = Build-TemplateVariables

foreach ($targetName in $effectiveTargets) {
  if (-not $allTargets.ContainsKey($targetName)) {
    $supported = ($availableTargets | Sort-Object) -join ", "
    throw "Unknown target '$targetName'. Supported targets: $supported"
  }

  $targetCfg = ConvertTo-HashtableRecursive -Value $allTargets[$targetName]
  if ($targetCfg.ContainsKey("enabled") -and (-not [bool]$targetCfg["enabled"])) {
    Write-Host "[skip] target '$targetName' is disabled."
    continue
  }

  $templatePath = Resolve-TemplatePath -TargetConfig $targetCfg -RepoRootPath $RepoRoot -TargetName $targetName
  $targetPath = Resolve-TargetMcpPath -TargetConfig $targetCfg -TargetName $targetName

  $templateRaw = Get-Content -Path $templatePath -Raw
  $rendered = Expand-Template -Content $templateRaw -Variables $vars

  if ($rendered.Missing.Count -gt 0) {
    $missingCsv = ($rendered.Missing | Sort-Object -Unique) -join ", "
    Write-Warning "[$targetName] Missing template variables were expanded to empty string: $missingCsv"
  }

  $mcpMode = "replace"
  if ($targetCfg.ContainsKey("sync")) {
    $syncCfg = ConvertTo-HashtableRecursive -Value $targetCfg["sync"]
    if ($syncCfg.ContainsKey("mcp_mode") -and -not [string]::IsNullOrWhiteSpace([string]$syncCfg["mcp_mode"])) {
      $mcpMode = [string]$syncCfg["mcp_mode"]
    }
  }

  $nextContent = $rendered.Content
  if ($mcpMode -eq "merge") {
    $trim = $nextContent.TrimStart()
    if ($trim.StartsWith("{") -or $trim.StartsWith("[")) {
      $nextContent = Merge-McpJsonContent -TemplateContent $nextContent -TargetPath $targetPath
    }
    else {
      Write-Warning "[$targetName] mcp_mode=merge is only supported for JSON templates. Falling back to replace."
    }
  }

  if ($PSCmdlet.ShouldProcess($targetPath, "Sync MCP config for '$targetName'")) {
    Write-ContentIfChanged -Path $targetPath -Content $nextContent -CreateBackup $createBackup -IsDryRun $isDryRun -Label $targetName
  }
}

Write-Host "MCP sync completed."
