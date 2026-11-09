@echo off
setlocal
cd /d "%~dp0"

:: Start python server quietly in the background if not already running
netstat -ano | findstr ":5055 " >nul
if %ERRORLEVEL% NEQ 0 (
    start /B python server.py
    :: Wait a brief moment for server bind
    timeout /t 1 /nobreak >nul
)

:: Check for Edge or Chrome to run in desktop app mode
set "APP_URL=http://127.0.0.1:5055"
set "EDGE_PATH=%ProgramFiles(x86)%\Microsoft\Edge\Application\msedge.exe"
if not exist "%EDGE_PATH%" set "EDGE_PATH=%ProgramFiles%\Microsoft\Edge\Application\msedge.exe"

set "CHROME_PATH=%ProgramFiles%\Google\Chrome\Application\chrome.exe"
if not exist "%CHROME_PATH%" set "CHROME_PATH=%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe"

if exist "%EDGE_PATH%" (
    start "" "%EDGE_PATH%" --app="%APP_URL%" --window-size=1180,820
) else if exist "%CHROME_PATH%" (
    start "" "%CHROME_PATH%" --app="%APP_URL%" --window-size=1180,820
) else (
    start "" "%APP_URL%"
)

exit
