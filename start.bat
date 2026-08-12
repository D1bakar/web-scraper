@echo off
setlocal EnableExtensions
title Web Scraper Pro

REM Always run from the folder containing this script (works when double-clicked in Explorer)
cd /d "%~dp0"

echo.
echo   Web Scraper Pro - Starting...
echo.

REM Prefer PowerShell launcher (venv setup, port cleanup, deps)
where powershell >nul 2>&1
if not errorlevel 1 (
    powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0start.ps1"
    if not errorlevel 1 goto :done
    echo.
    echo   PowerShell launcher failed - trying batch fallback...
    echo.
)

call "%~dp0start-batch.cmd"
if errorlevel 1 goto :failed

:done
exit /b 0

:failed
echo.
echo   Startup failed. See messages above.
pause
exit /b 1
