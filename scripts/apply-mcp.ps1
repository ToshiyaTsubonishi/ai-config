[CmdletBinding()]
param(
  [string]$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path,
  [string[]]$Targets = @("codex", "antigravity"),
  [switch]$NoBackup
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
      if ($Variables.ContainsKey($name) -and -not [string]::IsNullOrWhiteSpace([string]$Variables[$name])) {
        return [string]$Variables[$name]
      }
      $missing.Add($name) | Out-Null
      return $m.Value
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
    [Parameter(Mandatory = $true)][bool]$CreateBackup
  )

  if (-not (Test-Path $TemplatePath)) {
    throw "Template not found: $TemplatePath"
  }

  $raw = Get-Content -Path $TemplatePath -Raw
  $result = Expand-Template -Content $raw -Variables $Variables

  if ($result.Missing.Count -gt 0) {
    $missingList = ($result.Missing | Sort-Object -Unique) -join ", "
    throw "[$Name] Missing variables: $missingList"
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

$dotenvPath = Join-Path $RepoRoot ".env"
$fromDotEnv = Read-DotEnv -Path $dotenvPath

$vars = @{}
foreach ($entry in $fromDotEnv.GetEnumerator()) {
  $vars[$entry.Key] = $entry.Value
}
foreach ($entry in Get-ChildItem Env:) {
  $vars[$entry.Name] = $entry.Value
}

$map = @{
  codex = @{
    Template = (Join-Path $RepoRoot "mcp/codex.config.toml.tmpl")
    Target   = (Join-Path $HOME ".codex/config.toml")
  }
  antigravity = @{
    Template = (Join-Path $RepoRoot "mcp/antigravity.mcp_config.json.tmpl")
    Target   = (Join-Path $HOME ".gemini/antigravity/mcp_config.json")
  }
}

foreach ($target in $Targets) {
  if (-not $map.ContainsKey($target)) {
    $supported = ($map.Keys | Sort-Object) -join ", "
    throw "Unknown target: $target. Supported targets: $supported"
  }

  $item = $map[$target]
  Apply-Template -Name $target -TemplatePath $item.Template -TargetPath $item.Target -Variables $vars -CreateBackup (-not $NoBackup)
}

Write-Host "Done."
