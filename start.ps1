# Start Web Scraper Pro dashboard (Windows PowerShell)
# Run from web-scraper folder:  .\start.ps1
# If you get PSSecurityException, use:  .\start.bat

$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

Write-Host ""
Write-Host "  Web Scraper Pro v2.6.0" -ForegroundColor Cyan
Write-Host "  ======================" -ForegroundColor DarkGray
Write-Host ""

# Verify Python is available
try {
    $pythonVersion = python --version 2>&1
    if ($LASTEXITCODE -ne 0) { throw "Python not found" }
    Write-Host "  Python: $pythonVersion" -ForegroundColor DarkGray
} catch {
    Write-Host "  ERROR: Python not found. Install Python 3.10+ from https://python.org" -ForegroundColor Red
    exit 1
}

# Create venv if missing
if (-not (Test-Path ".venv\Scripts\python.exe")) {
    Write-Host "  Creating virtual environment..." -ForegroundColor Yellow
    python -m venv .venv
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
}

$py = ".\.venv\Scripts\python.exe"

# Install / upgrade dependencies
Write-Host "  Installing dependencies..." -ForegroundColor Yellow
& $py -m pip install -q --progress-bar off --upgrade pip 2>$null
& $py -m pip install -q --progress-bar off -r requirements.txt
if ($LASTEXITCODE -ne 0) {
    Write-Host "  ERROR: Failed to install dependencies." -ForegroundColor Red
    exit 1
}

# Create .env from example if missing
if (-not (Test-Path ".env")) {
    Copy-Item ".env.example" ".env"
    Write-Host "  Created .env from .env.example" -ForegroundColor Yellow
}

# Ensure data directory exists
New-Item -ItemType Directory -Force -Path "data" | Out-Null

# Free port 8000 if an old server is still running (prevents stale instances)
try {
    $conn = Get-NetTCPConnection -LocalPort 8000 -State Listen -ErrorAction SilentlyContinue | Select-Object -First 1
    if ($conn) {
        Write-Host "  Port 8000 in use - stopping PID $($conn.OwningProcess)..." -ForegroundColor Yellow
        Stop-Process -Id $conn.OwningProcess -Force -ErrorAction SilentlyContinue
        Start-Sleep -Seconds 1
    }
} catch {
    # Fallback when Get-NetTCPConnection is unavailable
    $netstat = netstat -ano | Select-String ":8000\s+.*LISTENING\s+(\d+)" | Select-Object -First 1
    if ($netstat -match "(\d+)\s*$") {
        $oldPid = [int]$Matches[1]
        Write-Host "  Port 8000 in use - stopping PID $oldPid..." -ForegroundColor Yellow
        Stop-Process -Id $oldPid -Force -ErrorAction SilentlyContinue
        Start-Sleep -Seconds 1
    }
}

$phoneSetup = $args -contains "--phone-setup"

Write-Host ""
if ($phoneSetup) {
    & $py scripts/print_access_urls.py 8000 --qr
} else {
    & $py scripts/print_access_urls.py 8000
}
Write-Host ""
if ($phoneSetup) {
    Write-Host "  Still cannot connect? Double-click start-tunnel.bat for a public HTTPS URL." -ForegroundColor Yellow
}
Write-Host "  Tip: verify version is 2.6.0 at /api/health before testing modes." -ForegroundColor DarkGray
Write-Host "  Press Ctrl+C to stop the server." -ForegroundColor DarkGray
Write-Host ""

# Bind 0.0.0.0 so phones on the same Wi-Fi / hotspot can reach the dashboard
& $py -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
