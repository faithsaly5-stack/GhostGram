@echo off
chcp 65001 >nul
title GhostGram PRO
cd /d "%~dp0"

if not exist ".env" (
    echo ==================================================
    echo ⚙️ Configuration file .env not found.
    echo Launching First-Time Setup Wizard...
    echo ==================================================
    echo.
    python setup.py
    if not exist ".env" (
        echo.
        echo [ERROR] Setup was cancelled or failed.
        pause
        exit /b 1
    )
)

echo ==================================================
echo   🚀 Starting GhostGram PRO Locally...
echo ==================================================
echo.
python main.py
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [ERROR] Bot stopped with an error code %ERRORLEVEL%.
)
pause
