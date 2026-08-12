@echo off
setlocal EnableExtensions
title Web Scraper Pro - Allow Phone Access

echo.
echo   Web Scraper Pro - Windows Firewall Setup
echo   ========================================
echo.

net session >nul 2>&1
if errorlevel 1 (
    echo   ERROR: Administrator privileges required.
    echo.
    echo   Right-click this file and choose "Run as administrator",
    echo   or run in an elevated Command Prompt:
    echo.
    echo     netsh advfirewall firewall add rule name="Web Scraper Pro (port 8000)" dir=in action=allow protocol=TCP localport=8000
    echo.
    pause
    exit /b 1
)

netsh advfirewall firewall show rule name="Web Scraper Pro (port 8000)" >nul 2>&1
if not errorlevel 1 (
    echo   Firewall rule already exists for port 8000.
    goto :done
)

netsh advfirewall firewall add rule name="Web Scraper Pro (port 8000)" dir=in action=allow protocol=TCP localport=8000
if errorlevel 1 (
    echo   ERROR: Failed to add firewall rule.
    pause
    exit /b 1
)

echo   Added inbound firewall rule for TCP port 8000.

:done
echo.
echo   Next steps:
echo     1. Double-click phone-setup.bat  (firewall + server + phone URL)
echo     2. On your phone, open the URL shown at startup
echo.
echo   If the phone still cannot connect:
echo     - Phone must NOT use mobile data (SIM) while PC is on Wi-Fi
echo     - Some phone hotspots block phone-to-PC access
echo     - Use start-tunnel.bat for a public HTTPS link (works anywhere)
echo.
pause
exit /b 0
