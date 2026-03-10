param(
    [ValidateSet("status", "pull", "push")]
    [string]$Mode = "status",
    [switch]$DryRun
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$RepoRoot = Split-Path -Parent $PSScriptRoot
$pairs = @(
    @{
        Name = "agent"
        Store = Join-Path $RepoRoot "instructions\Agent.md"
        Target = Join-Path $HOME ".codex\AGENTS.md"
    },
    @{
        Name = "gemini"
        Store = Join-Path $RepoRoot "instructions\Gemini.md"
        Target = Join-Path $HOME ".gemini\GEMINI.md"
    },
    @{
        Name = "lesson"
        Store = Join-Path $RepoRoot "instructions\Lesson.md"
        Target = Join-Path $RepoRoot "tasks\lessons.md"
    }
)

function Get-HashOrDash {
    param([string]$Path)
    if (-not (Test-Path $Path)) {
        return "-"
    }
    return (Get-FileHash -Algorithm SHA256 $Path).Hash.ToLowerInvariant()
}

function Copy-WithLog {
    param(
        [string]$Source,
        [string]$Destination,
        [string]$Label
    )

    if ($DryRun) {
        Write-Host "[DRY RUN] ${Label}: $Source -> $Destination"
        return
    }

    $parent = Split-Path -Parent $Destination
    if ($parent) {
        New-Item -ItemType Directory -Force -Path $parent | Out-Null
    }
    Copy-Item -Force $Source $Destination
    Write-Host "[SYNC] ${Label}: $Source -> $Destination"
}

function Invoke-Pull {
    foreach ($pair in $pairs) {
        if (-not (Test-Path $pair.Target)) {
            Write-Host "[SKIP] $($pair.Name): runtime file not found: $($pair.Target)"
            continue
        }
        Copy-WithLog -Source $pair.Target -Destination $pair.Store -Label $pair.Name
    }
}

function Invoke-Push {
    foreach ($pair in $pairs) {
        if (-not (Test-Path $pair.Store)) {
            Write-Host "[SKIP] $($pair.Name): repository file not found: $($pair.Store)"
            continue
        }
        Copy-WithLog -Source $pair.Store -Destination $pair.Target -Label $pair.Name
    }
}

function Show-Status {
    $rows = foreach ($pair in $pairs) {
        $storeExists = Test-Path $pair.Store
        $targetExists = Test-Path $pair.Target
        $state = "missing"
        if ($storeExists -and $targetExists) {
            if ((Get-HashOrDash $pair.Store) -eq (Get-HashOrDash $pair.Target)) {
                $state = "synced"
            } else {
                $state = "drift"
            }
        } elseif ($storeExists -or $targetExists) {
            $state = "partial"
        }

        [pscustomobject]@{
            Name = $pair.Name
            Store = if ($storeExists) { "yes" } else { "no" }
            Target = if ($targetExists) { "yes" } else { "no" }
            State = $state
            TargetPath = $pair.Target
        }
    }

    $rows | Format-Table -AutoSize
}

switch ($Mode) {
    "pull" { Invoke-Pull }
    "push" { Invoke-Push }
    "status" { Show-Status }
}
