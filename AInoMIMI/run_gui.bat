@echo off
chcp 65001 > nul
echo ========================================================
echo  AINOMIMI - Music Analysis Pipeline (GUI Launcher)
echo ========================================================
echo.

python --version > nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python not found! Please install Python 3.10+.
    pause
    exit /b
)

echo Starting GUI...
python gui.py

if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Application crashed or closed unexpectedly.
    pause
)
