@echo off
echo ^>^>^> Phase 1: Creating Python Virtual Environment
python -m venv venv
call venv\Scripts\activate.bat

echo ^>^>^> Phase 2: Installing Python Dependencies
python -m pip install --upgrade pip
pip install PyQt5 "requests[socks]" pysocks

echo ^>^>^> Phase 3: Fetching Xray-core for Windows (64-bit)
if not exist "bin" mkdir bin
powershell -Command "Invoke-WebRequest -Uri 'https://github.com/XTLS/Xray-core/releases/latest/download/Xray-windows-64.zip' -OutFile 'xray.zip'"
powershell -Command "Expand-Archive -Path 'xray.zip' -DestinationPath 'bin\' -Force"
del xray.zip

echo ^>^>^> Phase 4: Creating Desktop Shortcut
powershell -Command "$wshell = New-Object -ComObject WScript.Shell; $shortcut = $wshell.CreateShortcut('%USERPROFILE%\Desktop\Xray Client.lnk'); $shortcut.TargetPath = '%~dp0run.bat'; $shortcut.WorkingDirectory = '%~dp0'; $shortcut.IconLocation = '%~dp0venv\Scripts\pythonw.exe'; $shortcut.Save()"

echo ^>^>^> Installation Complete! 
echo A shortcut has been created on your Desktop.
pause
