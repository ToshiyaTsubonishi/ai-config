[CmdletBinding()]
param(
  [string]$ExportDir,
  [string]$ConfigFile,
  [string]$ModelsFile,
  [string]$ToolServersFile,
  [string]$OpenWebUiUrl = "http://localhost:3001",
  [string]$OpenWebUiApiKey = "",
  [switch]$UseLatestFiles,
  [switch]$SkipConfig,
  [switch]$SkipModels,
  [switch]$SkipToolServers,
  [switch]$DryRun
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Get-LatestFile {
  param(
    [Parameter(Mandatory = $true)][string]$Directory,
    [Parameter(Mandatory = $true)][string[]]$Patterns
  )

  if (-not (Test-Path $Directory)) {
    return $null
  }

  $files = @()
  foreach ($pattern in $Patterns) {
    $files += Get-ChildItem -Path $Directory -Filter $pattern -File -ErrorAction SilentlyContinue
  }

  if ($files.Count -eq 0) {
    return $null
  }

  return ($files | Sort-Object LastWriteTime -Descending | Select-Object -First 1).FullName
}

function Get-FieldValue {
  param(
    [Parameter(Mandatory = $true)][object]$Object,
    [Parameter(Mandatory = $true)][string]$Name
  )

  if ($Object -is [hashtable]) {
    if ($Object.ContainsKey($Name)) {
      return $Object[$Name]
    }
    return $null
  }

  if ($Object -and $Object.PSObject.Properties[$Name]) {
    return $Object.$Name
  }

  return $null
}

function Normalize-ToolConnections {
  param([Parameter(Mandatory = $true)][object]$Raw)

  $connections = @()

  if ($Raw -is [hashtable]) {
    if ($Raw.ContainsKey("TOOL_SERVER_CONNECTIONS")) {
      $connections = @($Raw["TOOL_SERVER_CONNECTIONS"])
    } elseif ($Raw.ContainsKey("tool_servers")) {
      $connections = @($Raw["tool_servers"])
    } else {
      $connections = @($Raw)
    }
  } elseif ($Raw -is [System.Collections.IEnumerable] -and -not ($Raw -is [string])) {
    $connections = @($Raw)
  } else {
    $connections = @($Raw)
  }

  $normalized = @()
  $index = 0

  foreach ($connection in $connections) {
    $url = [string](Get-FieldValue -Object $connection -Name "url")
    if ([string]::IsNullOrWhiteSpace($url)) {
      continue
    }

    $path = Get-FieldValue -Object $connection -Name "path"
    if ($null -eq $path) { $path = "" }

    $type = Get-FieldValue -Object $connection -Name "type"
    if ([string]::IsNullOrWhiteSpace([string]$type)) { $type = "openapi" }

    $authType = Get-FieldValue -Object $connection -Name "auth_type"
    if ([string]::IsNullOrWhiteSpace([string]$authType)) { $authType = "none" }

    $key = Get-FieldValue -Object $connection -Name "key"
    if ($null -eq $key) { $key = "" }

    $config = Get-FieldValue -Object $connection -Name "config"
    if ($null -eq $config) { $config = @{} }

    $info = Get-FieldValue -Object $connection -Name "info"
    if ($null -eq $info) {
      $info = @{
        id = "tool-server-$index"
        name = "tool-server-$index"
        description = ""
      }
    } else {
      $infoId = Get-FieldValue -Object $info -Name "id"
      $infoName = Get-FieldValue -Object $info -Name "name"
      $infoDescription = Get-FieldValue -Object $info -Name "description"

      if ([string]::IsNullOrWhiteSpace([string]$infoId)) { $infoId = "tool-server-$index" }
      if ([string]::IsNullOrWhiteSpace([string]$infoName)) { $infoName = $infoId }
      if ($null -eq $infoDescription) { $infoDescription = "" }

      $info = @{
        id = [string]$infoId
        name = [string]$infoName
        description = [string]$infoDescription
      }
    }

    $item = [ordered]@{
      url = $url
      path = [string]$path
      type = [string]$type
      auth_type = [string]$authType
      key = [string]$key
      config = $config
      info = $info
    }

    $headers = Get-FieldValue -Object $connection -Name "headers"
    if ($null -ne $headers) {
      $item["headers"] = $headers
    }

    $normalized += $item
    $index++
  }

  return $normalized
}

function Invoke-OpenWebUiApi {
  param(
    [Parameter(Mandatory = $true)][ValidateSet("GET", "POST")][string]$Method,
    [Parameter(Mandatory = $true)][string]$Path,
    [object]$Body,
    [hashtable]$Headers,
    [switch]$UseDryRun
  )

  $uri = ($OpenWebUiUrl.TrimEnd("/")) + $Path

  if ($UseDryRun) {
    if ($null -eq $Body) {
      Write-Host "[dry-run] $Method $uri"
    } else {
      $summary = "body: object"
      if ($Body -is [hashtable]) {
        if ($Body.ContainsKey("models")) {
          $summary = "body: models=" + @($Body["models"]).Count
        } elseif ($Body.ContainsKey("TOOL_SERVER_CONNECTIONS")) {
          $summary = "body: TOOL_SERVER_CONNECTIONS=" + @($Body["TOOL_SERVER_CONNECTIONS"]).Count
        } elseif ($Body.ContainsKey("config")) {
          $summary = "body: config import"
        }
      }
      Write-Host "[dry-run] $Method $uri $summary"
    }
    return $null
  }

  if ($null -eq $Body) {
    return Invoke-RestMethod -Method $Method -Uri $uri -Headers $Headers -TimeoutSec 60
  }

  $jsonBody = $Body | ConvertTo-Json -Depth 100
  return Invoke-RestMethod -Method $Method -Uri $uri -Headers $Headers -ContentType "application/json" -Body $jsonBody -TimeoutSec 120
}

if ($UseLatestFiles -and [string]::IsNullOrWhiteSpace($ExportDir)) {
  throw "UseLatestFiles requires ExportDir."
}

if ($UseLatestFiles) {
  if (-not $ConfigFile) {
    $ConfigFile = Get-LatestFile -Directory $ExportDir -Patterns @("config-*.json")
  }
  if (-not $ModelsFile) {
    $ModelsFile = Get-LatestFile -Directory $ExportDir -Patterns @("models-export-*.json")
  }
  if (-not $ToolServersFile) {
    $ToolServersFile = Get-LatestFile -Directory $ExportDir -Patterns @("tool-server-*.json", "tool-servers-*.json")
  }
}

$headers = @{}
if (-not [string]::IsNullOrWhiteSpace($OpenWebUiApiKey)) {
  $headers["Authorization"] = "Bearer $OpenWebUiApiKey"
}

try {
  Invoke-OpenWebUiApi -Method "GET" -Path "/health" -Headers $headers -UseDryRun:$DryRun | Out-Null
} catch {
  throw "Open WebUI health check failed at $OpenWebUiUrl"
}

if (-not $SkipConfig) {
  if ($ConfigFile -and (Test-Path $ConfigFile)) {
    Write-Host "[import] config: $ConfigFile"
    $config = Get-Content -Path $ConfigFile -Raw | ConvertFrom-Json -AsHashtable
    $payload = @{ config = $config }
    Invoke-OpenWebUiApi -Method "POST" -Path "/api/v1/configs/import" -Body $payload -Headers $headers -UseDryRun:$DryRun | Out-Null
  } else {
    Write-Warning "Config file not found. Skip config import."
  }
}

if (-not $SkipModels) {
  if ($ModelsFile -and (Test-Path $ModelsFile)) {
    Write-Host "[import] models: $ModelsFile"
    $rawModels = Get-Content -Path $ModelsFile -Raw | ConvertFrom-Json -AsHashtable

    $models = @()
    if ($rawModels -is [System.Collections.IEnumerable] -and -not ($rawModels -is [string]) -and -not ($rawModels -is [hashtable])) {
      $models = @($rawModels)
    } elseif ($rawModels -is [hashtable] -and $rawModels.ContainsKey("models")) {
      $models = @($rawModels["models"])
    } else {
      throw "Unsupported models file format: $ModelsFile"
    }

    $payload = @{ models = $models }
    Invoke-OpenWebUiApi -Method "POST" -Path "/api/v1/models/import" -Body $payload -Headers $headers -UseDryRun:$DryRun | Out-Null
  } else {
    Write-Warning "Models file not found. Skip models import."
  }
}

if (-not $SkipToolServers) {
  if ($ToolServersFile -and (Test-Path $ToolServersFile)) {
    Write-Host "[import] tool servers: $ToolServersFile"
    $rawTools = Get-Content -Path $ToolServersFile -Raw | ConvertFrom-Json -AsHashtable
    $normalizedTools = @(Normalize-ToolConnections -Raw $rawTools)

    if ($normalizedTools.Count -gt 0) {
      $payload = @{ TOOL_SERVER_CONNECTIONS = $normalizedTools }
      Invoke-OpenWebUiApi -Method "POST" -Path "/api/v1/configs/tool_servers" -Body $payload -Headers $headers -UseDryRun:$DryRun | Out-Null
    } else {
      Write-Warning "No valid tool server entries found in $ToolServersFile"
    }
  } else {
    Write-Warning "Tool server file not found. Skip tool server import."
  }
}

if (-not $DryRun) {
  try {
    $toolState = Invoke-OpenWebUiApi -Method "GET" -Path "/api/v1/configs/tool_servers" -Headers $headers
    $modelState = Invoke-OpenWebUiApi -Method "GET" -Path "/api/v1/models/export" -Headers $headers

    $toolCount = @($toolState.TOOL_SERVER_CONNECTIONS).Count
    $modelCount = @($modelState).Count

    Write-Host "[verify] TOOL_SERVER_CONNECTIONS: $toolCount"
    Write-Host "[verify] Models: $modelCount"
  } catch {
    Write-Warning "Verification request failed: $($_.Exception.Message)"
  }
}

Write-Host "Open WebUI export sync completed."
