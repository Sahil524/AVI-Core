# ============================================================
# AVI Core — Windows Uninstallation Script (PowerShell)
# Open-Source Offline Media Converter for Windows
# ============================================================

[CmdletBinding()]
param(
    [ValidateSet("User", "Machine", "Auto")]
    [string]$Scope = "Auto",
    [string]$InstallDir = "",
    [switch]$NoPrompt,
    [switch]$KeepLogs
)

$ErrorActionPreference = "Stop"

$LogDir = Join-Path $env:LOCALAPPDATA "AVICore\logs"
if (-not (Test-Path $LogDir)) {
    New-Item -Path $LogDir -ItemType Directory -Force | Out-Null
}
$LogFile = Join-Path $LogDir "installer.log"

function Write-UninstallerLog($msg, $level = "INFO") {
    $timestamp = (Get-Date).ToString("yyyy-MM-dd HH:mm:ss")
    $logLine = "$timestamp [UNINSTALL-$level] $msg"
    Add-Content -Path $LogFile -Value $logLine -ErrorAction SilentlyContinue

    switch ($level) {
        "ERROR"   { Write-Host $msg -ForegroundColor Red }
        "WARNING" { Write-Host $msg -ForegroundColor Yellow }
        "SUCCESS" { Write-Host $msg -ForegroundColor Green }
        "HEADER"  { Write-Host "`n$msg" -ForegroundColor Cyan }
        default   { Write-Host $msg -ForegroundColor White }
    }
}

function Exit-Uninstaller($code, $msg) {
    if ($code -ne 0) {
        Write-UninstallerLog $msg "ERROR"
        Write-UninstallerLog "Uninstallation failed with exit code $code." "ERROR"
    } else {
        Write-UninstallerLog $msg "SUCCESS"
        Write-UninstallerLog "Uninstallation completed successfully." "SUCCESS"
    }

    $isDirectConsole = ($Host.Name -eq "ConsoleHost") -and (-not $NoPrompt) -and (-not $env:CI)
    if ($isDirectConsole) {
        Write-Host "`nPress Enter to exit..." -ForegroundColor DarkGray
        [void][System.Console]::ReadLine()
    }

    exit $code
}

Write-UninstallerLog "============================================================" "HEADER"
Write-UninstallerLog "AVI Core Windows Uninstaller" "HEADER"
Write-UninstallerLog "============================================================" "HEADER"

try {
    # ------------------------------------------------------------
    # 1. Determine Scope & Installation Directory
    # ------------------------------------------------------------
    $currentIdentity = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = [Security.Principal.WindowsPrincipal]$currentIdentity
    $isAdmin = $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)

    $userTarget = Join-Path $env:LOCALAPPDATA "Programs\AVICore"
    $machineTarget = Join-Path $env:ProgramFiles "AVI Core"

    if (-not $InstallDir) {
        if (Test-Path $userTarget) {
            $InstallDir = $userTarget
            $Scope = "User"
        } elseif (Test-Path $machineTarget) {
            $InstallDir = $machineTarget
            $Scope = "Machine"
        } else {
            $InstallDir = $userTarget
            $Scope = if ($isAdmin) { "Machine" } else { "User" }
        }
    }

    Write-UninstallerLog "Target installation directory: $InstallDir (Scope: $Scope)" "INFO"

    # ------------------------------------------------------------
    # 2. Stop Any Active Processes
    # ------------------------------------------------------------
    Write-UninstallerLog "Stopping any running AVI Core processes..." "INFO"
    $running = Get-Process -Name "avicore", "context_menu" -ErrorAction SilentlyContinue
    if ($running) {
        $running | Stop-Process -Force -ErrorAction SilentlyContinue
        Start-Sleep -Milliseconds 500
    }

    # ------------------------------------------------------------
    # 3. Unregister Windows Explorer Context Menu
    # ------------------------------------------------------------
    $contextMenuExe = Join-Path $InstallDir "context_menu.exe"
    if (Test-Path $contextMenuExe) {
        Write-UninstallerLog "Unregistering Windows Explorer context menu entries..." "INFO"
        $unregProc = Start-Process -FilePath $contextMenuExe -ArgumentList "unregister", "--silent" -Wait -PassThru -NoNewWindow
        if ($unregProc.ExitCode -eq 0) {
            Write-UninstallerLog "Context menu unregistered successfully." "SUCCESS"
        } else {
            Write-UninstallerLog "Context menu unregistration returned code $($unregProc.ExitCode)." "WARNING"
        }
    } else {
        # Fallback to local python or context_menu.py if running from repo
        $localCm = Join-Path $PSScriptRoot "context_menu.py"
        if (Test-Path $localCm) {
            python "$localCm" unregister --silent
        }
    }

    # ------------------------------------------------------------
    # 4. Remove from PATH Environment Variable
    # ------------------------------------------------------------
    Write-UninstallerLog "Removing AVI Core from PATH environment variable..." "INFO"
    $targetBinPath = Join-Path $InstallDir "avicore"
    $normalizedTarget = [System.IO.Path]::GetFullPath($targetBinPath).TrimEnd('\')
    $normalizedBase = [System.IO.Path]::GetFullPath($InstallDir).TrimEnd('\')

    foreach ($targetScope in @([EnvironmentVariableTarget]::User, [EnvironmentVariableTarget]::Machine)) {
        if ($targetScope -eq [EnvironmentVariableTarget]::Machine -and -not $isAdmin) {
            continue
        }
        $rawPath = [Environment]::GetEnvironmentVariable("Path", $targetScope)
        if (-not $rawPath) { continue }

        $entries = $rawPath.Split(';', [System.StringSplitOptions]::RemoveEmptyEntries) | ForEach-Object { $_.Trim() }
        $filtered = @()
        $modified = $false
        foreach ($entry in $entries) {
            $norm = [System.IO.Path]::GetFullPath($entry).TrimEnd('\')
            if ($norm -eq $normalizedTarget -or $norm -eq $normalizedBase) {
                $modified = $true
            } else {
                $filtered += $entry
            }
        }
        if ($modified) {
            $newPath = $filtered -join ';'
            [Environment]::SetEnvironmentVariable("Path", $newPath, $targetScope)
            Write-UninstallerLog "Cleaned AVI Core from $($targetScope) PATH." "SUCCESS"
        }
    }

    # ------------------------------------------------------------
    # 5. Delete Application Files
    # ------------------------------------------------------------
    if (Test-Path $InstallDir) {
        Write-UninstallerLog "Deleting application directory: $InstallDir..." "INFO"
        Remove-Item -Path $InstallDir -Recurse -Force -ErrorAction SilentlyContinue
        if (Test-Path $InstallDir) {
            Write-UninstallerLog "Some files in $InstallDir could not be deleted immediately. They may be marked for deletion on reboot." "WARNING"
        } else {
            Write-UninstallerLog "Application directory removed." "SUCCESS"
        }
    }

    # ------------------------------------------------------------
    # 6. Clean Runtime Data (Optional Logs)
    # ------------------------------------------------------------
    $runtimeDir = Join-Path $env:LOCALAPPDATA "AVICore\runtime"
    if (Test-Path $runtimeDir) {
        Remove-Item -Path $runtimeDir -Recurse -Force -ErrorAction SilentlyContinue
    }

    if (-not $KeepLogs) {
        Write-UninstallerLog "Logs preserved at $LogFile. Pass -KeepLogs:$false to delete." "INFO"
    }

    Exit-Uninstaller 0 "AVI Core has been successfully uninstalled from this computer."

} catch {
    Exit-Uninstaller 1 "An unexpected error occurred during uninstallation: $_"
}
