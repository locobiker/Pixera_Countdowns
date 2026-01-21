#!/bin/bash
#
# Production start script for Pixera Countdowns
# This starts both backend and frontend in production mode
#

set -e  # Exit on error

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$SCRIPT_DIR"

# Use production_build if it exists, otherwise use current directory
if [ -d "$ROOT_DIR/production_build" ]; then
    ROOT_DIR="$ROOT_DIR/production_build"
fi

BACKEND_DIR="${ROOT_DIR}/backend"
FRONTEND_DIR="${ROOT_DIR}/frontend"
LOG_DIR="${ROOT_DIR}/logs"

BACKEND_PORT=${BACKEND_PORT:-8000}
FRONTEND_PORT=${FRONTEND_PORT:-3000}
PIXERA_HOST=${PIXERA_HOST:-192.168.68.76}
PIXERA_PORT=${PIXERA_PORT:-4023}

# Ensure logs directory exists
mkdir -p "$LOG_DIR"

# Check if already running
if [ -f "$LOG_DIR/backend.pid" ]; then
    OLD_PID=$(cat "$LOG_DIR/backend.pid")
    if ps -p "$OLD_PID" > /dev/null 2>&1; then
        echo "⚠️  Backend is already running (PID: $OLD_PID)"
        echo "   Stop it first with: kill $OLD_PID"
        exit 1
    fi
fi

if [ -f "$LOG_DIR/frontend.pid" ]; then
    OLD_PID=$(cat "$LOG_DIR/frontend.pid")
    if ps -p "$OLD_PID" > /dev/null 2>&1; then
        echo "⚠️  Frontend is already running (PID: $OLD_PID)"
        echo "   Stop it first with: kill $OLD_PID"
        exit 1
    fi
fi

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed"
    exit 1
fi

# Setup Python virtual environment for backend
echo "Setting up Python virtual environment..."
cd "$BACKEND_DIR"
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi
source venv/bin/activate

# Install backend dependencies
echo "Installing backend dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Set environment variables
export PIXERA_HOST="$PIXERA_HOST"
export PIXERA_PORT="$PIXERA_PORT"

# Start FastAPI backend
echo ""
echo "Starting FastAPI backend on port $BACKEND_PORT..."
cd "$ROOT_DIR"
nohup python3 -m uvicorn backend.main:app \
    --host 0.0.0.0 \
    --port "$BACKEND_PORT" \
    --workers 1 \
    > "$LOG_DIR/backend.log" 2>&1 &

BACKEND_PID=$!
echo "$BACKEND_PID" > "$LOG_DIR/backend.pid"
echo "✅ Backend started (PID: $BACKEND_PID)"

# Check if Node.js is available for serving frontend
if command -v node &> /dev/null && command -v npm &> /dev/null; then
    # Check if serve or http-server is available
    if command -v serve &> /dev/null; then
        echo ""
        echo "Starting frontend server on port $FRONTEND_PORT..."
        cd "$FRONTEND_DIR"
        nohup serve -s . -l "$FRONTEND_PORT" \
            > "$LOG_DIR/frontend.log" 2>&1 &
        FRONTEND_PID=$!
    elif command -v npx &> /dev/null; then
        echo ""
        echo "Starting frontend server on port $FRONTEND_PORT..."
        cd "$FRONTEND_DIR"
        nohup npx serve -s . -l "$FRONTEND_PORT" \
            > "$LOG_DIR/frontend.log" 2>&1 &
        FRONTEND_PID=$!
    else
        echo ""
        echo "⚠️  No frontend server found (serve or npx)"
        echo "   Install with: npm install -g serve"
        echo "   Or serve the frontend directory with your web server"
        FRONTEND_PID=""
    fi
    
    if [ -n "$FRONTEND_PID" ]; then
        echo "$FRONTEND_PID" > "$LOG_DIR/frontend.pid"
        echo "✅ Frontend started (PID: $FRONTEND_PID)"
    fi
else
    echo ""
    echo "⚠️  Node.js not found"
    echo "   Serve the frontend directory ($FRONTEND_DIR) with your web server"
    echo "   Or install Node.js and run: npm install -g serve"
fi

echo ""
echo "========================================="
echo "✅ Pixera Countdowns started!"
echo "========================================="
echo ""
echo "Backend: http://localhost:$BACKEND_PORT"
echo "Frontend: http://localhost:$FRONTEND_PORT"
echo ""
echo "Logs: $LOG_DIR"
echo "  - Backend: tail -f $LOG_DIR/backend.log"
echo "  - Frontend: tail -f $LOG_DIR/frontend.log"
echo ""
echo "To stop:"
echo "  kill \$(cat $LOG_DIR/backend.pid)"
if [ -f "$LOG_DIR/frontend.pid" ]; then
    echo "  kill \$(cat $LOG_DIR/frontend.pid)"
fi
echo ""

