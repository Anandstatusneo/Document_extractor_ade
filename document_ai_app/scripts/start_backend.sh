#!/bin/bash

# Document AI Backend Startup Script

echo "🚀 Starting Document AI Backend..."

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install dependencies if needed
if [ ! -f "deps_installed" ]; then
    echo "Installing dependencies..."
    pip install -r requirements.txt
    touch deps_installed
fi

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "Creating .env file from template..."
    cp .env.example .env
    echo "⚠️  Please edit .env file with your API keys"
fi

# Create upload directory
mkdir -p uploads

# Start the backend server
echo "Starting FastAPI server on http://localhost:8000"
cd backend
uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload

echo "✅ Backend started successfully!"
echo "📖 API Documentation: http://localhost:8000/docs"
echo "🔍 Health Check: http://localhost:8000/health"
