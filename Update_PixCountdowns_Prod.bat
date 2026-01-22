@echo off
title Pixera Countdowns - UPDATE PRODUCTION
cls

echo ---------------------------------------------------------
echo 🔄 STAGE: Rebuilding Production with latest code changes...
echo ---------------------------------------------------------

:: Move to the directory where the script is located
cd /d "%~dp0"

:: --build forces Docker to re-examine the source code and create new images
:: -d runs the containers in the background (detached mode)
docker-compose --profile prod up -d --build

echo.
echo ---------------------------------------------------------
echo ✅ SUCCESS: Production has been updated and restarted!
echo 🌐 Access at: http://localhost:3000
echo ---------------------------------------------------------
echo.

pause