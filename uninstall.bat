@echo off
setlocal enabledelayedexpansion
cd /d "%~dp0"

echo ============================================================
echo AVI Core — Windows Uninstall Launcher
echo ============================================================

REM Check if PowerShell is available
where powershell.exe >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo [ERROR] powershell.exe was not found in PATH.
    pause
    exit /b 1
)

powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0uninstall.ps1" %*
set "EXIT_CODE=%ERRORLEVEL%"

if %EXIT_CODE% neq 0 (
    echo.
    echo [ERROR] Uninstallation encountered errors (code %EXIT_CODE%).
    pause
)

exit /b %EXIT_CODE%
