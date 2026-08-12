@echo off
REM Start Web Scraper Pro (works even when PowerShell script execution is restricted)
cd /d "%~dp0"
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0start.ps1"
