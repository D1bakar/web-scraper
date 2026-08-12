@echo off
setlocal EnableExtensions
title Web Scraper Pro - Public Tunnel

cd /d "%~dp0"

echo.
echo   Web Scraper Pro - Public Tunnel
echo   ===============================
echo.
echo   Use this when your phone cannot reach the PC over Wi-Fi or hotspot.
echo   Creates a public HTTPS URL that works on mobile data (SIM).
echo.

python --version >nul 2>&1
if errorlevel 1 (
    echo   ERROR: Python not installed.
    pause
    exit /b 1
)

if not exist ".venv\Scripts\python.exe" (
    echo   Creating virtual environment...
    python -m venv .venv
)

set "PY=%~dp0.venv\Scripts\python.exe"

echo   Installing dependencies...
"%PY%" -m pip install -q --upgrade pip
"%PY%" -m pip install -q -r requirements.txt
"%PY%" -m pip install -q -r requirements-tunnel.txt
if errorlevel 1 exit /b 1

if not exist ".env" copy /Y ".env.example" ".env" >nul

REM Free port 8000
for /f "tokens=5" %%p in ('netstat -ano ^| findstr /R /C:":8000 .*LISTENING"') do (
    taskkill /PID %%p /F >nul 2>&1
)

echo   Starting server in background...
start "Web Scraper Pro Server" /MIN "%PY%" -m uvicorn app.main:app --host 0.0.0.0 --port 8000

echo   Waiting for server...
timeout /t 3 /nobreak >nul

powershell -NoProfile -Command "try { (Invoke-WebRequest -Uri 'http://127.0.0.1:8000/api/health' -UseBasicParsing).StatusCode } catch { exit 1 }"
if errorlevel 1 (
    echo   ERROR: Server did not start. Check errors above.
    pause
    exit /b 1
)

echo   Server is running. Starting tunnel...
echo.

REM Try ngrok CLI first, then cloudflared, then pyngrok
where ngrok >nul 2>&1
if not errorlevel 1 (
    echo   Using ngrok CLI...
    ngrok http 8000
    goto :cleanup
)

where cloudflared >nul 2>&1
if not errorlevel 1 (
    echo   Using cloudflared...
    cloudflared tunnel --url http://localhost:8000
    goto :cleanup
)

echo   ngrok/cloudflared not found — using pyngrok ^(requires NGROK_AUTHTOKEN in .env^)...
"%PY%" scripts/tunnel.py 8000
goto :cleanup

:cleanup
echo.
echo   Tunnel closed. Stopping background server...
for /f "tokens=5" %%p in ('netstat -ano ^| findstr /R /C:":8000 .*LISTENING"') do (
    taskkill /PID %%p /F >nul 2>&1
)
pause
exit /b 0
