#!/bin/bash
# Start Flynt API Server

# Set Python path
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

# Install dependencies if needed
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
else
    source venv/bin/activate
fi

# Start API server
echo "Starting Flynt API server..."
uvicorn flynt_api.app:create_app --host 0.0.0.0 --port 8000 --reload --log-level info
