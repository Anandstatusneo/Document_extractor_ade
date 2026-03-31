#!/bin/bash

# Document AI Setup Script
echo "🚀 Setting up Document AI Environment..."

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo "Installing Python dependencies..."
pip install -r requirements.txt

# Check system dependencies
echo "Checking system dependencies..."

# Check Tesseract
if command -v tesseract &> /dev/null; then
    echo "✓ Tesseract OCR is installed: $(tesseract --version | head -1)"
else
    echo "✗ Tesseract OCR not found. Please install it:"
    echo "  macOS: brew install tesseract"
    echo "  Ubuntu/Debian: sudo apt-get install tesseract-ocr"
    echo "  Windows: Download from https://github.com/UB-Mannheim/tesseract/wiki"
fi

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    echo "Creating .env file from template..."
    cp .env.example .env
    echo "⚠️  Please edit .env file with your API keys:"
    echo "   - VISION_AGENT_API_KEY (from LandingAI)"
    echo "   - HF_TOKEN (from Hugging Face)"
    echo "   - GROQ_API_KEY (from Groq)"
    echo "   - OPENAI_API_KEY (from OpenAI, optional)"
fi

echo ""
echo "✅ Setup complete!"
echo ""
echo "📋 Next steps:"
echo "1. Edit .env file with your API keys"
echo "2. Activate the environment: source venv/bin/activate"
echo "3. Start with L2/L2.ipynb for basic OCR"
echo "4. Progress through L4, L6, L8, L9, L11 notebooks"
echo ""
echo "📖 For detailed instructions, see README.md"
