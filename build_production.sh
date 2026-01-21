#!/bin/bash
#
# Build script for production deployment
# This prepares the application for production use
#

set -e  # Exit on error

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="${ROOT_DIR}/pixera_backend"
FRONTEND_DIR="${ROOT_DIR}/pixera_frontend"
BUILD_DIR="${ROOT_DIR}/production_build"

echo "========================================="
echo "Building Pixera Countdowns for Production"
echo "========================================="

# Clean previous build
if [ -d "$BUILD_DIR" ]; then
    echo "Cleaning previous build..."
    rm -rf "$BUILD_DIR"
fi

mkdir -p "$BUILD_DIR"
mkdir -p "$BUILD_DIR/logs"

# Build Frontend
echo ""
echo "Building frontend..."
cd "$FRONTEND_DIR"

# Install dependencies if needed
if [ ! -d "node_modules" ]; then
    echo "Installing frontend dependencies..."
    npm install
fi

# Build for production
echo "Running production build..."
npm run build

# Copy frontend build to production directory
echo "Copying frontend build..."
mkdir -p "$BUILD_DIR/frontend"
cp -r "$FRONTEND_DIR/dist"/* "$BUILD_DIR/frontend/"

# Copy Backend
echo ""
echo "Copying backend..."
mkdir -p "$BUILD_DIR/backend"

# Copy backend files, excluding unnecessary items
rsync -av --exclude='__pycache__' \
      --exclude='*.pyc' \
      --exclude='*.pyo' \
      --exclude='venv' \
      --exclude='.git' \
      --exclude='*.log' \
      "$BACKEND_DIR/" "$BUILD_DIR/backend/" || {
    # Fallback if rsync not available
    cp -r "$BACKEND_DIR"/* "$BUILD_DIR/backend/" 2>/dev/null || true
    find "$BUILD_DIR/backend" -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
    find "$BUILD_DIR/backend" -type f -name "*.pyc" -delete 2>/dev/null || true
    rm -rf "$BUILD_DIR/backend/venv" 2>/dev/null || true
}

# Copy configuration and scripts
echo ""
echo "Copying configuration files..."
cp "$ROOT_DIR/start_production.sh" "$BUILD_DIR/" 2>/dev/null || echo "start_production.sh will be created"
cp "$ROOT_DIR/stop_production.sh" "$BUILD_DIR/" 2>/dev/null || echo "stop_production.sh will be created"
cp "$ROOT_DIR/update_production.sh" "$BUILD_DIR/" 2>/dev/null || echo "update_production.sh will be created"
cp "$ROOT_DIR/README_DEPLOYMENT.md" "$BUILD_DIR/" 2>/dev/null || echo "README will be created"
cp "$ROOT_DIR/DEPLOYMENT_QUICK_START.md" "$BUILD_DIR/" 2>/dev/null || true

# Create a version file
echo "$(date +%Y%m%d_%H%M%S)" > "$BUILD_DIR/VERSION"

echo ""
echo "========================================="
echo "✅ Build complete!"
echo "Production build is in: $BUILD_DIR"
echo "========================================="
echo ""
echo "Next steps:"
echo "1. Review the build in: $BUILD_DIR"
echo "2. Copy $BUILD_DIR to your production server"
echo "3. Run ./start_production.sh on the production server"
echo ""

