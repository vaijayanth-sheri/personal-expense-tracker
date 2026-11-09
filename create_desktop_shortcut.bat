@echo off
setlocal
cd /d "%~dp0"

echo Creating Desktop Shortcut for Personal Expense Tracker...

set "TARGET_SCRIPT=%~dp0run_app.vbs"
set "ICON_PATH=%SystemRoot%\System32\shell32.dll,303"

powershell -Command "$ws = New-Object -ComObject WScript.Shell; $s = $ws.CreateShortcut([Environment]::GetFolderPath('Desktop') + '\Personal Expense Tracker.lnk'); $s.TargetPath = 'wscript.exe'; $s.Arguments = '\"%TARGET_SCRIPT%\"'; $s.WorkingDirectory = '%~dp0'; $s.IconLocation = 'shell32.dll, 303'; $s.Save()"

echo [SUCCESS] Desktop Shortcut created on your Desktop!
echo You can now simply double-click "Personal Expense Tracker" on your Desktop to launch your app.
pause
