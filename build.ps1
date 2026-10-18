# PirateDrop build script
# Usage:  powershell -ExecutionPolicy Bypass -File build.ps1

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $root

Write-Host "==> Ensuring croc.exe is present at repo root..."
if (-not (Test-Path "croc.exe")) {
    throw "croc.exe not found at repo root. Download it from https://github.com/schollz/croc/releases"
}

Write-Host "==> Generating icon (only if missing)..."
if (-not (Test-Path "assets\icon.ico")) {
    $env:QT_QPA_PLATFORM = "offscreen"
    python scripts\generate_icon.py
} else {
    Write-Host "    assets\icon.ico already exists; leaving it untouched."
}

Write-Host "==> Cleaning previous build output..."
if (Test-Path "build") { Remove-Item -Recurse -Force "build" }
if (Test-Path "dist") { Remove-Item -Recurse -Force "dist" }

Write-Host "==> Running PyInstaller..."
pyinstaller app.spec --noconfirm

Write-Host ""
Write-Host "Done. Executable at: dist\PirateDrop.exe"
