#!/bin/bash

# Document AI Frontend Startup Script

echo "🎨 Starting Document AI Frontend..."

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

# Start the frontend server
echo "Starting Streamlit server on http://localhost:8501"
cd frontend
streamlit run main.py --server.port 8501 --server.address 0.0.0.0

echo "✅ Frontend started successfully!"
echo "🌐 Application URL: http://localhost:8501"
