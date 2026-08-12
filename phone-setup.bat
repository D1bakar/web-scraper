@echo off
setlocal EnableExtensions
title Web Scraper Pro - Phone Setup

cd /d "%~dp0"

if /I "%~1"=="--firewall-only" goto :firewall_only

echo.
echo   ============================================================
echo     WEB SCRAPER PRO - PHONE SETUP
echo   ============================================================
echo.

REM --- Firewall (elevate if needed) ---
net session >nul 2>&1
if errorlevel 1 (
    echo   Step 1/2: Adding Windows Firewall rule ^(needs Admin^)...
    powershell -NoProfile -Command "Start-Process -FilePath '%~f0' -ArgumentList '--firewall-only' -Verb RunAs -Wait"
) else (
    call :add_firewall_rule
)

echo.
echo   Step 2/2: Starting server...
echo.

where powershell >nul 2>&1
if not errorlevel 1 (
    powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0start.ps1" --phone-setup
    goto :done
)

call "%~dp0start-batch.cmd" --phone-setup
goto :done

:firewall_only
cd /d "%~dp0"
call :add_firewall_rule
exit /b 0

:add_firewall_rule
netsh advfirewall firewall show rule name="Web Scraper Pro (port 8000)" >nul 2>&1
if not errorlevel 1 (
    echo   Firewall rule already exists for port 8000.
    exit /b 0
)
netsh advfirewall firewall add rule name="Web Scraper Pro (port 8000)" dir=in action=allow protocol=TCP localport=8000 >nul
if errorlevel 1 (
    echo   WARNING: Could not add firewall rule. Run as Administrator.
    exit /b 1
)
echo   Added inbound firewall rule for TCP port 8000.
exit /b 0

:done
exit /b 0
