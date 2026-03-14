# WhatsApp Message OS - Build Script for PyInstaller
# PowerShell script to automate the .exe building process

Write-Host "========================================" -ForegroundColor Cyan
Write-Host " WhatsApp Message OS - Build Script" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check if venv exists and activate
if (Test-Path "venv") {
    Write-Host "[*] Activating virtual environment..." -ForegroundColor Yellow
    & ".\venv\Scripts\Activate.ps1"
} else {
    Write-Host "[!] Virtual environment not found" -ForegroundColor Red
    Write-Host "[*] Creating virtual environment..." -ForegroundColor Yellow
    python -m venv venv
    & ".\venv\Scripts\Activate.ps1"
}

# Install/upgrade dependencies
Write-Host "[*] Checking dependencies..." -ForegroundColor Yellow
$output = pip list 2>$null
if ($output -notcontains "pyinstaller") {
    Write-Host "[*] Installing dependencies from requirements.txt..." -ForegroundColor Yellow
    pip install -r requirements.txt
}

# Ask user for build option
Write-Host ""
Write-Host "Select build option:" -ForegroundColor Cyan
Write-Host "1) Folder distribution (RECOMMENDED - ~500MB, faster startup)" -ForegroundColor White
Write-Host "2) Single file (.exe - ~500MB, more portable)" -ForegroundColor White
Write-Host "3) Debug build (with console window for troubleshooting)" -ForegroundColor White
Write-Host ""
$choice = Read-Host "Enter choice (1-3)"

# Clean previous builds
Write-Host ""
Write-Host "[*] Cleaning previous build artifacts..." -ForegroundColor Yellow
Remove-Item -Path "build" -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item -Path "dist" -Recurse -Force -ErrorAction SilentlyContinue

# Build based on choice
switch ($choice) {
    "1" {
        Write-Host "[*] Building folder distribution..." -ForegroundColor Yellow
        & pyinstaller WhatsApp_Message_OS.spec
    }
    "2" {
        Write-Host "[*] Building single-file executable..." -ForegroundColor Yellow
        & pyinstaller --onefile WhatsApp_Message_OS.spec
    }
    "3" {
        Write-Host "[*] Building debug version with console..." -ForegroundColor Yellow
        & pyinstaller --name="WhatsApp_Message_OS" ^
            --console ^
            --add-data "config.json:." ^
            --hidden-import=customtkinter ^
            --hidden-import=pandas ^
            --hidden-import=openpyxl ^
            --hidden-import=selenium ^
            --hidden-import=webdriver_manager ^
            main.py
    }
    default {
        Write-Host "[ERROR] Invalid choice" -ForegroundColor Red
        exit 1
    }
}

# Check if build was successful
if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Green
    Write-Host " Build Successful!" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Green
    
    # Show build output information
    if ((Test-Path "dist\WhatsApp_Message_OS") -or (Test-Path "dist\WhatsApp_Message_OS.exe")) {
        Get-ChildItem -Path "dist" -Recurse | Measure-Object -Sum | ForEach-Object {
            Write-Host "[*] Total files: $($_.Count)" -ForegroundColor Green
        }
        
        if (Test-Path "dist\WhatsApp_Message_OS.exe") {
            $size = (Get-Item "dist\WhatsApp_Message_OS.exe").Length / 1MB
            Write-Host "[*] Executable size: $([Math]::Round($size, 2)) MB" -ForegroundColor Green
        }
        
        Write-Host ""
        Write-Host "Your executable is ready in the 'dist' folder!" -ForegroundColor Green
        Write-Host ""
        
        # Offer to open dist folder
        $openDist = Read-Host "Open dist folder? (Y/n)"
        if ($openDist -ne "n" -and $openDist -ne "N") {
            explorer.exe ".\dist"
        }
    }
} else {
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Red
    Write-Host " Build Failed!" -ForegroundColor Red
    Write-Host "========================================" -ForegroundColor Red
    Write-Host "[ERROR] Build exited with code: $LASTEXITCODE" -ForegroundColor Red
    exit 1
}
