[CmdletBinding()]
param(
  [string]$WorkspaceRoot = $HOME,
  [switch]$NonInteractive,
  [switch]$DryRun
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Ensure-EnvFile {
  param(
    [Parameter(Mandatory = $true)][string]$EnvPath,
    [Parameter(Mandatory = $true)][string]$TemplatePath
  )

  if (Test-Path $EnvPath) {
    return
  }

  $dir = Split-Path -Path $EnvPath -Parent
  if (-not (Test-Path $dir)) {
    if ($DryRun) {
      Write-Host "[dry-run] mkdir $dir"
    } else {
      New-Item -ItemType Directory -Force -Path $dir | Out-Null
    }
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

function Get-EnvValue {
  param(
    [Parameter(Mandatory = $true)][string]$FilePath,
    [Parameter(Mandatory = $true)][string]$Key
  )

  if (-not (Test-Path $FilePath)) {
    return ""
  }

  $pattern = "^\s*" + [regex]::Escape($Key) + "\s*=\s*(.*)$"
  foreach ($line in Get-Content -Path $FilePath) {
    $match = [regex]::Match($line, $pattern)
    if ($match.Success) {
      return $match.Groups[1].Value.Trim()
    }
  }

  return ""
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

function ConvertTo-PlainText {
  param([Parameter(Mandatory = $true)][Security.SecureString]$Secure)

  $bstr = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($Secure)
  try {
    return [Runtime.InteropServices.Marshal]::PtrToStringBSTR($bstr)
  } finally {
    [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($bstr)
  }
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

function Prompt-EnvValue {
  param(
    [Parameter(Mandatory = $true)][string]$Prompt,
    [string]$Current,
    [bool]$Required,
    [bool]$Secret,
    [switch]$UseNonInteractive
  )

  if ($UseNonInteractive) {
    return $Current
  }

  $currentIsSet = -not [string]::IsNullOrWhiteSpace($Current)

  while ($true) {
    $label = $Prompt
    if ($Required) {
      $label += " [required]"
    } else {
      $label += " [optional]"
    }

    if ($currentIsSet) {
      $label += " [Enter to keep current]"
    } elseif (-not $Required) {
      $label += " [Enter to skip]"
    }

    if ($Secret) {
      $secure = Read-Host -Prompt $label -AsSecureString
      $input = ConvertTo-PlainText -Secure $secure
    } else {
      $input = Read-Host -Prompt $label
    }

    if ([string]::IsNullOrWhiteSpace($input)) {
      if ($currentIsSet) {
        return $Current
      }
      if (-not $Required) {
        return ""
      }
      Write-Warning "This value is required."
      continue
    }

    return $input.Trim()
  }
}

function Apply-EnvSpec {
  param(
    [Parameter(Mandatory = $true)][pscustomobject]$Spec,
    [switch]$UseNonInteractive
  )

  if (-not (Test-Path $Spec.TemplatePath)) {
    if ([bool]$Spec.Optional) {
      Write-Host "[skip] $($Spec.Name): template not found ($($Spec.TemplatePath))"
      return
    }
    throw "Template not found: $($Spec.TemplatePath)"
  }

  Ensure-EnvFile -EnvPath $Spec.EnvPath -TemplatePath $Spec.TemplatePath
  Write-Host "[env] $($Spec.Name): $($Spec.EnvPath)"

  foreach ($var in $Spec.Variables) {
    $rawCurrent = Get-EnvValue -FilePath $Spec.EnvPath -Key $var.Key
    $current = Normalize-TemplatePlaceholder -Value $rawCurrent

    $next = Prompt-EnvValue `
      -Prompt $var.Prompt `
      -Current $current `
      -Required ([bool]$var.Required) `
      -Secret ([bool]$var.Secret) `
      -UseNonInteractive:$UseNonInteractive

    if ($UseNonInteractive -and $var.Required -and [string]::IsNullOrWhiteSpace($next) -and -not $DryRun) {
      Write-Warning "Required value is still empty in non-interactive mode: $($var.Key)"
    }

    Set-EnvValue -FilePath $Spec.EnvPath -Key $var.Key -Value $next
  }
}

$root = (Resolve-Path $WorkspaceRoot).Path

$specs = @(
  [pscustomobject]@{
    Name = "ai-config"
    Optional = $false
    EnvPath = (Join-Path $root "ai-config/.env")
    TemplatePath = (Join-Path $root "ai-config/.env.example")
    Variables = @(
      [pscustomobject]@{ Key = "GOOGLE_API_KEY"; Required = $true; Secret = $true; Prompt = "Google API key (shared)" },
      [pscustomobject]@{ Key = "HF_TOKEN"; Required = $false; Secret = $true; Prompt = "HuggingFace token (shared)" },
      [pscustomobject]@{ Key = "GITHUB_PERSONAL_ACCESS_TOKEN"; Required = $false; Secret = $true; Prompt = "GitHub PAT for github-mcp" },
      [pscustomobject]@{ Key = "CONTEXT7_API_KEY"; Required = $false; Secret = $true; Prompt = "Context7 API key" },
      [pscustomobject]@{ Key = "FIRECRAWL_API_KEY"; Required = $false; Secret = $true; Prompt = "Firecrawl API key" },
      [pscustomobject]@{ Key = "FIGMA_API_KEY"; Required = $false; Secret = $true; Prompt = "Figma API key" },
      [pscustomobject]@{ Key = "JINA_API_KEY"; Required = $false; Secret = $true; Prompt = "Jina API key" },
      [pscustomobject]@{ Key = "WORKSPACE_ROOT"; Required = $false; Secret = $false; Prompt = "Workspace root override (optional)" },
      [pscustomobject]@{ Key = "AI_AGENT_COLLECTION_ENV_PATH"; Required = $false; Secret = $false; Prompt = "ai-agent-collection .env path override (optional)" },
      [pscustomobject]@{ Key = "AI_AGENT_COLLECTION_ENV_TEMPLATE_PATH"; Required = $false; Secret = $false; Prompt = "ai-agent-collection .env template path override (optional)" },
      [pscustomobject]@{ Key = "COMPOSE_PROJECT_NAME"; Required = $false; Secret = $false; Prompt = "Compose project name (default: ai-workspace)" },
      [pscustomobject]@{ Key = "PORT_OPEN_WEBUI"; Required = $false; Secret = $false; Prompt = "Open WebUI port" },
      [pscustomobject]@{ Key = "PORT_WHISPER_UI"; Required = $false; Secret = $false; Prompt = "Whisper UI port" },
      [pscustomobject]@{ Key = "PORT_YOMITOKU_GUI"; Required = $false; Secret = $false; Prompt = "Yomitoku GUI port" },
      [pscustomobject]@{ Key = "PORT_WHISPER_INFERENCE"; Required = $false; Secret = $false; Prompt = "Whisper inference port" },
      [pscustomobject]@{ Key = "PORT_YOMITOKU_INFERENCE"; Required = $false; Secret = $false; Prompt = "Yomitoku inference port" },
      [pscustomobject]@{ Key = "PORT_MCPO"; Required = $false; Secret = $false; Prompt = "MCPO port" },
      [pscustomobject]@{ Key = "PORT_MCP_ROUTER"; Required = $false; Secret = $false; Prompt = "MCP Router port" },
      [pscustomobject]@{ Key = "PORT_INFERENCE_PROXY_MCP"; Required = $false; Secret = $false; Prompt = "Inference Proxy MCP port" },
      [pscustomobject]@{ Key = "CODEX_CONFIG_PATH"; Required = $false; Secret = $false; Prompt = "Codex MCP config path override (optional)" },
      [pscustomobject]@{ Key = "GEMINI_MCP_CONFIG_PATH"; Required = $false; Secret = $false; Prompt = "Gemini MCP config path override (optional)" },
      [pscustomobject]@{ Key = "ANTIGRAVITY_MCP_CONFIG_PATH"; Required = $false; Secret = $false; Prompt = "Antigravity MCP config path override (optional)" },
      [pscustomobject]@{ Key = "CODEX_SKILLS_PATH"; Required = $false; Secret = $false; Prompt = "Codex skills path override (optional)" },
      [pscustomobject]@{ Key = "GEMINI_SKILLS_PATH"; Required = $false; Secret = $false; Prompt = "Gemini skills path override (optional)" },
      [pscustomobject]@{ Key = "ANTIGRAVITY_SKILLS_PATH"; Required = $false; Secret = $false; Prompt = "Antigravity skills path override (optional)" }
    )
  },
  [pscustomobject]@{
    Name = "ModernGallery"
    Optional = $true
    EnvPath = (Join-Path $root "ModernGallery/.env")
    TemplatePath = (Join-Path $root "ModernGallery/.env.template")
    Variables = @(
      [pscustomobject]@{ Key = "PORT_MODERN_GALLERY_WEB"; Required = $true; Secret = $false; Prompt = "ModernGallery web port" },
      [pscustomobject]@{ Key = "PORT_MODERN_GALLERY_API"; Required = $true; Secret = $false; Prompt = "ModernGallery API port" },
      [pscustomobject]@{ Key = "IMAGE_BASE_URL"; Required = $false; Secret = $false; Prompt = "ModernGallery image base URL" },
      [pscustomobject]@{ Key = "API_BASE_URL"; Required = $false; Secret = $false; Prompt = "ModernGallery frontend API base URL" }
    )
  }
)

foreach ($spec in $specs) {
  Apply-EnvSpec -Spec $spec -UseNonInteractive:$NonInteractive
}

$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$syncEnvScript = Join-Path $repoRoot "scripts/sync-env-files.ps1"

if (Test-Path $syncEnvScript) {
  & $syncEnvScript -RepoRoot $repoRoot -WorkspaceRoot $root -DryRun:$DryRun
} else {
  Write-Warning "sync-env-files script not found: $syncEnvScript"
}

Write-Host "Environment setup finished."
