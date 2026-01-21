#!/bin/bash
#
# Stop script for production deployment
#

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$SCRIPT_DIR"

# Use production_build if it exists, otherwise use current directory
if [ -d "$ROOT_DIR/production_build" ]; then
    ROOT_DIR="$ROOT_DIR/production_build"
fi

LOG_DIR="${ROOT_DIR}/logs"

echo "Stopping Pixera Countdowns..."

# Stop backend
if [ -f "$LOG_DIR/backend.pid" ]; then
    BACKEND_PID=$(cat "$LOG_DIR/backend.pid")
    if ps -p "$BACKEND_PID" > /dev/null 2>&1; then
        echo "Stopping backend (PID: $BACKEND_PID)..."
        kill "$BACKEND_PID" || true
        sleep 2
        if ps -p "$BACKEND_PID" > /dev/null 2>&1; then
            echo "Force killing backend..."
            kill -9 "$BACKEND_PID" || true
        fi
        echo "✅ Backend stopped"
    fi
    rm -f "$LOG_DIR/backend.pid"
fi

# Stop frontend
if [ -f "$LOG_DIR/frontend.pid" ]; then
    FRONTEND_PID=$(cat "$LOG_DIR/frontend.pid")
    if ps -p "$FRONTEND_PID" > /dev/null 2>&1; then
        echo "Stopping frontend (PID: $FRONTEND_PID)..."
        kill "$FRONTEND_PID" || true
        sleep 1
        if ps -p "$FRONTEND_PID" > /dev/null 2>&1; then
            echo "Force killing frontend..."
            kill -9 "$FRONTEND_PID" || true
        fi
        echo "✅ Frontend stopped"
    fi
    rm -f "$LOG_DIR/frontend.pid"
fi

echo ""
echo "✅ All services stopped"

