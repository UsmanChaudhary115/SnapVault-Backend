#!/bin/bash

echo "🚀 Starting SnapVault Backend..."
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found!"
    echo "Please run setup.sh first to set up the project."
    exit 1
fi

# Activate virtual environment and start the server
echo "🔄 Activating virtual environment..."
source venv/bin/activate

echo "🚀 Starting FastAPI server..."
echo "📍 Server will be available at: http://localhost:8000"
echo "📚 API Documentation: http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

uvicorn main:app --reload --host 0.0.0.0 --port 8000 