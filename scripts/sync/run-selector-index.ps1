[CmdletBinding()]
param(
  [string]$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "../..")).Path,
  [string]$SelectorIndexCommand,
  [string[]]$SelectorIndexArgs,
  [switch]$DryRun
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Resolve-SelectorArgs {
  param(
    [string[]]$RawArgs,
    [string]$ResolvedRepoRoot
  )

  $resolved = @()
  foreach ($arg in @($RawArgs)) {
    if ($null -eq $arg) { continue }
    $resolved += ([string]$arg).Replace("{REPO_ROOT}", $ResolvedRepoRoot)
  }
  return ,$resolved
}

function Test-PythonModules {
  param(
    [string]$PythonPath,
    [string[]]$Modules
  )

  if (-not $Modules -or $Modules.Count -eq 0) {
    return $true
  }

  $imports = ($Modules | ForEach-Object { "import $_" }) -join "; "
  & $PythonPath -c $imports 2>$null
  return ($LASTEXITCODE -eq 0)
}

if ($DryRun) {
  Write-Host "[dry-run] skip selector index build"
  return
}

$resolvedRepoRoot = (Resolve-Path $RepoRoot).Path

if (-not [string]::IsNullOrWhiteSpace($SelectorIndexCommand)) {
  $resolvedArgs = Resolve-SelectorArgs -RawArgs $SelectorIndexArgs -ResolvedRepoRoot $resolvedRepoRoot
  if ($resolvedArgs.Count -eq 0) {
    $resolvedArgs = @("--repo-root", $resolvedRepoRoot)
  }

  Write-Host "Building selector index via external command: $SelectorIndexCommand"
  & $SelectorIndexCommand @resolvedArgs
  if ($LASTEXITCODE -ne 0) {
    throw "External selector index command failed: $SelectorIndexCommand (exit=$LASTEXITCODE)"
  }
  return
}

# Local fallback for backward compatibility.
Write-Host "Building selector index via local ai-config module..."

$pythonCandidates = @(
  (Join-Path $resolvedRepoRoot ".venv/Scripts/python.exe"),
  (Join-Path $resolvedRepoRoot ".venv/bin/python")
)
$systemPython = Get-Command -Name python -ErrorAction SilentlyContinue
if ($systemPython) {
  $pythonCandidates += $systemPython.Source
}

$embeddingBackend = [System.Environment]::GetEnvironmentVariable("AI_CONFIG_EMBEDDING_BACKEND")
if ([string]::IsNullOrWhiteSpace($embeddingBackend)) {
  $embeddingBackend = "hash"
}
$vectorBackend = [System.Environment]::GetEnvironmentVariable("AI_CONFIG_VECTOR_BACKEND")
if ([string]::IsNullOrWhiteSpace($vectorBackend)) {
  $vectorBackend = "numpy"
}

$requiredModules = @("rank_bm25", "numpy")
if ($embeddingBackend -eq "sentence_transformer") {
  $requiredModules += "sentence_transformers"
}
if ($vectorBackend -eq "faiss") {
  $requiredModules += "faiss"
}

$pythonPath = $null
foreach ($candidate in @($pythonCandidates | Select-Object -Unique)) {
  if (-not (Test-Path $candidate)) { continue }
  if (Test-PythonModules -PythonPath $candidate -Modules $requiredModules) {
    $pythonPath = $candidate
    break
  }
  Write-Warning "Skipping Python candidate due to missing modules: $candidate"
}

if (-not $pythonPath) {
  throw "No Python runtime found with required modules: $($requiredModules -join ', ')"
}

$pythonModulePath = Join-Path $resolvedRepoRoot "src"
$originalPythonPath = [System.Environment]::GetEnvironmentVariable("PYTHONPATH", "Process")
$didSetPythonPath = $false
if (Test-Path $pythonModulePath) {
  if ([string]::IsNullOrWhiteSpace($originalPythonPath)) {
    $env:PYTHONPATH = $pythonModulePath
  }
  else {
    $env:PYTHONPATH = "$pythonModulePath;$originalPythonPath"
  }
  $didSetPythonPath = $true
}

try {
  & $pythonPath -m ai_config.build_index --repo-root $resolvedRepoRoot
  if ($LASTEXITCODE -ne 0) {
    throw "Local selector index build failed with python: $pythonPath (exit=$LASTEXITCODE)"
  }
}
finally {
  if ($didSetPythonPath) {
    if ($null -eq $originalPythonPath) {
      Remove-Item Env:PYTHONPATH -ErrorAction SilentlyContinue
    }
    else {
      $env:PYTHONPATH = $originalPythonPath
    }
  }
}
