@echo off
setlocal EnableExtensions

cd /d "%~dp0"

python --version >nul 2>&1
if errorlevel 1 (
    echo   ERROR: Python not installed or not on PATH.
    echo   Install Python 3.10+ from https://python.org
    echo   During install, check "Add python.exe to PATH".
    exit /b 1
)

for /f "delims=" %%v in ('python --version 2^>^&1') do echo   Python: %%v

if not exist ".venv\Scripts\python.exe" (
    echo   Creating virtual environment...
    python -m venv .venv
    if errorlevel 1 exit /b 1
)

set "PY=%~dp0.venv\Scripts\python.exe"

echo   Installing dependencies...
"%PY%" -m pip install -q --upgrade pip
"%PY%" -m pip install -q -r requirements.txt
if errorlevel 1 (
    echo   ERROR: Failed to install dependencies.
    exit /b 1
)

if not exist ".env" (
    copy /Y ".env.example" ".env" >nul
    echo   Created .env from .env.example
)

if not exist "data" mkdir "data"

REM Free port 8000 if something is already listening
for /f "tokens=5" %%p in ('netstat -ano ^| findstr /R /C:":8000 .*LISTENING"') do (
    echo   Port 8000 in use - stopping PID %%p...
    taskkill /PID %%p /F >nul 2>&1
)

echo.
echo   Dashboard:  http://127.0.0.1:8000
echo   API docs:   http://127.0.0.1:8000/api/docs
echo   Health:     http://127.0.0.1:8000/api/health
echo.
echo   Press Ctrl+C to stop the server.
echo.

"%PY%" -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
