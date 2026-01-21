#!/bin/bash
#
# Update script for production deployment
# This updates the application while keeping it running
#

set -e  # Exit on error

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$SCRIPT_DIR"

# Use production_build if it exists, otherwise use current directory
if [ -d "$ROOT_DIR/production_build" ]; then
    ROOT_DIR="$ROOT_DIR/production_build"
fi

LOG_DIR="${ROOT_DIR}/logs"
BACKEND_DIR="${ROOT_DIR}/backend"
FRONTEND_DIR="${ROOT_DIR}/frontend"

echo "========================================="
echo "Updating Pixera Countdowns"
echo "========================================="

# Check if running
BACKEND_PID=""
FRONTEND_PID=""

if [ -f "$LOG_DIR/backend.pid" ]; then
    BACKEND_PID=$(cat "$LOG_DIR/backend.pid")
    if ps -p "$BACKEND_PID" > /dev/null 2>&1; then
        echo "Backend is running (PID: $BACKEND_PID)"
    else
        BACKEND_PID=""
    fi
fi

if [ -f "$LOG_DIR/frontend.pid" ]; then
    FRONTEND_PID=$(cat "$LOG_DIR/frontend.pid")
    if ps -p "$FRONTEND_PID" > /dev/null 2>&1; then
        echo "Frontend is running (PID: $FRONTEND_PID)"
    else
        FRONTEND_PID=""
    fi
fi

# Stop services
if [ -n "$BACKEND_PID" ]; then
    echo ""
    echo "Stopping backend..."
    kill "$BACKEND_PID" || true
    sleep 2
    # Force kill if still running
    if ps -p "$BACKEND_PID" > /dev/null 2>&1; then
        kill -9 "$BACKEND_PID" || true
    fi
    rm -f "$LOG_DIR/backend.pid"
fi

if [ -n "$FRONTEND_PID" ]; then
    echo "Stopping frontend..."
    kill "$FRONTEND_PID" || true
    sleep 1
    # Force kill if still running
    if ps -p "$FRONTEND_PID" > /dev/null 2>&1; then
        kill -9 "$FRONTEND_PID" || true
    fi
    rm -f "$LOG_DIR/frontend.pid"
fi

# Update backend dependencies if requirements.txt changed
if [ -f "$BACKEND_DIR/requirements.txt" ]; then
    echo ""
    echo "Updating backend dependencies..."
    cd "$BACKEND_DIR"
    if [ -d "venv" ]; then
        source venv/bin/activate
        pip install --upgrade pip
        pip install -r requirements.txt
    fi
fi

# Update frontend if package.json changed
if [ -f "$FRONTEND_DIR/package.json" ] && [ -d "$FRONTEND_DIR/node_modules" ]; then
    echo ""
    echo "Updating frontend dependencies..."
    cd "$FRONTEND_DIR"
    npm install
    # Rebuild if needed
    if [ -f "package.json" ]; then
        echo "Rebuilding frontend..."
        npm run build
    fi
fi

# Restart services
echo ""
echo "Restarting services..."
cd "$SCRIPT_DIR"
./start_production.sh

echo ""
echo "========================================="
echo "✅ Update complete!"
echo "========================================="

