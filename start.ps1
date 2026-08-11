# Start Web Scraper Pro dashboard (Windows PowerShell)
# Run from anywhere:  .\start.ps1
# Or from repo root:  cd web-scraper; .\start.ps1

$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

Write-Host "Web Scraper Pro — starting..." -ForegroundColor Cyan

if (-not (Test-Path ".venv\Scripts\python.exe")) {
    Write-Host "Creating virtual environment..." -ForegroundColor Yellow
    python -m venv .venv
}

Write-Host "Installing dependencies..." -ForegroundColor Yellow
.\.venv\Scripts\python.exe -m pip install -q -r requirements.txt

if (-not (Test-Path ".env")) {
    Copy-Item ".env.example" ".env"
    Write-Host "Created .env from .env.example" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "Dashboard:  http://127.0.0.1:8000" -ForegroundColor Green
Write-Host "API docs:   http://127.0.0.1:8000/api/docs" -ForegroundColor Green
Write-Host "Health:     http://127.0.0.1:8000/api/health" -ForegroundColor Green
Write-Host ""
Write-Host "Press Ctrl+C to stop the server." -ForegroundColor DarkGray

.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
