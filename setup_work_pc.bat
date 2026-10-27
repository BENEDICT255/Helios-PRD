@echo off
setlocal
cd /d "%~dp0"

echo ================================================================
echo   HELIOS PRD AUTOMATION - WORK PC SETUP
echo ================================================================
echo.

REM Prefer the Python launcher; it avoids the broken WindowsApps alias.
where py >nul 2>nul
if not errorlevel 1 (
    set "PY_CMD=py -3"
) else (
    where python >nul 2>nul
    if errorlevel 1 (
        echo [ERROR] Python 3 was not found. Install Python 3.10+ from your company software portal.
        pause
        exit /b 1
    )
    set "PY_CMD=python"
)

if not exist ".venv\Scripts\python.exe" (
    echo [1/4] Creating project environment...
    %PY_CMD% -m venv .venv
    if errorlevel 1 goto :failed
) else (
    echo [1/4] Using existing project environment.
)

echo [2/4] Ensuring pip is available...
call .venv\Scripts\python.exe -m ensurepip --upgrade
if errorlevel 1 goto :failed

echo [3/4] Installing project packages...
call .venv\Scripts\python.exe -m pip install --upgrade pip
if errorlevel 1 goto :failed
call .venv\Scripts\python.exe -m pip install playwright openpyxl pytest
if errorlevel 1 goto :failed

echo [4/4] Installing Playwright Chromium...
REM Use the Windows certificate store on managed work PCs with TLS inspection.
set "NODE_USE_SYSTEM_CA=1"
call .venv\Scripts\python.exe -m playwright install chromium
if errorlevel 1 goto :failed

echo.
echo Setup complete. Run run_tests.bat, then run_launcher.bat.
pause
exit /b 0

:failed
echo.
echo [ERROR] Setup stopped. Read the error above and contact IT if downloads are blocked.
pause
exit /b 1
