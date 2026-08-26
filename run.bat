@echo off
chcp 65001 >nul
title GhostGram PRO - 1-Click Launcher
cd /d "%~dp0"

where python >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed or not in your system PATH!
    echo Please download and install Python from https://python.org
    echo IMPORTANT: Make sure to check "Add python.exe to PATH" during installation.
    pause
    exit /b 1
)

python launcher.py
pause
