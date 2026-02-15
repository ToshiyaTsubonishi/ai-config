param(
    [string]$PropertyId = "",
    [string]$PythonCommand = "python",
    [string]$CsvPath = ""
)

$ErrorActionPreference = "Stop"

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$repoRoot = Split-Path -Parent $scriptDir
$localEnvFile = Join-Path $repoRoot ".env"

if (Test-Path -LiteralPath $localEnvFile) {
    foreach ($line in Get-Content -LiteralPath $localEnvFile) {
        if ($line -match "^\s*#" -or $line -match "^\s*$") {
            continue
        }
        if ($line -match "^\s*([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.*)\s*$") {
            $key = $matches[1]
            $value = $matches[2].Trim()
            if (
                ($value.StartsWith('"') -and $value.EndsWith('"')) -or
                ($value.StartsWith("'") -and $value.EndsWith("'"))
            ) {
                $value = $value.Substring(1, $value.Length - 2)
            }
            if ([string]::IsNullOrWhiteSpace((Get-Item "Env:$key" -ErrorAction SilentlyContinue).Value)) {
                Set-Item -Path "Env:$key" -Value $value
            }
        }
    }
}

if ([string]::IsNullOrWhiteSpace($PropertyId)) {
    $PropertyId = $env:GA4_PROPERTY_ID
}

$ga4QueryScript = Join-Path $HOME ".agents/skills/ga4/scripts/ga4_query.py"

if (-not (Test-Path -LiteralPath $ga4QueryScript)) {
    throw "GA4 skill script not found: $ga4QueryScript"
}

if ([string]::IsNullOrWhiteSpace($PropertyId)) {
    throw "GA4 Property ID is required. Set GA4_PROPERTY_ID or pass -PropertyId."
}

$requiredEnv = @(
    "GOOGLE_CLIENT_ID",
    "GOOGLE_CLIENT_SECRET",
    "GOOGLE_REFRESH_TOKEN"
)

$missingEnv = $requiredEnv | Where-Object { [string]::IsNullOrWhiteSpace((Get-Item "Env:$_" -ErrorAction SilentlyContinue).Value) }
if ($missingEnv.Count -gt 0) {
    throw "Missing env vars: $($missingEnv -join ', ')"
}

$endDate = Get-Date
$startDate = $endDate.AddDays(-6)

$start = $startDate.ToString("yyyy-MM-dd")
$end = $endDate.ToString("yyyy-MM-dd")

$args = @(
    $ga4QueryScript,
    "--property", $PropertyId,
    "--metrics", "sessions,conversions",
    "--dimension", "date",
    "--start", $start,
    "--end", $end,
    "--limit", "500",
    "--json"
)

Write-Host "Running GA4 query for $start to $end (Property: $PropertyId)..."
$json = & $PythonCommand @args
if ($LASTEXITCODE -ne 0) {
    throw "ga4_query.py failed with exit code $LASTEXITCODE"
}

$rows = $json | ConvertFrom-Json
if ($null -eq $rows) {
    throw "No data returned."
}

$reportRows = @()
$totalSessions = 0.0
$totalConversions = 0.0

foreach ($row in $rows) {
    $sessions = [double]$row.sessions
    $conversions = [double]$row.conversions
    $cvr = if ($sessions -gt 0) { ($conversions / $sessions) * 100 } else { 0.0 }

    $dateText = [string]$row.date
    if ($dateText -match "^\d{8}$") {
        $dateText = [datetime]::ParseExact($dateText, "yyyyMMdd", $null).ToString("yyyy-MM-dd")
    }

    $reportRows += [pscustomobject]@{
        Date = $dateText
        Sessions = [math]::Round($sessions, 2)
        Conversions = [math]::Round($conversions, 2)
        CVR_Percent = [math]::Round($cvr, 2)
    }

    $totalSessions += $sessions
    $totalConversions += $conversions
}

$totalCvr = if ($totalSessions -gt 0) { ($totalConversions / $totalSessions) * 100 } else { 0.0 }

Write-Host ""
Write-Host "=== Last 7 Days: Sessions / CVR ==="
$reportRows | Sort-Object Date | Format-Table -AutoSize

Write-Host ""
Write-Host "=== Total (7 days) ==="
Write-Host ("Sessions    : {0:N2}" -f $totalSessions)
Write-Host ("Conversions : {0:N2}" -f $totalConversions)
Write-Host ("CVR (%)     : {0:N2}" -f $totalCvr)

if (-not [string]::IsNullOrWhiteSpace($CsvPath)) {
    $reportRows | Sort-Object Date | Export-Csv -Path $CsvPath -Encoding UTF8 -NoTypeInformation
    Write-Host "Saved CSV: $CsvPath"
}
