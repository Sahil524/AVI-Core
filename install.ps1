# ============================================================
# AVI Core — Windows Installation Script (PowerShell)
# Open-Source Offline Media Converter for Windows
# ============================================================

[CmdletBinding()]
param(
    [ValidateSet("User", "Machine", "Auto")]
    [string]$Scope = "Auto",
    [string]$InstallDir = "",
    [switch]$NoPrompt,
    [switch]$BuildIfMissing
)

$ErrorActionPreference = "Stop"

# Establish absolute source path regardless of invocation working directory
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
if (-not $ScriptDir) { $ScriptDir = $PSScriptRoot }
if (-not $ScriptDir) { $ScriptDir = Get-Location }
$SourceDir = [System.IO.Path]::GetFullPath($ScriptDir)

# Ensure logging directory exists
$LogDir = Join-Path $env:LOCALAPPDATA "AVICore\logs"
if (-not (Test-Path $LogDir)) {
    New-Item -Path $LogDir -ItemType Directory -Force | Out-Null
}
$LogFile = Join-Path $LogDir "installer.log"

function Write-InstallerLog($msg, $level = "INFO") {
    $timestamp = (Get-Date).ToString("yyyy-MM-dd HH:mm:ss")
    $logLine = "$timestamp [$level] $msg"
    Add-Content -Path $LogFile -Value $logLine -ErrorAction SilentlyContinue

    switch ($level) {
        "ERROR"   { Write-Host $msg -ForegroundColor Red }
        "WARNING" { Write-Host $msg -ForegroundColor Yellow }
        "SUCCESS" { Write-Host $msg -ForegroundColor Green }
        "HEADER"  { Write-Host "`n$msg" -ForegroundColor Cyan }
        default   { Write-Host $msg -ForegroundColor White }
    }
}

function Exit-Installer($code, $msg) {
    if ($code -ne 0) {
        Write-InstallerLog $msg "ERROR"
        Write-InstallerLog "Installation failed with exit code $code." "ERROR"
        Write-InstallerLog "See installer log for details: $LogFile" "WARNING"
    } else {
        Write-InstallerLog $msg "SUCCESS"
        Write-InstallerLog "Installation completed successfully." "SUCCESS"
    }

    # If launched by double-clicking / Explorer, pause so the console window does not disappear
    $isDirectConsole = ($Host.Name -eq "ConsoleHost") -and (-not $NoPrompt) -and (-not $env:CI)
    if ($isDirectConsole) {
        Write-Host "`nPress Enter to exit..." -ForegroundColor DarkGray
        [void][System.Console]::ReadLine()
    }

    exit $code
}

Write-InstallerLog "============================================================" "HEADER"
Write-InstallerLog "AVI Core Windows Installer v2.0.0" "HEADER"
Write-InstallerLog "============================================================" "HEADER"
Write-InstallerLog "Invoked from working directory: $PWD" "INFO"
Write-InstallerLog "Source directory resolved to:   $SourceDir" "INFO"

try {
    # ------------------------------------------------------------
    # 1. Determine Administrative Privileges & Target Scope
    # ------------------------------------------------------------
    $currentIdentity = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = [Security.Principal.WindowsPrincipal]$currentIdentity
    $isAdmin = $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)

    if ($Scope -eq "Auto") {
        $Scope = if ($isAdmin) { "Machine" } else { "User" }
    }

    if ($Scope -eq "Machine" -and -not $isAdmin) {
        Write-InstallerLog "Machine scope requested but process is not elevated. Falling back to User scope." "WARNING"
        $Scope = "User"
    }

    Write-InstallerLog "Installation target scope: $Scope (Administrator: $isAdmin)" "INFO"

    # ------------------------------------------------------------
    # 2. Determine Installation Target Directory
    # ------------------------------------------------------------
    if (-not $InstallDir) {
        if ($Scope -eq "Machine") {
            $InstallDir = Join-Path $env:ProgramFiles "AVI Core"
        } else {
            $InstallDir = Join-Path $env:LOCALAPPDATA "Programs\AVICore"
        }
    }
    $InstallDir = [System.IO.Path]::GetFullPath($InstallDir)
    Write-InstallerLog "Installation directory: $InstallDir" "INFO"

    # ------------------------------------------------------------
    # 3. Validate Required Source Files
    # ------------------------------------------------------------
    Write-InstallerLog "Validating installation source files..." "INFO"

    $distAvicoreDir = Join-Path $SourceDir "dist\avicore"
    $distContextMenu = Join-Path $SourceDir "dist\context_menu.exe"
    $distAvicoreExe = Join-Path $distAvicoreDir "avicore.exe"
    $logoIco = Join-Path $SourceDir "logo.ico"

    $binariesPresent = (Test-Path $distAvicoreExe) -and (Test-Path $distContextMenu)

    if (-not $binariesPresent) {
        Write-InstallerLog "Compiled binaries not found in 'dist\' directory." "WARNING"

        # Check if we can build them automatically
        $buildScript = Join-Path $SourceDir "build_binaries.ps1"
        if (Test-Path $buildScript) {
            Write-InstallerLog "Triggering build_binaries.ps1 to generate compiled binaries..." "INFO"
            & powershell.exe -NoProfile -ExecutionPolicy Bypass -File "$buildScript"
            if ($LASTEXITCODE -ne 0 -or -not (Test-Path $distAvicoreExe)) {
                Exit-Installer 1 "Automated build failed. Please build binaries using build_binaries.ps1 before installing."
            }
            Write-InstallerLog "Binaries compiled successfully." "SUCCESS"
        } else {
            Exit-Installer 1 "Missing required files: dist\avicore\avicore.exe or dist\context_menu.exe not found at $SourceDir."
        }
    }

    # Ensure engine binary (ffmpeg.exe) is present in the distribution
    $distFfmpeg = Join-Path $distAvicoreDir "ffmpeg.exe"
    $rootFfmpeg = Join-Path $SourceDir "bin\ffmpeg.exe"

    if (-not (Test-Path $distFfmpeg) -and (Test-Path $rootFfmpeg)) {
        Write-InstallerLog "Copying ffmpeg.exe from bin/ into distribution directory..." "INFO"
        Copy-Item -Path $rootFfmpeg -Destination $distFfmpeg -Force
    }

    if (-not (Test-Path $distFfmpeg)) {
        Exit-Installer 1 "Engine binary (ffmpeg.exe) is missing from both dist\avicore\ and bin\."
    }

    # ------------------------------------------------------------
    # 4. Stop Any Active AVI Core Processes (Upgrade / Reinstall Protection)
    # ------------------------------------------------------------
    Write-InstallerLog "Checking for active AVI Core processes..." "INFO"
    $runningProcesses = Get-Process -Name "avicore", "context_menu" -ErrorAction SilentlyContinue
    if ($runningProcesses) {
        Write-InstallerLog "Active AVI Core processes detected. Stopping them to prevent file lock contention..." "WARNING"
        $runningProcesses | Stop-Process -Force -ErrorAction SilentlyContinue
        Start-Sleep -Milliseconds 500
    }

    # ------------------------------------------------------------
    # 5. Copy Application Files into Destination
    # ------------------------------------------------------------
    Write-InstallerLog "Deploying AVI Core binaries to: $InstallDir..." "INFO"
    if (-not (Test-Path $InstallDir)) {
        New-Item -Path $InstallDir -ItemType Directory -Force | Out-Null
    }

    # Target directory structure:
    #   $InstallDir\context_menu.exe
    #   $InstallDir\logo.ico
    #   $InstallDir\avicore\avicore.exe
    #   $InstallDir\avicore\ffmpeg.exe
    #   $InstallDir\avicore\_internal\...

    $targetAvicoreDir = Join-Path $InstallDir "avicore"
    if (-not (Test-Path $targetAvicoreDir)) {
        New-Item -Path $targetAvicoreDir -ItemType Directory -Force | Out-Null
    }

    # Copy avicore directory contents (recursively)
    Copy-Item -Path "$distAvicoreDir\*" -Destination $targetAvicoreDir -Recurse -Force
    Write-InstallerLog "Deployed avicore engine and dependencies." "INFO"

    # Copy context_menu.exe
    $targetContextMenu = Join-Path $InstallDir "context_menu.exe"
    Copy-Item -Path $distContextMenu -Destination $targetContextMenu -Force
    Write-InstallerLog "Deployed context_menu.exe." "INFO"

    # Copy logo.ico
    if (Test-Path $logoIco) {
        Copy-Item -Path $logoIco -Destination (Join-Path $InstallDir "logo.ico") -Force
        Write-InstallerLog "Deployed branding logo.ico." "INFO"
    }

    # ------------------------------------------------------------
    # 6. Configure System / User PATH Environment Variable
    # ------------------------------------------------------------
    Write-InstallerLog "Configuring system PATH environment variable..." "INFO"
    $targetBinPath = $targetAvicoreDir
    $envTarget = if ($Scope -eq "Machine") { [EnvironmentVariableTarget]::Machine } else { [EnvironmentVariableTarget]::User }

    $currentPath = [Environment]::GetEnvironmentVariable("Path", $envTarget)
    if (-not $currentPath) { $currentPath = "" }

    $pathEntries = $currentPath.Split(';', [System.StringSplitOptions]::RemoveEmptyEntries) | ForEach-Object { $_.Trim() }

    $normalizedTarget = [System.IO.Path]::GetFullPath($targetBinPath).TrimEnd('\')
    $legacyCandidates = @("C:\AVI Core", "C:\AVI Core\avicore", (Join-Path $env:LOCALAPPDATA "AVI Core"))

    $cleanedEntries = @()
    foreach ($entry in $pathEntries) {
        if (-not $entry) { continue }
        $norm = $entry.TrimEnd('\')
        try {
            $norm = [System.IO.Path]::GetFullPath($entry).TrimEnd('\')
        } catch {}

        if ($legacyCandidates -contains $norm) {
            Write-InstallerLog "Removing obsolete legacy path: $entry" "INFO"
        } elseif ($norm -ne $normalizedTarget) {
            $cleanedEntries += $entry
        }
    }

    # Add the target path cleanly
    $newPathEntries = $cleanedEntries + $targetBinPath
    $newPath = $newPathEntries -join ';'
    [Environment]::SetEnvironmentVariable("Path", $newPath, $envTarget)

    # Update current session PATH
    $sessionEntries = ($env:Path).Split(';', [System.StringSplitOptions]::RemoveEmptyEntries) | Where-Object {
        $p = $_.TrimEnd('\')
        -not ($legacyCandidates -contains $p) -and ($p -ne $normalizedTarget)
    }
    $env:Path = ($targetBinPath + ";" + ($sessionEntries -join ';'))
    Write-InstallerLog "Configured $Scope PATH with '$targetBinPath'." "SUCCESS"

    # Broadcast environment variable update to Windows shell
    try {
        if (-not ([System.Management.Automation.PSTypeName]'Win32EnvBroadcaster').Type) {
            Add-Type -Namespace Win32 -Name Win32EnvBroadcaster -MemberDefinition @"
[System.Runtime.InteropServices.DllImport("user32.dll", SetLastError = true, CharSet = System.Runtime.InteropServices.CharSet.Auto)]
public static extern System.IntPtr SendMessageTimeout(
    System.IntPtr hWnd,
    uint Msg,
    System.UIntPtr wParam,
    string lParam,
    uint fuFlags,
    uint uTimeout,
    out System.UIntPtr lpdwResult
);
"@
        }
        $result = [System.UIntPtr]::Zero
        [Win32.Win32EnvBroadcaster]::SendMessageTimeout([System.IntPtr]0xFFFF, 0x001A, [System.UIntPtr]::Zero, "Environment", 2, 2000, [ref]$result) | Out-Null
    } catch {
        # Non-fatal if broadcast fails
    }

    # ------------------------------------------------------------
    # 7. Register Windows Explorer Context Menu
    # ------------------------------------------------------------
    Write-InstallerLog "Registering Windows Explorer right-click context menu..." "INFO"
    $regProcess = Start-Process -FilePath $targetContextMenu -ArgumentList "register", "--silent" -Wait -PassThru -NoNewWindow
    if ($regProcess.ExitCode -ne 0) {
        Write-InstallerLog "Context menu registration returned non-zero code ($($regProcess.ExitCode))." "WARNING"
    } else {
        Write-InstallerLog "Context menu registered successfully." "SUCCESS"
    }

    # ------------------------------------------------------------
    # 8. Post-Install Verification
    # ------------------------------------------------------------
    Write-InstallerLog "Running self-diagnostic verification on installed binaries..." "INFO"
    $installedAvicore = Join-Path $targetAvicoreDir "avicore.exe"
    $verifyRun = Start-Process -FilePath $installedAvicore -ArgumentList "--help" -Wait -PassThru -NoNewWindow
    if ($verifyRun.ExitCode -ne 0) {
        Write-InstallerLog "Warning: Self-diagnostic returned exit code $($verifyRun.ExitCode)." "WARNING"
    } else {
        Write-InstallerLog "Verified: avicore.exe responded correctly to --help." "SUCCESS"
    }

    Exit-Installer 0 "AVI Core is now installed and ready to use!`n  - CLI Command:     avicore`n  - Context Menu:    Right-click any supported media file in File Explorer`n  - Installed to:    $InstallDir"

} catch {
    Exit-Installer 1 "An unexpected error occurred during installation: $_"
}
