# ============================================================
# POWERSHELL BUILD AUTOMATION FOR AVI CORE
# ============================================================

$ErrorActionPreference = "Stop"

# Determine script directory reliably regardless of execution working directory
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
if (-not $ScriptDir) {
    $ScriptDir = $PSScriptRoot
}
if (-not $ScriptDir) {
    $ScriptDir = Get-Location
}
$ProjectRoot = [System.IO.Path]::GetFullPath($ScriptDir)
Set-Location $ProjectRoot

function Exit-Build($exitCode, $message) {
    if ($exitCode -ne 0) {
        Write-Host "`n[ERROR] $message" -ForegroundColor Red
    } else {
        Write-Host "`n[SUCCESS] $message" -ForegroundColor Green
    }
    if ($Host.Name -eq "ConsoleHost" -and -not $env:CI -and -not $args[0]) {
        # Only pause if interactive console and not called from CLI pipeline
    }
    exit $exitCode
}

try {
    Write-Host "=== AVI Core Build Pipeline ===" -ForegroundColor Cyan
    Write-Host "Project Root: $ProjectRoot`n" -ForegroundColor DarkGray

    # Step 0A: Check Python & Required Tools
    Write-Host "=== Step 0: Checking Environment Dependencies ===" -ForegroundColor Cyan
    if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
        throw "Python executable was not found in system PATH. Please install Python 3.9+."
    }

    $ffmpegSource = Join-Path $ProjectRoot "bin\ffmpeg.exe"
    if (-not (Test-Path $ffmpegSource)) {
        throw "Missing engine binary: $ffmpegSource does not exist. Please place ffmpeg.exe in the bin/ directory."
    }

    $logoIco = Join-Path $ProjectRoot "logo.ico"
    if (-not (Test-Path $logoIco)) {
        throw "Verification failed: logo.ico does not exist at $logoIco."
    }

    Write-Host "Verifying logo.ico icon resources..." -ForegroundColor DarkGray
    $icoVerification = python -c @"
from PIL import Image
try:
    img = Image.open(r'$logoIco')
    if img.format != 'ICO':
        print('ERROR: logo.ico is not in ICO format')
        exit(1)
    sizes = img.ico.sizes()
    required = {(16, 16), (32, 32), (48, 48), (256, 256)}
    missing = required - sizes
    if (missing):
        print(f'ERROR: logo.ico is missing required sizes: {missing}')
        exit(2)
    print('OK')
except Exception as e:
    print(f'ERROR: Failed to parse logo.ico: {e}')
    exit(3)
"@
    if ($icoVerification -ne "OK") {
        throw "logo.ico validation failed: $icoVerification"
    }
    Write-Host "Branding and engine dependencies verified successfully.`n" -ForegroundColor Green

    # Step 1: Cleaning previous build artifacts
    Write-Host "=== Step 1: Cleaning previous build artifacts ===" -ForegroundColor Cyan
    $buildDir = Join-Path $ProjectRoot "build"
    $distDir = Join-Path $ProjectRoot "dist"

    if (Test-Path $buildDir) {
        Remove-Item -Path $buildDir -Recurse -Force
    }
    # Clean subdirectories in dist except the installer executable if present
    $distAvicore = Join-Path $distDir "avicore"
    $distContextMenu = Join-Path $distDir "context_menu.exe"
    if (Test-Path $distAvicore) {
        Remove-Item -Path $distAvicore -Recurse -Force
    }
    if (Test-Path $distContextMenu) {
        Remove-Item -Path $distContextMenu -Force
    }
    Write-Host "Clean completed successfully.`n" -ForegroundColor Green

    # Step 2: Compiling avicore.exe (--onedir)
    Write-Host "=== Step 2: Compiling avicore.exe (--onedir) ===" -ForegroundColor Cyan
    $appPy = Join-Path $ProjectRoot "app.py"
    python -m PyInstaller --onedir --clean --name avicore --icon="$logoIco" --add-binary "$ffmpegSource;." "$appPy"
    if ($LASTEXITCODE -ne 0) {
        throw "Failed to compile avicore.exe via PyInstaller."
    }
    Write-Host "avicore.exe compiled successfully.`n" -ForegroundColor Green

    # Workaround for PyInstaller 6+ _internal folder placement of binaries
    $internalFfmpeg = Join-Path $distDir "avicore\_internal\ffmpeg.exe"
    $rootFfmpeg = Join-Path $distDir "avicore\ffmpeg.exe"
    if (Test-Path $internalFfmpeg) {
        Write-Host "Copying ffmpeg.exe from _internal to root avicore folder..." -ForegroundColor DarkGray
        Copy-Item -Path $internalFfmpeg -Destination $rootFfmpeg -Force
    }

    # Step 3: Compiling context_menu.exe (--onefile --noconsole)
    Write-Host "=== Step 3: Compiling context_menu.exe (--onefile --noconsole) ===" -ForegroundColor Cyan
    $contextMenuPy = Join-Path $ProjectRoot "context_menu.py"
    python -m PyInstaller --onefile --noconsole --clean --name context_menu --icon="$logoIco" "$contextMenuPy"
    if ($LASTEXITCODE -ne 0) {
        throw "Failed to compile context_menu.exe via PyInstaller."
    }
    Write-Host "context_menu.exe compiled successfully.`n" -ForegroundColor Green

    # Step 4: Verifying build outputs
    Write-Host "=== Step 4: Verifying build outputs ===" -ForegroundColor Cyan
    $contextMenuExe = Join-Path $distDir "context_menu.exe"
    $aviCoreExe = Join-Path $distDir "avicore\avicore.exe"
    $ffmpegExe = Join-Path $distDir "avicore\ffmpeg.exe"

    if (-not (Test-Path $contextMenuExe)) {
        throw "Verification failed: $contextMenuExe does not exist."
    }
    if (-not (Test-Path $aviCoreExe)) {
        throw "Verification failed: $aviCoreExe does not exist."
    }
    if (-not (Test-Path $ffmpegExe)) {
        throw "Verification failed: $ffmpegExe does not exist."
    }

    Write-Host "Checking if context_menu.exe contains icon resource..." -ForegroundColor DarkGray
    $hasIconContext = python -c "import ctypes; print(ctypes.windll.user32.PrivateExtractIconsW(r'$contextMenuExe', 0, 16, 16, None, None, 0, 0))"
    if ([int]$hasIconContext -le 0) {
        throw "Verification failed: context_menu.exe does not contain any icon resources."
    }

    Write-Host "Checking if avicore.exe contains icon resource..." -ForegroundColor DarkGray
    $hasIconAvicore = python -c "import ctypes; print(ctypes.windll.user32.PrivateExtractIconsW(r'$aviCoreExe', 0, 16, 16, None, None, 0, 0))"
    if ([int]$hasIconAvicore -le 0) {
        throw "Verification failed: avicore.exe does not contain any icon resources."
    }

    Write-Host "`nAll build outputs verified successfully!" -ForegroundColor Green
    Write-Host "  - $contextMenuExe" -ForegroundColor Yellow
    Write-Host "  - $aviCoreExe" -ForegroundColor Yellow
    Write-Host "  - $ffmpegExe" -ForegroundColor Yellow

} catch {
    Write-Host "`n[BUILD FAILURE] $_" -ForegroundColor Red
    if ($Host.Name -eq "ConsoleHost" -and -not $env:CI) {
        Write-Host "`nPress Enter to exit..." -ForegroundColor Yellow
        [void][System.Console]::ReadLine()
    }
    exit 1
}
