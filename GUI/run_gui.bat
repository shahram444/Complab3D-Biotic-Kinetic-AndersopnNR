@echo off
REM Launch CompLaB Studio on Windows
REM Usage:  run_gui.bat              (normal)
REM         run_gui.bat --install    (install deps first)

cd /d "%~dp0"

if "%~1"=="--install" (
    echo Installing dependencies...
    pip install -r requirements.txt
    shift
)

python main.py %*
