@echo off
title Pixera Countdowns - PRODUCTION
echo ---------------------------------------------------------
echo STAGE: Starting PRODUCTION Environment
echo ---------------------------------------------------------
cd /d "%~dp0"
docker-compose --profile prod up -d
echo.
echo ✅ SUCCESS: System is running in the background.
echo 🌐 Access at: http://localhost:3000
echo.
pause