[CmdletBinding()]
param(
  [string]$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path,
  [string]$OutputDir = (Join-Path (Resolve-Path (Join-Path $PSScriptRoot "..")).Path "inventory")
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

function Resolve-ConfiguredPath {
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

function Get-SkillInventory {
  param([Parameter(Mandatory = $true)][string]$RootPath)

  if (-not (Test-Path $RootPath)) {
    return [pscustomobject]@{
      rootPath = $RootPath
      count = 0
      skills = @()
    }
  }

  $skillDirs = @(Get-ChildItem -Path $RootPath -Filter "SKILL.md" -File -Recurse |
    ForEach-Object {
      $dir = $_.Directory.FullName
      $relative = $dir.Substring($RootPath.Length).TrimStart([char[]]@('\', '/'))
      if ([string]::IsNullOrWhiteSpace($relative)) {
        $relative = "."
      }
      ($relative -replace '\\', '/')
    } |
    Sort-Object -Unique)

  return [pscustomobject]@{
    rootPath = $RootPath
    count = $skillDirs.Count
    skills = @($skillDirs)
  }
}

function Get-CodexMcpInventory {
  param([Parameter(Mandatory = $true)][string]$Path)

  if (-not (Test-Path $Path)) {
    return [pscustomobject]@{
      configPath = $Path
      count = 0
      servers = @()
    }
  }

  $content = Get-Content -Path $Path -Raw
  $sections = [System.Text.RegularExpressions.Regex]::Matches(
    $content,
    "(?ms)^\[mcp_servers\.([^\]]+)\]\s*(.*?)(?=^\[mcp_servers\.|\z)"
  )

  $servers = @()
  foreach ($section in $sections) {
    $name = $section.Groups[1].Value
    $body = $section.Groups[2].Value

    $envKeys = @()
    foreach ($line in ($body -split "`r?`n")) {
      $envLineMatch = [System.Text.RegularExpressions.Regex]::Match($line, "^\s*env\s*=\s*\{(.+)\}\s*$")
      if ($envLineMatch.Success) {
        $envKeys = [System.Text.RegularExpressions.Regex]::Matches($envLineMatch.Groups[1].Value, "([A-Z0-9_]+)\s*=") |
          ForEach-Object { $_.Groups[1].Value } |
          Sort-Object -Unique
        break
      }
    }

    $servers += [pscustomobject]@{
      name = $name
      hasCommand = ($body -match "(?m)^\s*command\s*=")
      hasUrl = ($body -match "(?m)^\s*url\s*=")
      envKeys = @($envKeys)
    }
  }

  return [pscustomobject]@{
    configPath = $Path
    count = $servers.Count
    servers = @($servers | Sort-Object name)
  }
}

function Get-JsonMcpInventory {
  param([Parameter(Mandatory = $true)][string]$Path)

  if (-not (Test-Path $Path)) {
    return [pscustomobject]@{
      configPath = $Path
      count = 0
      servers = @()
    }
  }

  $json = Get-Content -Path $Path -Raw | ConvertFrom-Json -AsHashtable
  $servers = @()

  if ($json.ContainsKey("mcpServers") -and $json["mcpServers"] -is [hashtable]) {
    foreach ($entry in $json["mcpServers"].GetEnumerator()) {
      $value = $entry.Value
      $envKeys = @()
      if ($value.ContainsKey("env") -and $value["env"] -is [hashtable]) {
        $envKeys = @($value["env"].Keys | Sort-Object)
      }

      $argsCount = 0
      if ($value.ContainsKey("args") -and $value["args"] -is [System.Collections.IEnumerable]) {
        $argsCount = @($value["args"]).Count
      }

      $servers += [pscustomobject]@{
        name = $entry.Key
        command = if ($value.ContainsKey("command")) { [string]$value["command"] } else { "" }
        argsCount = $argsCount
        envKeys = @($envKeys)
      }
    }
  }

  return [pscustomobject]@{
    configPath = $Path
    count = $servers.Count
    servers = @($servers | Sort-Object name)
  }
}

if (-not (Test-Path $OutputDir)) {
  New-Item -ItemType Directory -Force -Path $OutputDir | Out-Null
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

$codexSkillsPath = Resolve-ConfiguredPath -DefaultPath (Join-Path $HOME ".codex/skills") -PathVarName "CODEX_SKILLS_PATH" -Variables $vars
$geminiSkillsPath = Resolve-ConfiguredPath -DefaultPath (Join-Path $HOME ".gemini/skills") -PathVarName "GEMINI_SKILLS_PATH" -Variables $vars
$antigravitySkillsPath = Resolve-ConfiguredPath -DefaultPath (Join-Path $HOME ".gemini/antigravity/skills") -PathVarName "ANTIGRAVITY_SKILLS_PATH" -Variables $vars

$codexConfigPath = Resolve-ConfiguredPath -DefaultPath (Join-Path $HOME ".codex/config.toml") -PathVarName "CODEX_CONFIG_PATH" -Variables $vars
$geminiMcpPath = Resolve-ConfiguredPath -DefaultPath (Join-Path $HOME ".gemini/antigravity/mcp_config.json") -PathVarName "GEMINI_MCP_CONFIG_PATH" -Variables $vars
$antigravityMcpPath = Resolve-ConfiguredPath -DefaultPath (Join-Path $HOME ".antigravity/mcp_config.json") -PathVarName "ANTIGRAVITY_MCP_CONFIG_PATH" -Variables $vars

$skillsCodex = Get-SkillInventory -RootPath $codexSkillsPath
$skillsGemini = Get-SkillInventory -RootPath $geminiSkillsPath
$skillsAntigravity = Get-SkillInventory -RootPath $antigravitySkillsPath

$mcpCodex = Get-CodexMcpInventory -Path $codexConfigPath
$mcpGemini = Get-JsonMcpInventory -Path $geminiMcpPath
$mcpAntigravity = Get-JsonMcpInventory -Path $antigravityMcpPath

$summary = [pscustomobject]@{
  generatedAt = (Get-Date).ToString("o")
  skills = [pscustomobject]@{
    codex = $skillsCodex.count
    gemini = $skillsGemini.count
    antigravity = $skillsAntigravity.count
  }
  mcp = [pscustomobject]@{
    codex = $mcpCodex.count
    gemini = $mcpGemini.count
    antigravity = $mcpAntigravity.count
  }
}

$files = @{
  "skills.codex.json" = $skillsCodex
  "skills.gemini.json" = $skillsGemini
  "skills.antigravity.json" = $skillsAntigravity
  "mcp.codex.json" = $mcpCodex
  "mcp.gemini.json" = $mcpGemini
  "mcp.antigravity.json" = $mcpAntigravity
  "summary.json" = $summary
}

foreach ($entry in $files.GetEnumerator()) {
  $target = Join-Path $OutputDir $entry.Key
  $entry.Value | ConvertTo-Json -Depth 8 | Set-Content -Path $target -Encoding utf8NoBOM
  Write-Host "[ok] $target"
}

Write-Host "Done."
