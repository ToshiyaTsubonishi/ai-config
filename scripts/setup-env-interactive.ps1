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
    EnvPath = (Join-Path $root "ai-config/.env")
    TemplatePath = (Join-Path $root "ai-config/.env.example")
    Variables = @(
      [pscustomobject]@{ Key = "GITHUB_PERSONAL_ACCESS_TOKEN"; Required = $false; Secret = $true; Prompt = "GitHub PAT for github-mcp" },
      [pscustomobject]@{ Key = "CONTEXT7_API_KEY"; Required = $false; Secret = $true; Prompt = "Context7 API key" },
      [pscustomobject]@{ Key = "FIRECRAWL_API_KEY"; Required = $false; Secret = $true; Prompt = "Firecrawl API key" },
      [pscustomobject]@{ Key = "FIGMA_API_KEY"; Required = $false; Secret = $true; Prompt = "Figma API key" },
      [pscustomobject]@{ Key = "JINA_API_KEY"; Required = $false; Secret = $true; Prompt = "Jina API key" }
    )
  },
  [pscustomobject]@{
    Name = "ai-agent-collection/docker-infrastructure"
    EnvPath = (Join-Path $root "ai-agent-collection/docker-infrastructure/.env")
    TemplatePath = (Join-Path $root "ai-agent-collection/docker-infrastructure/.env.template")
    Variables = @(
      [pscustomobject]@{ Key = "GOOGLE_API_KEY"; Required = $true; Secret = $true; Prompt = "Google API key" },
      [pscustomobject]@{ Key = "HF_TOKEN"; Required = $false; Secret = $true; Prompt = "HuggingFace token" }
    )
  },
  [pscustomobject]@{
    Name = "ModernGallery"
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

Write-Host "Environment setup finished."
