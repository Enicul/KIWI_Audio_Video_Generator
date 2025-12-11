#!/bin/bash
# Quick start script for KIWI-Video API

set -e

echo "🚀 Starting KIWI-Video API Server..."
echo ""
echo "API will be available at:"
echo "  - Main: http://localhost:8000"
echo "  - Docs: http://localhost:8000/docs"
echo "  - Health: http://localhost:8000/health"
echo ""
echo "Press Ctrl+C to stop"
echo ""

# Ensure we're in the right directory
cd "$(dirname "$0")"

# Start the server
uvicorn kiwi_video.api.app:app --reload --host 0.0.0.0 --port 8000

