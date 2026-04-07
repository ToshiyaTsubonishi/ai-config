param(
    [switch]$SkipVendorSync
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$RepoRoot = Split-Path -Parent $PSScriptRoot
Set-Location $RepoRoot

function Write-ModuleWrapper {
    param(
        [string]$Name,
        [string]$Module,
        [string]$PythonVersionTag
    )

    $wrapperPath = Join-Path $RepoRoot ".venv\Scripts\$Name.cmd"
    $content = @"
@echo off
setlocal
set "REPO_ROOT=$RepoRoot"
set "BOOTSTRAP=%REPO_ROOT%\scripts\run_module.py"
set "VENV_PYTHON=%REPO_ROOT%\.venv\Scripts\python.exe"
set "LOCAL_PY=%REPO_ROOT%\.venv\Scripts\py.exe"
set "PYTHONPATH=%REPO_ROOT%\src;%PYTHONPATH%"
if exist "%VENV_PYTHON%" goto run_venv
if exist "%LOCAL_PY%" goto run_local_py_version
goto run_py_version
:run_venv
"%VENV_PYTHON%" -m $Module %*
if not errorlevel 1 exit /b 0
:run_local_py_version
"%LOCAL_PY%" -$PythonVersionTag "%BOOTSTRAP%" $Module %*
if not errorlevel 1 exit /b 0
:run_py_version
py -$PythonVersionTag "%BOOTSTRAP%" $Module %*
if not errorlevel 1 exit /b 0
:run_py_default
py "%BOOTSTRAP%" $Module %*
if not errorlevel 1 exit /b 0
:run_python_default
python "%BOOTSTRAP%" $Module %*
exit /b %ERRORLEVEL%
"@
    Set-Content -Path $wrapperPath -Value $content -Encoding ASCII
}

function Get-VenvPythonVersionTag {
    $configPath = Join-Path $RepoRoot ".venv\pyvenv.cfg"
    if (-not (Test-Path $configPath)) {
        return "3.11"
    }

    foreach ($line in Get-Content -Path $configPath) {
        if ($line -notmatch "^version\s*=\s*([0-9]+)\.([0-9]+)") {
            continue
        }
        return "$($Matches[1]).$($Matches[2])"
    }

    return "3.11"
}

function Get-PythonCandidate {
    $candidates = @(
        @{ Command = "python"; Args = @() },
        @{ Command = "py"; Args = @("-3.13") },
        @{ Command = "py"; Args = @("-3.12") },
        @{ Command = "py"; Args = @("-3.11") },
        @{ Command = "py"; Args = @() }
    )

    foreach ($candidate in $candidates) {
        if (-not (Get-Command $candidate.Command -ErrorAction SilentlyContinue)) {
            continue
        }
        try {
            & $candidate.Command @($candidate.Args + @("-c", "import sys; raise SystemExit(0 if sys.version_info >= (3, 11) else 1)")) | Out-Null
            if ($LASTEXITCODE -eq 0) {
                return $candidate
            }
        } catch {
        }
    }

    throw "Python 3.11 or newer was not found."
}

Write-Host "=== ai-config setup ==="
Write-Host "Repo root: $RepoRoot"

$venvPython = Join-Path $RepoRoot ".venv\Scripts\python.exe"
$needsRecreate = -not (Test-Path $venvPython)
if (-not $needsRecreate) {
    try {
        & $venvPython -c "import sys; raise SystemExit(0 if sys.version_info >= (3, 11) else 1)" | Out-Null
        if ($LASTEXITCODE -ne 0) {
            $needsRecreate = $true
        }
    } catch {
        $needsRecreate = $true
    }
}

if ($needsRecreate) {
    $python = Get-PythonCandidate
    Write-Host "Creating virtual environment with $($python.Command) $($python.Args -join ' ')"
    & $python.Command @($python.Args + @("-m", "venv", "--clear", ".venv"))
}

if (-not (Test-Path (Join-Path $RepoRoot ".env")) -and (Test-Path (Join-Path $RepoRoot ".env.example"))) {
    Copy-Item (Join-Path $RepoRoot ".env.example") (Join-Path $RepoRoot ".env")
    Write-Host "Created .env from .env.example"
}

$venvPython = Join-Path $RepoRoot ".venv\Scripts\python.exe"
$indexCmd = Join-Path $RepoRoot ".venv\Scripts\ai-config-index.cmd"
$venvVersionTag = Get-VenvPythonVersionTag
$pyLauncher = Get-Command py -ErrorAction SilentlyContinue
$localPyLauncher = Join-Path $RepoRoot ".venv\Scripts\py.exe"

Write-Host "Installing ai-config..."
& $venvPython -m pip install --upgrade pip --quiet
& $venvPython -m pip install ".[dev]" --quiet

if ($pyLauncher) {
    Copy-Item -Force $pyLauncher.Source $localPyLauncher
}

Write-Host "Generating Windows runtime wrappers..."
Write-ModuleWrapper -Name "ai-config-agent" -Module "ai_config.orchestrator.cli" -PythonVersionTag $venvVersionTag
Write-ModuleWrapper -Name "ai-config-doctor" -Module "ai_config.doctor" -PythonVersionTag $venvVersionTag
Write-ModuleWrapper -Name "ai-config-index" -Module "ai_config.build_index" -PythonVersionTag $venvVersionTag
Write-ModuleWrapper -Name "ai-config-mcp-server" -Module "ai_config.mcp_server.server" -PythonVersionTag $venvVersionTag
Write-ModuleWrapper -Name "ai-config-sources" -Module "ai_config.source_manager" -PythonVersionTag $venvVersionTag
Write-ModuleWrapper -Name "ai-config-vendor-skills" -Module "ai_config.vendor.cli" -PythonVersionTag $venvVersionTag

if ($SkipVendorSync) {
    Write-Warning "Skipping vendor manifest sync. External skill coverage may be incomplete."
} else {
    Write-Host "Syncing vendor-managed external skills..."
    & $venvPython -m ai_config.vendor.cli --repo-root $RepoRoot sync-manifest
    if ($LASTEXITCODE -ne 0) {
        throw "Vendor manifest sync failed. The pinned ref materialization step did not complete. Retry with network access or rerun with -SkipVendorSync if partial external coverage is acceptable."
    }
}

Write-Host "Building tool index..."
& $indexCmd --repo-root $RepoRoot --profile default

Write-Host ""
Write-Host "=== Setup complete ==="
Write-Host "To start the MCP server:"
Write-Host "  $RepoRoot\.venv\Scripts\ai-config-mcp-server.cmd --repo-root $RepoRoot"
Write-Host ""
Write-Host "To register with your AI tools:"
Write-Host "  powershell -ExecutionPolicy Bypass -File scripts/register.ps1"
