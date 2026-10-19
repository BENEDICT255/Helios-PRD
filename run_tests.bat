@echo off
REM ======================================================================
REM  Helios PRD - Run Automated Pytest Test Suite
REM ======================================================================

setlocal
cd /d "%~dp0"

if exist ".venv\Scripts\pytest.exe" (
    set "PYTEST_EXE=.venv\Scripts\pytest.exe"
) else (
    set "PYTEST_EXE=pytest"
)

echo [*] Running automated test suite...
echo.

"%PYTEST_EXE%" -v

echo.
pause
