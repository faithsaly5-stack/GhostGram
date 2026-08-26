@echo off
chcp 65001 >nul
title GhostGram VPS Deployer
cd /d "%~dp0"

echo ==================================================
echo   GhostGram VPS Deployer
echo ==================================================
echo.

setlocal enabledelayedexpansion

:: Parse default .env for configuration
set "VPS_IP="
set "SSH_USER="
set "SSH_PORT="

if exist "profiles\default\.env" (
    for /f "usebackq tokens=1,2 delims==" %%A in ("profiles\default\.env") do (
        if "%%A"=="VPS_IP" set VPS_IP=%%B
        if "%%A"=="SSH_USER" set SSH_USER=%%B
        if "%%A"=="SSH_PORT" set SSH_PORT=%%B
    )
)

if "!VPS_IP!"=="" set VPS_IP=127.0.0.1
if "!VPS_IP!"=="YOUR_VPS_IP" set VPS_IP=127.0.0.1

if "!VPS_IP!"=="127.0.0.1" (
    echo [SETUP] VPS credentials not configured!
    echo Let's configure your VPS settings now.
    set /p NEW_VPS_IP="Enter your VPS IP address: "
    set /p NEW_SSH_USER="Enter your SSH username [root]: "
    if "!NEW_SSH_USER!"=="" set NEW_SSH_USER=root
    set /p NEW_SSH_PORT="Enter your SSH port [22]: "
    if "!NEW_SSH_PORT!"=="" set NEW_SSH_PORT=22
    
    set VPS_IP=!NEW_VPS_IP!
    set SSH_USER=!NEW_SSH_USER!
    set SSH_PORT=!NEW_SSH_PORT!
    
    if not exist "profiles\default" mkdir "profiles\default"
    
    (
        echo.
        echo # Deployment Settings Global VPS Config
        echo VPS_IP=!VPS_IP!
        echo SSH_USER=!SSH_USER!
        echo SSH_PORT=!SSH_PORT!
    ) >> "profiles\default\.env"
    echo  VPS credentials saved to profiles\default\.env!
    echo.
)
set "PAYLOAD=teleagent_deploy.zip"

if exist "!PAYLOAD!" del /f /q "!PAYLOAD!"

echo [1/3] Compressing files locally...
tar -a -c -f "!PAYLOAD!" --exclude=*.json --exclude=*.session --exclude=*.session-journal *.py requirements.txt profiles
if !ERRORLEVEL! NEQ 0 (
    echo [ERROR] Failed to compress files.
    goto :end
)
echo Local zip package created successfully!
echo.

echo [2/3] Uploading payload to VPS...
echo (If prompted for a password, please right-click to paste)
scp -P !SSH_PORT! "!PAYLOAD!" deploy.sh "!SSH_USER!@!VPS_IP!:/tmp/"
if !ERRORLEVEL! NEQ 0 (
    echo [ERROR] SCP upload failed.
    goto :end
)
if exist "!PAYLOAD!" del /f /q "!PAYLOAD!"
echo Files uploaded to VPS successfully!
echo.

echo [3/3] Extracting and restarting service on VPS...
echo (If prompted for a password, please right-click to paste)
ssh -t -p !SSH_PORT! "!SSH_USER!@!VPS_IP!" "bash /tmp/deploy.sh"
if !ERRORLEVEL! NEQ 0 (
    echo [ERROR] SSH deployment failed.
    goto :end
)

echo.
echo Deployment finished successfully!

:end
echo.
echo ==================================================
echo Deployment process finished.
echo ==================================================
pause
cmd /k
