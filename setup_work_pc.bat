@echo off
REM ======================================================================
REM  Helios PRD - Work PC Setup Script
REM  Sets up Python virtual environment and installs all dependencies
REM ======================================================================

setlocal
cd /d "%~dp0"

echo ======================================================================
echo   HELIOS PRD - WORK PC AUTOMATION SETUP
echo ======================================================================
echo.

REM 1. Check Python
where python >nul 2>nul
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed or not in PATH.
    echo Please install Python 3.10+ from python.org or your company software portal.
    pause
    exit /b 1
)

echo [1/4] Found Python:
python --version

REM 2. Create virtual environment if not present
if not exist ".venv" (
    echo [2/4] Creating virtual environment (.venv)...
    python -m venv .venv
    if %errorlevel% neq 0 (
        echo [ERROR] Failed to create virtual environment.
        pause
        exit /b 1
    )
) else (
    echo [2/4] Virtual environment (.venv) already exists.
)

REM 3. Install packages
echo [3/4] Installing required dependencies (playwright, openpyxl, pytest)...
call .venv\Scripts\activate.bat
python -m pip install --upgrade pip
python -m pip install playwright openpyxl pytest
if %errorlevel% neq 0 (
    echo [ERROR] Failed to install packages via pip.
    pause
    exit /b 1
)

REM 4. Install Playwright browser
echo [4/4] Installing Playwright Chromium browser binary...
python -m playwright install chromium
if %errorlevel% neq 0 (
    echo [ERROR] Failed to install Playwright browser binaries.
    pause
    exit /b 1
)

echo.
echo ======================================================================
echo   SETUP COMPLETE!
echo   You can now:
echo     - Double-click 'run_launcher.bat' to open the Automation Launcher
echo     - Double-click 'start_chrome_sso.bat' to launch Chrome for SSO
echo ======================================================================
echo.
pause
