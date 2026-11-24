@echo off
setlocal
cd /d "%~dp0"

where pythonw >nul 2>&1
if %errorlevel%==0 (
    start "" pythonw main.py %*
    exit /b 0
)

where python >nul 2>&1
if %errorlevel%==0 (
    start "" python main.py %*
    exit /b 0
)

echo [HATA] Python bulunamadi! Lutfen Python 3.9+ kurup PATH'e ekleyin.
pause
exit /b 1
