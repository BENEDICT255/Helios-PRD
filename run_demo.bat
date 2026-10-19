@echo off
REM ======================================================================
REM  Helios PRD - Excel-Driven Material-Line Entry Automation Demo
REM  Launches the automation visibly in a Chromium browser
REM ======================================================================

setlocal
cd /d "%~dp0"

echo ======================================================================
echo   HELIOS PRD - LOCAL MATERIAL-LINE ENTRY AUTOMATION
echo   [DEMO ONLY - NOT CONNECTED TO PRODUCTION]
echo ======================================================================

if exist ".venv\Scripts\python.exe" (
    set "PYTHON_EXE=.venv\Scripts\python.exe"
) else (
    set "PYTHON_EXE=python"
)

echo [*] Using Python: %PYTHON_EXE%
echo [*] Launching live automation in visible browser window...
echo.

"%PYTHON_EXE%" main.py --slow-mo 300

echo.
echo ======================================================================
echo   Execution finished. Check reports/run_report.md for details.
echo ======================================================================
pause
