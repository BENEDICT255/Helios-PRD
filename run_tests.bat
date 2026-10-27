@echo off
setlocal
cd /d "%~dp0"

if exist ".venv\Scripts\python.exe" (
    set "PYTHON_EXE=.venv\Scripts\python.exe"
) else (
    set "PYTHON_EXE=python"
)

echo [*] Running automated test suite...
echo.
"%PYTHON_EXE%" -m pytest -v
set "TEST_EXIT=%ERRORLEVEL%"
echo.
if not "%TEST_EXIT%"=="0" echo [ERROR] Tests failed.
pause
exit /b %TEST_EXIT%
