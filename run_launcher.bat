@echo off
REM ======================================================================
REM  Helios PRD - Material Lines Automation Launcher
REM  Opens the desktop popup window to download template, select file,
REM  input target ticket URL, and start automation.
REM ======================================================================

setlocal
cd /d "%~dp0"

if exist ".venv\Scripts\python.exe" (
    set "PYTHON_EXE=.venv\Scripts\python.exe"
) else (
    set "PYTHON_EXE=python"
)

echo [*] Launching Helios PRD Automation window...
start "" "%PYTHON_EXE%" launcher.py
