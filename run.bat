@echo off
chcp 65001 >nul
title GhostGram PRO - 1-Click Launcher
cd /d "%~dp0"

echo ==================================================
echo   👻 GhostGram PRO - 1-Click Launcher
echo ==================================================
echo.

:: 1. Check Python
where python >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Python is not installed or not in your system PATH!
    echo Please download and install Python (3.10+) from https://python.org
    echo IMPORTANT: Make sure to check "Add python.exe to PATH" during installation.
    echo.
    pause
    exit /b 1
)

:: 2. Auto-Install Dependencies
echo [1/3] Checking requirements...
python -c "import telethon, google.genai, dotenv, psutil" >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo Installing required packages (one-time setup)...
    pip install -q -r requirements.txt
    if %ERRORLEVEL% NEQ 0 (
        echo [ERROR] Failed to install dependencies. Please check your internet connection.
        pause
        exit /b 1
    )
    echo Requirements verified!
)

:: 3. Check Configuration & Setup Wizard
if not exist ".env" (
    echo.
    echo [2/3] Configuration file (.env) not found.
    echo Launching First-Time Setup Wizard...
    echo.
    python setup.py
    if not exist ".env" (
        echo.
        echo [ERROR] Setup was cancelled or failed.
        pause
        exit /b 1
    )
)

:: 4. Check Telegram Login Session
set HAS_SESSION=
for %%f in (*.session) do set HAS_SESSION=1
if not defined HAS_SESSION (
    echo.
    echo [2/3] Telegram authentication required...
    python login.py
)

:: 5. Launch GhostGram
echo.
echo ==================================================
echo   🚀 Starting GhostGram PRO...
echo   (Keep this window open to keep your bot active)
echo ==================================================
echo.
python main.py
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [!] Bot stopped.
)
pause
