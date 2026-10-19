@echo off
REM ======================================================================
REM  Helios PRD - Run Automation in Dry-Run Mode
REM ======================================================================

setlocal
cd /d "%~dp0"

if exist ".venv\Scripts\python.exe" (
    set "PYTHON_EXE=.venv\Scripts\python.exe"
) else (
    set "PYTHON_EXE=python"
)

echo [*] Running dry-run validation (no lines saved)...
echo.

"%PYTHON_EXE%" main.py --dry-run

echo.
pause
