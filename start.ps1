# Start Web Scraper Pro dashboard (Windows PowerShell)
# Run from anywhere:  .\start.ps1

$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

Write-Host ""
Write-Host "  Web Scraper Pro v2.1" -ForegroundColor Cyan
Write-Host "  ====================" -ForegroundColor DarkGray
Write-Host ""

# Verify Python is available
try {
    $pythonVersion = python --version 2>&1
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
& $py -m pip install -q --upgrade pip 2>$null
& $py -m pip install -q -r requirements.txt
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

Write-Host ""
Write-Host "  Dashboard:  http://127.0.0.1:8000" -ForegroundColor Green
Write-Host "  API docs:   http://127.0.0.1:8000/api/docs" -ForegroundColor Green
Write-Host "  Health:     http://127.0.0.1:8000/api/health/detail" -ForegroundColor Green
Write-Host ""
Write-Host "  Press Ctrl+C to stop the server." -ForegroundColor DarkGray
Write-Host ""

& $py -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
