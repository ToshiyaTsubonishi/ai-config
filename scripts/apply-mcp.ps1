[CmdletBinding()]
param(
  [string]$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path,
  [string[]]$Targets = @("codex", "gemini", "antigravity"),
  [switch]$NoBackup,
  [switch]$StrictVariables
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

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

    if ((($value.StartsWith('"')) -and ($value.EndsWith('"'))) -or (($value.StartsWith("'")) -and ($value.EndsWith("'")))) {
      if ($value.Length -ge 2) {
        $value = $value.Substring(1, $value.Length - 2)
      }
    }

    if ($key) {
      $vars[$key] = $value
    }
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
    "\{\{([A-Z0-9_]+)\}\}",
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

  return [pscustomobject]@{
    Content = $expanded
    Missing = @($missing)
  }
}

function Apply-Template {
  param(
    [Parameter(Mandatory = $true)][string]$Name,
    [Parameter(Mandatory = $true)][string]$TemplatePath,
    [Parameter(Mandatory = $true)][string]$TargetPath,
    [Parameter(Mandatory = $true)][hashtable]$Variables,
    [Parameter(Mandatory = $true)][bool]$CreateBackup,
    [Parameter(Mandatory = $true)][bool]$Strict
  )

  if (-not (Test-Path $TemplatePath)) {
    throw "Template not found: $TemplatePath"
  }

  $raw = Get-Content -Path $TemplatePath -Raw
  $result = Expand-Template -Content $raw -Variables $Variables

  if ($result.Missing.Count -gt 0) {
    $missingList = ($result.Missing | Sort-Object -Unique) -join ", "
    if ($Strict) {
      throw "[$Name] Missing variables: $missingList"
    }
    Write-Warning "[$Name] Missing variables were set to empty: $missingList"
  }

  $targetDir = Split-Path -Path $TargetPath -Parent
  if (-not (Test-Path $targetDir)) {
    New-Item -ItemType Directory -Force -Path $targetDir | Out-Null
  }

  if ($CreateBackup -and (Test-Path $TargetPath)) {
    $stamp = Get-Date -Format "yyyyMMdd-HHmmss"
    Copy-Item -Path $TargetPath -Destination "$TargetPath.bak.$stamp"
  }

  Set-Content -Path $TargetPath -Value $result.Content -Encoding utf8NoBOM
  Write-Host "[ok] $Name -> $TargetPath"
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

if (-not $vars.ContainsKey("WEBFLOW_MCP_COMMAND") -or [string]::IsNullOrWhiteSpace([string]$vars["WEBFLOW_MCP_COMMAND"])) {
  $defaultWebflowCommand = "npx"

  if ($IsWindows) {
    $shortNpxCandidate = "C:\Progra~1\nodejs\npx.cmd"
    $longNpxCandidate = Join-Path $env:ProgramFiles "nodejs/npx.cmd"

    if (Test-Path $shortNpxCandidate) {
      $defaultWebflowCommand = $shortNpxCandidate
    } elseif (-not [string]::IsNullOrWhiteSpace($longNpxCandidate) -and (Test-Path $longNpxCandidate)) {
      $defaultWebflowCommand = $longNpxCandidate
    }
  }

  $vars["WEBFLOW_MCP_COMMAND"] = $defaultWebflowCommand
}

if ($vars.ContainsKey("WEBFLOW_MCP_COMMAND") -and -not [string]::IsNullOrWhiteSpace([string]$vars["WEBFLOW_MCP_COMMAND"])) {
  $normalizedWebflowCommand = [string]$vars["WEBFLOW_MCP_COMMAND"]
  if ($IsWindows) {
    $normalizedWebflowCommand = $normalizedWebflowCommand -replace "\\", "/"
  }
  $vars["WEBFLOW_MCP_COMMAND"] = $normalizedWebflowCommand
}

$map = @{
  codex = @{
    Template = (Join-Path $RepoRoot "mcp/codex.config.toml.tmpl")
    DefaultTarget = (Join-Path $HOME ".codex/config.toml")
    PathVar  = "CODEX_CONFIG_PATH"
  }
  gemini = @{
    Template = (Join-Path $RepoRoot "mcp/antigravity.mcp_config.json.tmpl")
    DefaultTarget = (Join-Path $HOME ".gemini/antigravity/mcp_config.json")
    PathVar  = "GEMINI_MCP_CONFIG_PATH"
  }
  antigravity = @{
    Template = (Join-Path $RepoRoot "mcp/antigravity.mcp_config.json.tmpl")
    DefaultTarget = (Join-Path $HOME ".antigravity/mcp_config.json")
    PathVar  = "ANTIGRAVITY_MCP_CONFIG_PATH"
  }
}

foreach ($target in $Targets) {
  if (-not $map.ContainsKey($target)) {
    $supported = ($map.Keys | Sort-Object) -join ", "
    throw "Unknown target: $target. Supported targets: $supported"
  }

  $item = $map[$target]
  $targetPath = Resolve-TargetPath -DefaultPath $item.DefaultTarget -PathVarName $item.PathVar -Variables $vars
  Apply-Template -Name $target -TemplatePath $item.Template -TargetPath $targetPath -Variables $vars -CreateBackup (-not $NoBackup) -Strict $StrictVariables
}

Write-Host "Done."
