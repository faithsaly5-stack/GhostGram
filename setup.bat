@echo off
chcp 65001 >nul
title GhostGram First Time Setup
cd /d "%~dp0"
python setup.py
pause
