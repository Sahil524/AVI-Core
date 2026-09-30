@echo off
setlocal enabledelayedexpansion
cd /d "%~dp0"

echo ============================================================
echo AVI Core — Windows Setup Launcher
echo ============================================================

REM Check if PowerShell is available
where powershell.exe >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo [ERROR] powershell.exe was not found in PATH.
    echo Please install Windows PowerShell to continue.
    pause
    exit /b 1
)

powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0install.ps1" %*
set "EXIT_CODE=%ERRORLEVEL%"

if %EXIT_CODE% neq 0 (
    echo.
    echo [ERROR] Installation failed with exit code %EXIT_CODE%.
    echo Check %%LOCALAPPDATA%%\AVICore\logs\installer.log for details.
    echo.
    pause
)

exit /b %EXIT_CODE%
