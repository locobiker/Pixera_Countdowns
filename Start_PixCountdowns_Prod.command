#!/bin/bash
cd "$(dirname "$0")"
echo "---------------------------------------------------------"
echo "STAGE: Starting PRODUCTION Environment"
echo "---------------------------------------------------------"
docker-compose --profile prod up -d
echo ""
echo "✅ SUCCESS: System is running."
echo "🌐 Access at: http://localhost:3000"
echo ""
# Keeps the window open so they can see the success message
read -p "Press enter to close this window..."