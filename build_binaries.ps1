# ============================================================
# POWERSHELL BUILD AUTOMATION FOR AVI CORE
# ============================================================

$ErrorActionPreference = "Stop"

Write-Host "=== Step 0: Verifying branding source ===" -ForegroundColor Cyan
if (-not (Test-Path "logo.ico")) {
    Write-Error "Verification failed: logo.ico does not exist in the project root."
}
$icoVerification = python -c "
from PIL import Image
try:
    img = Image.open('logo.ico')
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
"
if ($icoVerification -ne "OK") {
    Write-Error "logo.ico validation failed: $icoVerification"
}
Write-Host "logo.ico verified successfully (contains 16x16, 32x32, 48x48, 256x256).`n" -ForegroundColor Green

Write-Host "=== Step 1: Cleaning previous build artifacts ===" -ForegroundColor Cyan
if (Test-Path "build") {
    Remove-Item -Path "build" -Recurse -Force
}
if (Test-Path "dist") {
    Remove-Item -Path "dist" -Recurse -Force
}
Write-Host "Clean completed successfully.`n" -ForegroundColor Green

Write-Host "=== Step 2: Compiling avicore.exe (--onedir) ===" -ForegroundColor Cyan
python -m PyInstaller --onedir --clean --name avicore --icon=logo.ico --add-binary "bin/ffmpeg.exe;." app.py
if ($LASTEXITCODE -ne 0) {
    Write-Error "Failed to compile avicore.exe"
}
Write-Host "avicore.exe compiled successfully.`n" -ForegroundColor Green

# Workaround for PyInstaller 6+ _internal folder placement of binaries
$internalFfmpeg = "dist\avicore\_internal\ffmpeg.exe"
$rootFfmpeg = "dist\avicore\ffmpeg.exe"
if (Test-Path $internalFfmpeg) {
    Write-Host "Copying ffmpeg.exe from _internal to root avicore folder..." -ForegroundColor Cyan
    Copy-Item -Path $internalFfmpeg -Destination $rootFfmpeg -Force
}

Write-Host "=== Step 3: Compiling context_menu.exe (--onefile --noconsole) ===" -ForegroundColor Cyan
python -m PyInstaller --onefile --noconsole --clean --name context_menu --icon=logo.ico context_menu.py

if ($LASTEXITCODE -ne 0) {
    Write-Error "Failed to compile context_menu.exe"
}
Write-Host "context_menu.exe compiled successfully.`n" -ForegroundColor Green

Write-Host "=== Step 4: Verifying build outputs ===" -ForegroundColor Cyan

$contextMenuExe = "dist\context_menu.exe"
$aviCoreExe = "dist\avicore\avicore.exe"
$ffmpegExe = "dist\avicore\ffmpeg.exe"

if (-not (Test-Path $contextMenuExe)) {
    Write-Error "Verification failed: $contextMenuExe does not exist."
}
if (-not (Test-Path $aviCoreExe)) {
    Write-Error "Verification failed: $aviCoreExe does not exist."
}
if (-not (Test-Path $ffmpegExe)) {
    Write-Error "Verification failed: $ffmpegExe does not exist."
}

Write-Host "Checking if context_menu.exe contains icon resource..." -ForegroundColor Cyan
$hasIconContext = python -c "import ctypes; print(ctypes.windll.user32.PrivateExtractIconsW(r'$contextMenuExe', 0, 16, 16, None, None, 0, 0))"
if ([int]$hasIconContext -le 0) {
    Write-Error "Verification failed: context_menu.exe does not contain any icon resources."
}
Write-Host "context_menu.exe icon verified.`n" -ForegroundColor Green

Write-Host "Checking if avicore.exe contains icon resource..." -ForegroundColor Cyan
$hasIconAvicore = python -c "import ctypes; print(ctypes.windll.user32.PrivateExtractIconsW(r'$aviCoreExe', 0, 16, 16, None, None, 0, 0))"
if ([int]$hasIconAvicore -le 0) {
    Write-Error "Verification failed: avicore.exe does not contain any icon resources."
}
Write-Host "avicore.exe icon verified.`n" -ForegroundColor Green

Write-Host "All build outputs verified successfully!" -ForegroundColor Green
Write-Host "  - $contextMenuExe" -ForegroundColor Yellow
Write-Host "  - $aviCoreExe" -ForegroundColor Yellow
Write-Host "  - $ffmpegExe" -ForegroundColor Yellow
