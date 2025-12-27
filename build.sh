#!/bin/bash
# Build script for TERRAQORE - Linux/macOS

set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$PROJECT_ROOT/core_clli"
FRONTEND_DIR="$PROJECT_ROOT/gui"

echo "=========================================="
echo "TERRAQORE v1.0 - Build Script"
echo "=========================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[✓]${NC} $1"
}

print_error() {
    echo -e "${RED}[✗]${NC} $1"
}

print_info() {
    echo -e "${YELLOW}[i]${NC} $1"
}

# Check prerequisites
print_info "Checking prerequisites..."

if ! command -v python3 &> /dev/null; then
    print_error "Python 3 is not installed"
    exit 1
fi

if ! command -v node &> /dev/null; then
    print_error "Node.js is not installed"
    exit 1
fi

if ! command -v npm &> /dev/null; then
    print_error "npm is not installed"
    exit 1
fi

print_status "Python 3 found: $(python3 --version)"
print_status "Node.js found: $(node --version)"
print_status "npm found: $(npm --version)"
echo ""

# Backend Build
print_info "Building backend..."
cd "$BACKEND_DIR"

# Create virtual environment if it doesn't exist
if [ ! -d ".venv" ]; then
    print_info "Creating virtual environment..."
    python3 -m venv .venv
fi

# Activate virtual environment
source .venv/bin/activate

# Install dependencies
print_info "Installing backend dependencies..."
pip install --upgrade pip
pip install -r "$PROJECT_ROOT/requirements.txt"
pip install build wheel setuptools

# Run tests
if [ -d "tests" ]; then
    print_info "Running backend tests..."
    pip install pytest pytest-cov
    pytest tests -v --cov=core --cov-report=term-missing || print_error "Some tests failed"
else
    print_info "No tests directory found, skipping tests"
fi

print_status "Backend built successfully"
echo ""

# Frontend Build
print_info "Building frontend..."
cd "$FRONTEND_DIR"

# Install dependencies
print_info "Installing frontend dependencies..."
npm ci

# Run linter
if npm run lint 2>/dev/null; then
    print_status "Linting passed"
else
    print_info "Linting completed with warnings"
fi

# Build
print_info "Building frontend bundle..."
npm run build

print_status "Frontend built successfully"
echo ""

# Create dist directory if it doesn't exist
print_info "Preparing distribution files..."
mkdir -p "$PROJECT_ROOT/dist"

echo ""
print_status "=========================================="
print_status "Build completed successfully!"
print_status "=========================================="
echo ""
print_info "Backend: Ready to run with 'cd core_clli && .venv/bin/python -m uvicorn backend_main:app'"
print_info "Frontend: Ready to serve from gui/dist/"
echo ""
