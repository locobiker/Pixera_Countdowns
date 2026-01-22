@echo off
title Pixera Countdowns - DEV MODE
echo ---------------------------------------------------------
echo STAGE: Starting DEVELOPMENT Environment (Hot Reload)
echo ---------------------------------------------------------
cd /d "%~dp0"
docker-compose --profile dev up -d
echo.
echo 🛠️  SUCCESS: Dev mode active on port 3001.
echo 🌐 Access at: http://localhost:3001
echo.
pause