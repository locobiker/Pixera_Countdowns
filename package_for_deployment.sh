#!/bin/bash
#
# Package script - Creates a tarball for easy deployment
# This builds the application and packages it into a single archive
#

set -e  # Exit on error

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$SCRIPT_DIR"

echo "========================================="
echo "Packaging Pixera Countdowns for Deployment"
echo "========================================="

# Build first
echo "Building application..."
"$ROOT_DIR/build_production.sh"

# Create package
VERSION=$(date +%Y%m%d_%H%M%S)
PACKAGE_NAME="pixera-countdowns-${VERSION}.tar.gz"
PACKAGE_PATH="${ROOT_DIR}/${PACKAGE_NAME}"

echo ""
echo "Creating package: $PACKAGE_NAME"
cd "$ROOT_DIR"
tar -czf "$PACKAGE_PATH" \
    --exclude='*.pyc' \
    --exclude='*.pyo' \
    --exclude='*.pyd' \
    --exclude='__pycache__' \
    --exclude='*.log' \
    --exclude='*.log.*' \
    --exclude='*.pid' \
    --exclude='node_modules' \
    --exclude='venv' \
    --exclude='.git' \
    --exclude='.DS_Store' \
    --exclude='*.swp' \
    --exclude='*.swo' \
    production_build/

echo ""
echo "========================================="
echo "✅ Package created: $PACKAGE_NAME"
echo "========================================="
echo ""
echo "Package size: $(du -h "$PACKAGE_PATH" | cut -f1)"
echo ""
echo "To deploy:"
echo "  1. Copy $PACKAGE_NAME to your production server"
echo "  2. Extract: tar -xzf $PACKAGE_NAME"
echo "  3. Run: cd production_build && ./start_production.sh"
echo ""

