#!/bin/bash
# Move to the directory where this script is located
cd "$(dirname "$0")"

echo "---------------------------------------------------------"
echo "🔄 STAGE: Rebuilding Production with latest code changes..."
echo "---------------------------------------------------------"

# --build forces Docker to ignore the old image and make a new one
# -d runs it in the background
docker-compose --profile prod up -d --build

echo ""
echo "✅ SUCCESS: Production has been updated and restarted!"
echo "🌐 Access at: http://localhost:3000"
echo ""

# Keeps the window open to confirm the build finished without errors
read -p "Press enter to close this window..."