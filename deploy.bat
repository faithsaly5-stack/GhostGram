@echo off
chcp 65001 >nul
title GhostGram VPS Deployer
cd /d "%~dp0"

echo ==================================================
echo   GhostGram VPS Deployer
echo ==================================================
echo.

:: Parse .env file for configuration
for /f "usebackq tokens=1,2 delims==" %%A in (".env") do (
    if "%%A"=="VPS_IP" set VPS_IP=%%B
    if "%%A"=="SSH_USER" set SSH_USER=%%B
    if "%%A"=="SSH_PORT" set SSH_PORT=%%B
)

if "%VPS_IP%"=="" (
    echo [ERROR] VPS_IP not found in .env file!
    echo Please set VPS_IP, SSH_USER, and SSH_PORT in your .env file.
    goto :end
)
if "%VPS_IP%"=="YOUR_VPS_IP" (
    echo [ERROR] VPS_IP is not configured!
    echo Please replace YOUR_VPS_IP in your .env file with your actual server IP.
    goto :end
)
set "PAYLOAD=teleagent_deploy.zip"

if exist "%PAYLOAD%" del /f /q "%PAYLOAD%"

echo [1/3] Compressing files locally (skipping sessions for safety)...
tar -a -c -f "%PAYLOAD%" *.py personas requirements.txt .env
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Failed to compress files.
    goto :end
)
echo Local zip package created successfully!
echo.

echo [2/3] Uploading payload to VPS...
echo (If prompted for a password, please right-click to paste)
scp -P %SSH_PORT% "%PAYLOAD%" deploy.sh "%SSH_USER%@%VPS_IP%:/tmp/"
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] SCP upload failed.
    goto :end
)
if exist "%PAYLOAD%" del /f /q "%PAYLOAD%"
echo Files uploaded to VPS successfully!
echo.

echo [3/3] Extracting and restarting service on VPS...
echo (If prompted for a password, please right-click to paste)
ssh -t -p %SSH_PORT% "%SSH_USER%@%VPS_IP%" "bash /tmp/deploy.sh"
if %ERRORLEVEL% NEQ 0 (
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
