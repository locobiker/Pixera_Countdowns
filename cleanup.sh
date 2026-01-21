#!/bin/bash
#
# Cleanup script - Removes unnecessary files and directories
# This helps keep the project clean and reduces size
#

set -e  # Exit on error

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "========================================="
echo "Cleaning up Pixera Countdowns project"
echo "========================================="

# Remove Python cache files
echo "Removing Python cache files..."
find "$ROOT_DIR" -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find "$ROOT_DIR" -type f -name "*.pyc" -delete 2>/dev/null || true
find "$ROOT_DIR" -type f -name "*.pyo" -delete 2>/dev/null || true
find "$ROOT_DIR" -type f -name "*.pyd" -delete 2>/dev/null || true

# Remove Python virtual environments (they'll be recreated on production)
echo "Removing Python virtual environments..."
if [ -d "$ROOT_DIR/venv" ]; then
    echo "  Removing $ROOT_DIR/venv"
    rm -rf "$ROOT_DIR/venv"
fi
if [ -d "$ROOT_DIR/pixera_backend/venv" ]; then
    echo "  Removing $ROOT_DIR/pixera_backend/venv"
    rm -rf "$ROOT_DIR/pixera_backend/venv"
fi

# Remove node_modules (they'll be reinstalled when needed)
echo "Removing node_modules..."
if [ -d "$ROOT_DIR/pixera_frontend/node_modules" ]; then
    echo "  Removing $ROOT_DIR/pixera_frontend/node_modules"
    rm -rf "$ROOT_DIR/pixera_frontend/node_modules"
fi

# Remove build artifacts
echo "Removing build artifacts..."
if [ -d "$ROOT_DIR/pixera_frontend/dist" ]; then
    echo "  Removing $ROOT_DIR/pixera_frontend/dist"
    rm -rf "$ROOT_DIR/pixera_frontend/dist"
fi
if [ -d "$ROOT_DIR/production_build" ]; then
    echo "  Removing $ROOT_DIR/production_build"
    rm -rf "$ROOT_DIR/production_build"
fi

# Remove old log files (keep directory structure)
echo "Cleaning log files..."
if [ -d "$ROOT_DIR/logs" ]; then
    echo "  Removing old log files..."
    rm -f "$ROOT_DIR/logs"/*.log* 2>/dev/null || true
    rm -f "$ROOT_DIR/logs"/*.pid 2>/dev/null || true
    # Keep the directory
    touch "$ROOT_DIR/logs/.gitkeep" 2>/dev/null || true
fi

# Remove old/unused files
echo "Removing old/unused files..."
if [ -f "$ROOT_DIR/pixera_frontend/server.js" ]; then
    echo "  Removing old server.js (not needed with current setup)"
    rm -f "$ROOT_DIR/pixera_frontend/server.js"
fi

if [ -d "$ROOT_DIR/pixera_frontend/public" ]; then
    echo "  Removing old public directory (using Vite build instead)"
    rm -rf "$ROOT_DIR/pixera_frontend/public"
fi

# Remove root package-lock.json if it exists (should only be in frontend)
if [ -f "$ROOT_DIR/package-lock.json" ] && [ ! -f "$ROOT_DIR/package.json" ]; then
    echo "  Removing root package-lock.json (not needed)"
    rm -f "$ROOT_DIR/package-lock.json"
fi

# Remove duplicate config files (keep .js versions, remove .cjs)
if [ -f "$ROOT_DIR/pixera_frontend/postcss.config.js" ] && [ -f "$ROOT_DIR/pixera_frontend/postcss.config.cjs" ]; then
    echo "  Removing duplicate postcss.config.cjs (keeping .js version)"
    rm -f "$ROOT_DIR/pixera_frontend/postcss.config.cjs"
fi

if [ -f "$ROOT_DIR/pixera_frontend/tailwind.config.js" ] && [ -f "$ROOT_DIR/pixera_frontend/tailwind.config.cjs" ]; then
    echo "  Removing duplicate tailwind.config.cjs (keeping .js version)"
    rm -f "$ROOT_DIR/pixera_frontend/tailwind.config.cjs"
fi

echo ""
echo "========================================="
echo "✅ Cleanup complete!"
echo "========================================="
echo ""
echo "Removed:"
echo "  - Python cache files (__pycache__, *.pyc)"
echo "  - Python virtual environments (venv/)"
echo "  - Node modules (node_modules/)"
echo "  - Build artifacts (dist/, production_build/)"
echo "  - Old log files"
echo "  - Unused files (server.js, public/, etc.)"
echo ""
echo "Note: These will be recreated as needed:"
echo "  - venv/ when you run start_production.sh"
echo "  - node_modules/ when you run npm install"
echo "  - dist/ when you run npm run build"
echo ""


