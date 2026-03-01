[CmdletBinding()]
param(
  [string]$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "../..")).Path,
  [double]$DebounceSec = 1.5
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$resolvedRepoRoot = (Resolve-Path $RepoRoot).Path
$pythonCandidates = @(
  (Join-Path $resolvedRepoRoot ".venv/Scripts/python.exe"),
  (Join-Path $resolvedRepoRoot ".venv/bin/python")
)

$pythonPath = $null
foreach ($candidate in $pythonCandidates) {
  if (Test-Path $candidate) {
    $pythonPath = $candidate
    break
  }
}

if (-not $pythonPath) {
  throw "No local Python found under .venv (expected .venv/Scripts/python.exe or .venv/bin/python)"
}

$pythonModulePath = Join-Path $resolvedRepoRoot "src"
$originalPythonPath = [System.Environment]::GetEnvironmentVariable("PYTHONPATH", "Process")
if ([string]::IsNullOrWhiteSpace($originalPythonPath)) {
  $env:PYTHONPATH = $pythonModulePath
}
else {
  $env:PYTHONPATH = "$pythonModulePath;$originalPythonPath"
}

try {
  & $pythonPath -m ai_config.build_index --repo-root $resolvedRepoRoot --watch --debounce-sec $DebounceSec
  if ($LASTEXITCODE -ne 0) {
    throw "ai_config.build_index watch exited with code $LASTEXITCODE"
  }
}
finally {
  if ([string]::IsNullOrWhiteSpace($originalPythonPath)) {
    Remove-Item Env:PYTHONPATH -ErrorAction SilentlyContinue
  }
  else {
    $env:PYTHONPATH = $originalPythonPath
  }
}
