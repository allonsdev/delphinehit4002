@echo off

REM === Get current local IP ===
for /f "tokens=2 delims=:" %%a in ('ipconfig ^| findstr /C:"IPv4 Address"') do (
    set IP=%%a
    goto :ipfound
)

:ipfound
set IP=%IP: =%
echo Your IP is %IP%

REM === Start Django server on all interfaces ===
start "" /B python manage.py runserver 0.0.0.0:8000

REM === Wait until server is reachable ===
:waitloop
curl -s http://%IP%:8000 >nul
if errorlevel 1 (
    timeout /t 1 >nul
    goto waitloop
)

REM === Open in Chrome using LAN IP ===
start chrome http://%IP%:8000

exit