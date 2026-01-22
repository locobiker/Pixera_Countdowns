#!/bin/bash
cd "$(dirname "$0")"
echo "---------------------------------------------------------"
echo "STAGE: Starting DEVELOPMENT Environment"
echo "---------------------------------------------------------"
docker-compose --profile dev up -d
echo ""
echo "🛠️  SUCCESS: Dev mode active."
echo "🌐 Access at: http://localhost:3001"
echo ""
read -p "Press enter to close this window..."