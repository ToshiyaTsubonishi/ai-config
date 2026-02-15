[CmdletBinding()]
param(
  [string]$WorkspaceRoot = $HOME,
  [string]$AiConfigRepoUrl = "https://github.com/ToshiyaTsubonishi/ai-config-sync.git",
  [string]$AiAgentCollectionRepoUrl = "https://github.com/ToshiyaTsubonishi/ai-agent-collection.git",
  [string]$ModernGalleryRepoUrl = "https://github.com/ToshiyaTsubonishi/ModernGallery.git",
  [ValidateSet("core", "full")][string]$AiPlatformProfile = "core",
  [switch]$SkipFetch,
  [switch]$SkipEnvSetup,
  [switch]$SkipAiConfigSync,
  [switch]$SkipBuildRunTest,
  [switch]$ApplyAntigravityImport,
  [string]$AntigravityImportDir,
  [switch]$SkipAntigravitySettings,
  [switch]$SkipAntigravitySnippets,
  [switch]$SkipAntigravityExtensions,
  [switch]$SkipAntigravityGlobalStorage,
  [switch]$ApplyOpenWebUiExport,
  [string]$OpenWebUiExportDir,
  [string]$OpenWebUiUrl = "http://localhost:3001",
  [string]$OpenWebUiApiKey = "",
  [switch]$SkipOpenWebUiConfig,
  [switch]$SkipOpenWebUiModels,
  [switch]$SkipOpenWebUiToolServers,
  [switch]$NonInteractive,
  [switch]$DryRun
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Invoke-Program {
  param(
    [Parameter(Mandatory = $true)][string]$Program,
    [Parameter(Mandatory = $true)][string[]]$Arguments
  )

  if ($DryRun) {
    Write-Host "[dry-run] $Program $($Arguments -join ' ')"
    return
  }

  & $Program @Arguments
  if ($LASTEXITCODE -ne 0) {
    throw "Command failed: $Program $($Arguments -join ' ')"
  }
}

function Read-DotEnvValue {
  param(
    [Parameter(Mandatory = $true)][string]$Path,
    [Parameter(Mandatory = $true)][string]$Key,
    [Parameter(Mandatory = $true)][string]$DefaultValue
  )

  if (-not (Test-Path $Path)) {
    return $DefaultValue
  }

  $pattern = "^\s*" + [regex]::Escape($Key) + "\s*=\s*(.*)$"
  foreach ($line in Get-Content -Path $Path) {
    $match = [regex]::Match($line, $pattern)
    if ($match.Success) {
      $value = $match.Groups[1].Value.Trim()
      if (-not [string]::IsNullOrWhiteSpace($value)) {
        return $value
      }
    }
  }

  return $DefaultValue
}

function Test-Http {
  param(
    [Parameter(Mandatory = $true)][string]$Url,
    [Parameter(Mandatory = $true)][string]$Name
  )

  if ($DryRun) {
    Write-Host "[dry-run] HTTP check $Name -> $Url"
    return
  }

  try {
    $response = Invoke-WebRequest -Uri $Url -TimeoutSec 30
    if ($response.StatusCode -lt 200 -or $response.StatusCode -ge 400) {
      throw "Unexpected status code: $($response.StatusCode)"
    }
    Write-Host "[ok] $Name"
  } catch {
    throw "Health check failed for $Name ($Url): $($_.Exception.Message)"
  }
}

function Resolve-LatestOpenWebUiExportDir {
  param([string]$BaseDirectory)

  if (-not (Test-Path $BaseDirectory)) {
    return $null
  }

  $candidate = Get-ChildItem -Path $BaseDirectory -Directory -Filter "drive-download*" -ErrorAction SilentlyContinue |
    Sort-Object LastWriteTime -Descending |
    Select-Object -First 1

  if ($candidate) {
    return $candidate.FullName
  }

  return $null
}

function Resolve-DefaultAntigravityImportDir {
  param([Parameter(Mandatory = $true)][string]$AiConfigPath)

  $candidate = Join-Path $AiConfigPath "inventory/antigravity/latest"
  if (Test-Path $candidate) {
    return $candidate
  }

  return $null
}

$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$workspace = (Resolve-Path $WorkspaceRoot).Path

$aiConfigPath = Join-Path $workspace "ai-config"
$aiAgentCollectionPath = Join-Path $workspace "ai-agent-collection"
$modernGalleryPath = Join-Path $workspace "ModernGallery"

$fetchScript = Join-Path $repoRoot "scripts/fetch-repos.ps1"
$setupEnvScript = Join-Path $repoRoot "scripts/setup-env-interactive.ps1"

if (-not $SkipFetch) {
  Write-Host "[1/5] Fetch repositories"
  & $fetchScript `
    -WorkspaceRoot $workspace `
    -AiConfigRepoUrl $AiConfigRepoUrl `
    -AiAgentCollectionRepoUrl $AiAgentCollectionRepoUrl `
    -ModernGalleryRepoUrl $ModernGalleryRepoUrl `
    -DryRun:$DryRun
}

if (-not $SkipEnvSetup) {
  Write-Host "[2/5] Setup .env files (interactive)"
  & $setupEnvScript -WorkspaceRoot $workspace -NonInteractive:$NonInteractive -DryRun:$DryRun
}

if (-not $SkipAiConfigSync) {
  Write-Host "[3/5] Sync MCP and Skills"
  $syncAllScript = Join-Path $aiConfigPath "scripts/sync-all.ps1"
  if (-not (Test-Path $syncAllScript)) {
    throw "sync-all script not found: $syncAllScript"
  }

  if ($DryRun) {
    Write-Host "[dry-run] pwsh $syncAllScript -RepoRoot $aiConfigPath"
  } else {
    & $syncAllScript -RepoRoot $aiConfigPath
  }
}

if ($ApplyAntigravityImport) {
  Write-Host "[optional] Import Antigravity settings/extensions"

  if ([string]::IsNullOrWhiteSpace($AntigravityImportDir)) {
    $AntigravityImportDir = Resolve-DefaultAntigravityImportDir -AiConfigPath $aiConfigPath
    if (-not $AntigravityImportDir) {
      throw "Could not resolve Antigravity import directory. Specify -AntigravityImportDir explicitly."
    }
  }

  $importAntigravityScript = Join-Path $aiConfigPath "scripts/import-antigravity.ps1"
  if (-not (Test-Path $importAntigravityScript)) {
    throw "import-antigravity script not found: $importAntigravityScript"
  }

  & $importAntigravityScript `
    -InputDir $AntigravityImportDir `
    -SkipSettings:$SkipAntigravitySettings `
    -SkipSnippets:$SkipAntigravitySnippets `
    -SkipExtensions:$SkipAntigravityExtensions `
    -SkipGlobalStorage:$SkipAntigravityGlobalStorage `
    -DryRun:$DryRun
}

if (-not $SkipBuildRunTest) {
  if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    throw "docker command not found. Install Docker Desktop first."
  }

  Write-Host "[4/5] Build, run, and smoke-test services"

  $aiCompose = Join-Path $aiAgentCollectionPath "docker-infrastructure/stacks/ai-platform/compose.yaml"
  $aiEnv = Join-Path $aiAgentCollectionPath "docker-infrastructure/.env"
  if (-not (Test-Path $aiCompose)) {
    throw "Compose file not found: $aiCompose"
  }

  $aiProfiles = @()
  if ($AiPlatformProfile -eq "full") {
    $aiProfiles = @("--profile", "ai-full")
  } else {
    $aiProfiles = @("--profile", "open-webui")
  }

  $aiComposeArgs = @("compose", "--env-file", $aiEnv, "-f", $aiCompose) + $aiProfiles + @("up", "-d", "--build")
  Invoke-Program -Program "docker" -Arguments $aiComposeArgs

  $openWebUiPort = Read-DotEnvValue -Path $aiEnv -Key "PORT_OPEN_WEBUI" -DefaultValue "3001"
  $mcpRouterPort = Read-DotEnvValue -Path $aiEnv -Key "PORT_MCP_ROUTER" -DefaultValue "9001"

  Test-Http -Name "Open WebUI" -Url ("http://localhost:{0}/health" -f $openWebUiPort)
  Test-Http -Name "MCP Router" -Url ("http://localhost:{0}/health" -f $mcpRouterPort)

  $mgCompose = Join-Path $modernGalleryPath "docker-compose.yml"
  $mgEnv = Join-Path $modernGalleryPath ".env"
  if (-not (Test-Path $mgCompose)) {
    throw "Compose file not found: $mgCompose"
  }

  $mgComposeArgs = @("compose", "--env-file", $mgEnv, "-f", $mgCompose, "up", "-d", "--build")
  Invoke-Program -Program "docker" -Arguments $mgComposeArgs

  $mgWebPort = Read-DotEnvValue -Path $mgEnv -Key "PORT_MODERN_GALLERY_WEB" -DefaultValue "13100"
  $mgApiPort = Read-DotEnvValue -Path $mgEnv -Key "PORT_MODERN_GALLERY_API" -DefaultValue "18100"

  Test-Http -Name "ModernGallery API" -Url ("http://localhost:{0}/" -f $mgApiPort)
  Test-Http -Name "ModernGallery Web" -Url ("http://localhost:{0}/" -f $mgWebPort)
}

if ($ApplyOpenWebUiExport) {
  Write-Host "[5/5] Apply Open WebUI exports"

  if ([string]::IsNullOrWhiteSpace($OpenWebUiExportDir)) {
    $OpenWebUiExportDir = Resolve-LatestOpenWebUiExportDir -BaseDirectory (Join-Path $HOME "Downloads")
    if (-not $OpenWebUiExportDir) {
      throw "Could not resolve Open WebUI export directory. Specify -OpenWebUiExportDir explicitly."
    }
  }

  $syncOpenWebUiScript = Join-Path $aiConfigPath "scripts/sync-open-webui-export.ps1"
  if (-not (Test-Path $syncOpenWebUiScript)) {
    throw "sync-open-webui-export script not found: $syncOpenWebUiScript"
  }

  & $syncOpenWebUiScript `
    -ExportDir $OpenWebUiExportDir `
    -UseLatestFiles `
    -OpenWebUiUrl $OpenWebUiUrl `
    -OpenWebUiApiKey $OpenWebUiApiKey `
    -SkipConfig:$SkipOpenWebUiConfig `
    -SkipModels:$SkipOpenWebUiModels `
    -SkipToolServers:$SkipOpenWebUiToolServers `
    -DryRun:$DryRun
}

Write-Host "Restore workflow completed."
