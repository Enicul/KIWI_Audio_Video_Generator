#!/bin/bash
# Run development server

set -e

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
fi

echo "🚀 Starting KIWI-Video development server..."
echo "API will be available at http://localhost:8000"
echo "API docs at http://localhost:8000/docs"
echo ""

uvicorn kiwi_video.api.app:app --reload --host 0.0.0.0 --port 8000

