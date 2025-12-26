#!/bin/bash
# Start script for FlyntCore - Linux/macOS

set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$PROJECT_ROOT/core_clli"
FRONTEND_DIR="$PROJECT_ROOT/gui"

echo "=========================================="
echo "FlyntCore v1.0 - Start Script"
echo "=========================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

print_status() {
    echo -e "${GREEN}[✓]${NC} $1"
}

print_info() {
    echo -e "${YELLOW}[i]${NC} $1"
}

# Check if backend and frontend should be started
START_BACKEND=true
START_FRONTEND=true

if [ "$1" == "--backend-only" ]; then
    START_FRONTEND=false
elif [ "$1" == "--frontend-only" ]; then
    START_BACKEND=false
fi

# Start backend
if [ "$START_BACKEND" = true ]; then
    print_info "Starting backend..."
    cd "$BACKEND_DIR"
    
    # Activate virtual environment
    if [ -d ".venv" ]; then
        source .venv/bin/activate
    fi
    
    # Check if Ollama is running
    if ! curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
        print_info "Note: Ollama is not running. Start with: ollama serve"
    fi
    
    print_status "Starting backend on http://127.0.0.1:8000"
    python -m uvicorn backend_main:app --host 127.0.0.1 --port 8000 &
    BACKEND_PID=$!
    sleep 2
fi

# Start frontend
if [ "$START_FRONTEND" = true ]; then
    print_info "Starting frontend..."
    cd "$FRONTEND_DIR"
    
    print_status "Starting frontend on http://localhost:3001"
    npm run dev &
    FRONTEND_PID=$!
    sleep 2
fi

echo ""
print_status "=========================================="
print_status "FlyntCore is running!"
print_status "=========================================="
echo ""

if [ "$START_BACKEND" = true ]; then
    echo "Backend API: http://127.0.0.1:8000"
    echo "API Docs: http://127.0.0.1:8000/docs"
fi

if [ "$START_FRONTEND" = true ]; then
    echo "Frontend: http://localhost:3001"
fi

echo ""
print_info "Press Ctrl+C to stop all services"
echo ""

# Wait for processes
if [ "$START_BACKEND" = true ] && [ "$START_FRONTEND" = true ]; then
    wait $BACKEND_PID $FRONTEND_PID
elif [ "$START_BACKEND" = true ]; then
    wait $BACKEND_PID
elif [ "$START_FRONTEND" = true ]; then
    wait $FRONTEND_PID
fi
