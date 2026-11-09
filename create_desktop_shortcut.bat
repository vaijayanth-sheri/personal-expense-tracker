@echo off
setlocal
cd /d "%~dp0"

echo Updating Desktop Shortcut with custom Vault Icon...

set "TARGET_SCRIPT=%~dp0run_app.vbs"
set "ICON_FILE=%~dp0assets\icon.ico"

powershell -Command "$ws = New-Object -ComObject WScript.Shell; $s = $ws.CreateShortcut([Environment]::GetFolderPath('Desktop') + '\Personal Expense Tracker.lnk'); $s.TargetPath = 'wscript.exe'; $s.Arguments = '\"%TARGET_SCRIPT%\"'; $s.WorkingDirectory = '%~dp0'; $s.IconLocation = '%ICON_FILE%'; $s.Save()"

echo [SUCCESS] Desktop Shortcut updated with custom geometric vault icon!
exit /b 0
