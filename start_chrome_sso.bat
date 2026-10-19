@echo off
REM ======================================================================
REM  Helios PRD - Start Chrome with Remote Debugging for SSO Session
REM  Launches Chrome on port 9222 so Python can attach to your active tab.
REM ======================================================================

setlocal
cd /d "%~dp0"

echo ======================================================================
echo   HELIOS PRD - CHROME SSO LAUNCHER (REMOTE DEBUGGING PORT 9222)
echo ======================================================================
echo.

set "CHROME_BIN="
if exist "C:\Program Files\Google\Chrome\Application\chrome.exe" set "CHROME_BIN=C:\Program Files\Google\Chrome\Application\chrome.exe"
if not defined CHROME_BIN (
    if exist "C:\Program Files (x86)\Google\Chrome\Application\chrome.exe" set "CHROME_BIN=C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"
)
if not defined CHROME_BIN (
    if exist "%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe" set "CHROME_BIN=%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe"
)

if not defined CHROME_BIN (
    echo [ERROR] Google Chrome was not found in standard paths.
    echo Please launch Chrome manually from command line with:
    echo   chrome.exe --remote-debugging-port=9222
    pause
    exit /b 1
)

echo [*] Chrome found at: "%CHROME_BIN%"
echo [*] Launching Chrome on debugging port 9222...
echo.
echo [INSTRUCTIONS]
echo   1. In the Chrome window that opens, log into Helios PRD using your SSO / access credentials.
echo   2. Navigate to your specific Site Material Request ticket (Lines tab).
echo   3. Leave that Chrome tab open.
echo   4. Double-click 'run_launcher.bat', select 'Attach to Active Chrome / SSO Session', and click Run.
echo.

start "" "%CHROME_BIN%" --remote-debugging-port=9222 --user-data-dir="%TEMP%\chrome_helios_profile"
