[CmdletBinding()]
param(
  [string]$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path,
  [string]$WorkspaceRoot = "",
  [switch]$DryRun
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

    if (((($value.StartsWith('"')) -and ($value.EndsWith('"'))) -or (($value.StartsWith("'")) -and ($value.EndsWith("'")))) -and $value.Length -ge 2) {
      $value = $value.Substring(1, $value.Length - 2)
    }

    if ($key) {
      $vars[$key] = $value
    }
  }

  return $vars
}

function Normalize-TemplatePlaceholder {
  param([string]$Value)

  if ([string]::IsNullOrWhiteSpace($Value)) {
    return ""
  }

  $trimmed = $Value.Trim()
  if (
    $trimmed -match '^your_.*_here$' -or
    $trimmed -match '^<.*>$' -or
    $trimmed -match '^(changeme|replace_me)$'
  ) {
    return ""
  }

  return $trimmed
}

function Resolve-ConfiguredPath {
  param(
    [Parameter(Mandatory = $true)][string]$DefaultPath,
    [string]$PathVarName,
    [Parameter(Mandatory = $true)][hashtable]$Variables
  )

  if ($PathVarName -and $Variables.ContainsKey($PathVarName)) {
    $candidate = Normalize-TemplatePlaceholder -Value ([string]$Variables[$PathVarName]
    )
    if (-not [string]::IsNullOrWhiteSpace($candidate)) {
      return [System.Environment]::ExpandEnvironmentVariables($candidate)
    }
  }

  return [System.Environment]::ExpandEnvironmentVariables($DefaultPath)
}

function Ensure-EnvFile {
  param(
    [Parameter(Mandatory = $true)][string]$EnvPath,
    [Parameter(Mandatory = $true)][string]$TemplatePath
  )

  $dir = Split-Path -Path $EnvPath -Parent
  if (-not (Test-Path $dir)) {
    if ($DryRun) {
      Write-Host "[dry-run] mkdir $dir"
    } else {
      New-Item -ItemType Directory -Force -Path $dir | Out-Null
    }
  }

  if (Test-Path $EnvPath) {
    return
  }

  if (-not (Test-Path $TemplatePath)) {
    throw "Template not found: $TemplatePath"
  }

  if ($DryRun) {
    Write-Host "[dry-run] copy $TemplatePath -> $EnvPath"
  } else {
    Copy-Item -Path $TemplatePath -Destination $EnvPath
  }
}

function Set-EnvValue {
  param(
    [Parameter(Mandatory = $true)][string]$FilePath,
    [Parameter(Mandatory = $true)][string]$Key,
    [Parameter(Mandatory = $true)][AllowEmptyString()][string]$Value
  )

  $lines = @()
  if (Test-Path $FilePath) {
    $lines = Get-Content -Path $FilePath
  }

  $pattern = "^\s*" + [regex]::Escape($Key) + "\s*="
  $updated = $false

  for ($i = 0; $i -lt $lines.Count; $i++) {
    if ($lines[$i] -match $pattern) {
      $lines[$i] = "$Key=$Value"
      $updated = $true
      break
    }
  }

  if (-not $updated) {
    $lines += "$Key=$Value"
  }

  if ($DryRun) {
    Write-Host "[dry-run] set $Key in $FilePath"
  } else {
    Set-Content -Path $FilePath -Value $lines -Encoding utf8NoBOM
  }
}

$sourceEnvPath = Join-Path $RepoRoot ".env"
if (-not (Test-Path $sourceEnvPath)) {
  if ($DryRun) {
    Write-Warning "Source .env not found in dry-run mode: $sourceEnvPath"
    return
  }
  throw "Source .env not found: $sourceEnvPath"
}

$vars = Read-DotEnv -Path $sourceEnvPath
$workspace = ""

if (-not [string]::IsNullOrWhiteSpace($WorkspaceRoot)) {
  $workspace = (Resolve-Path $WorkspaceRoot).Path
} elseif ($vars.ContainsKey("WORKSPACE_ROOT") -and -not [string]::IsNullOrWhiteSpace((Normalize-TemplatePlaceholder -Value ([string]$vars["WORKSPACE_ROOT"])))) {
  $workspace = [System.Environment]::ExpandEnvironmentVariables((Normalize-TemplatePlaceholder -Value ([string]$vars["WORKSPACE_ROOT"])))
} else {
  $workspace = (Resolve-Path (Join-Path $RepoRoot "..")).Path
}

$workspaceDockerRoot = Join-Path $workspace "docker-infrastructure"
if (Test-Path $workspaceDockerRoot) {
  $defaultAgentEnvPath = Join-Path $workspaceDockerRoot ".env"
  $defaultAgentTemplatePath = Join-Path $workspaceDockerRoot ".env.template"
}
else {
  $defaultAgentEnvPath = Join-Path $workspace "ai-agent-collection/docker-infrastructure/.env"
  $defaultAgentTemplatePath = Join-Path $workspace "ai-agent-collection/docker-infrastructure/.env.template"
}

$agentEnvPath = Resolve-ConfiguredPath -DefaultPath $defaultAgentEnvPath -PathVarName "AI_AGENT_COLLECTION_ENV_PATH" -Variables $vars
$agentTemplatePath = Resolve-ConfiguredPath -DefaultPath $defaultAgentTemplatePath -PathVarName "AI_AGENT_COLLECTION_ENV_TEMPLATE_PATH" -Variables $vars

Ensure-EnvFile -EnvPath $agentEnvPath -TemplatePath $agentTemplatePath

$managedKeys = @(
  "GOOGLE_API_KEY",
  "HF_TOKEN",
  "COMPOSE_PROJECT_NAME",
  "PORT_OPEN_WEBUI",
  "PORT_WHISPER_UI",
  "PORT_YOMITOKU_GUI",
  "PORT_WHISPER_INFERENCE",
  "PORT_YOMITOKU_INFERENCE",
  "PORT_MCPO",
  "PORT_MCP_ROUTER",
  "PORT_INFERENCE_PROXY_MCP"
)

foreach ($key in $managedKeys) {
  if (-not $vars.ContainsKey($key)) { continue }
  $value = Normalize-TemplatePlaceholder -Value ([string]$vars[$key])
  if ([string]::IsNullOrWhiteSpace($value)) { continue }
  Set-EnvValue -FilePath $agentEnvPath -Key $key -Value $value
  Write-Host "[ok] synced $key -> $agentEnvPath"
}

Write-Host "Environment file sync completed."
