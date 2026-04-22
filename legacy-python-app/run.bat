@echo off
REM WhatsApp Message OS - Quick Start Script for Windows

echo ========================================
echo  WhatsApp Message OS - Quick Launcher
echo ========================================
echo.

REM Check if venv exists
if not exist "venv\" (
    echo [!] Virtual environment not found.
    echo [*] Creating virtual environment...
    python -m venv venv
    if errorlevel 1 (
        echo [ERROR] Failed to create virtual environment
        echo Make sure Python 3.8+ is installed and in PATH
        pause
        exit /b 1
    )
)

REM Activate venv
echo [*] Activating virtual environment...
call venv\Scripts\activate.bat

REM Check if required packages are installed
echo [*] Checking dependencies...
pip show customtkinter > nul 2>&1
if errorlevel 1 (
    echo [!] Dependencies not found. Installing from requirements.txt...
    pip install -r requirements.txt
    if errorlevel 1 (
        echo [ERROR] Failed to install dependencies
        pause
        exit /b 1
    )
)

REM Run the application
echo [*] Starting WhatsApp Message OS...
python main.py

REM Keep window open if there's an error
if errorlevel 1 (
    echo.
    echo [ERROR] Application failed to start
    pause
)
