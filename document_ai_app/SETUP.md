# 🚀 Document AI Application Setup Guide

## 📋 Prerequisites

- **Python 3.10+** (3.13+ recommended)
- **Tesseract OCR** - for basic OCR functionality
- **Git** - to clone the repository

## ⚡ Quick Setup

### 1. Clone and Setup

```bash
cd document_ai_app
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
cp .env.example .env
# Edit .env with your API keys
```

### 3. Install Tesseract OCR

```bash
# macOS
brew install tesseract

# Ubuntu/Debian
sudo apt-get install tesseract-ocr

# Windows
# Download from: https://github.com/UB-Mannheim/tesseract/wiki
```

### 4. Start Services

```bash
# Terminal 1: Start Backend
./scripts/start_backend.sh

# Terminal 2: Start Frontend
./scripts/start_frontend.sh
```

### 5. Access Application

- **Frontend**: http://localhost:8501
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

## 🔑 Required API Keys

Edit `.env` file with your API keys:

### LandingAI ADE (Recommended)
```bash
VISION_AGENT_API_KEY=your_landingai_api_key_here
```
Get from: https://landing.ai

### Optional Keys
```bash
HF_TOKEN=your_huggingface_api_key_here      # For Hugging Face models
GROQ_API_KEY=your_groq_api_key_here        # For Groq models
OPENAI_API_KEY=your_openai_api_key_here    # For OpenAI models
```

## 🏗️ Architecture Overview

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Streamlit     │    │   FastAPI       │    │   OCR Engines   │
│   Frontend      │◄──►│   Backend       │◄──►│   (Tesseract,   │
│   (Port 8501)   │    │   (Port 8000)   │    │   PaddleOCR,    │
└─────────────────┘    └─────────────────┘    │   LandingAI)    │
                                              └─────────────────┘
```

## 📁 Project Structure

```
document_ai_app/
├── backend/                 # FastAPI backend
│   ├── api/                # API endpoints
│   ├── core/               # Configuration
│   ├── models/             # Data models
│   ├── services/           # Business logic
│   └── utils/              # Utilities
├── frontend/               # Streamlit frontend
│   ├── pages/              # App pages
│   ├── components/         # UI components
│   └── utils/              # Frontend utilities
├── shared/                 # Shared code
│   ├── models/             # Shared data models
│   └── config/             # Shared config
├── scripts/                # Startup scripts
├── requirements.txt        # Dependencies
└── .env.example          # Environment template
```

## 🚀 Running the Application

### Method 1: Using Scripts (Recommended)

```bash
# Start Backend
./scripts/start_backend.sh

# Start Frontend (new terminal)
./scripts/start_frontend.sh
```

### Method 2: Manual Start

```bash
# Backend
cd backend
uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload

# Frontend (new terminal)
cd frontend
streamlit run main.py --server.port 8501
```

## 📖 Usage Guide

### 1. Upload Document
- Navigate to Upload page
- Drag & drop or browse for file
- Supported formats: PDF, PNG, JPG, TIFF, BMP
- Max file size: 50MB

### 2. Choose OCR Engine
- **Tesseract**: Fast, good for simple text
- **PaddleOCR**: Better for complex layouts
- **LandingAI ADE**: Best for structured extraction

### 3. Process Document
- Click "Process Document"
- Wait for processing to complete
- View results in Results page

### 4. View Results
- **Extracted Text**: Full text content
- **Chunks**: Structured extraction with metadata
- **Statistics**: Processing metrics
- **JSON**: Raw API response

## 🔧 Configuration

### Backend Settings (.env)
```bash
# Server
HOST=0.0.0.0
PORT=8000
DEBUG=false

# File Upload
MAX_FILE_SIZE=52428800  # 50MB
UPLOAD_DIR=uploads

# OCR
DEFAULT_OCR_ENGINE=tesseract
```

### Frontend Settings
- Backend URL configurable in sidebar
- Theme and display options
- Processing preferences

## 🛠️ Development

### Backend Development
```bash
cd backend
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend Development
```bash
cd frontend
streamlit run main.py --server.port 8501
```

### Running Tests
```bash
pytest tests/
```

## 🐳 Docker Deployment

```bash
# Build and run with Docker Compose
docker-compose up -d

# Or build individually
docker build -f Dockerfile.backend -t docai-backend .
docker build -f Dockerfile.frontend -t docai-frontend .
```

## 🔍 Troubleshooting

### Common Issues

#### Backend Not Starting
```bash
# Check dependencies
pip install -r requirements.txt

# Check port conflicts
lsof -i :8000

# Check logs
uvicorn api.main:app --log-level debug
```

#### Frontend Not Connecting
```bash
# Verify backend is running
curl http://localhost:8000/health

# Check CORS settings
# Ensure frontend URL is in BACKEND_CORS_ORIGINS
```

#### OCR Engine Errors
```bash
# Check Tesseract
tesseract --version

# Check LandingAI API key
curl -H "Authorization: Bearer YOUR_KEY" https://api.va.landing.ai/v1/ade/health
```

#### File Upload Issues
```bash
# Check file permissions
ls -la uploads/

# Check file size limits
# Verify MAX_FILE_SIZE in .env
```

### Performance Tips

1. **Use appropriate OCR engine**:
   - Tesseract for simple documents
   - LandingAI for complex extraction

2. **Optimize file sizes**:
   - Compress images before upload
   - Use appropriate resolution

3. **Backend performance**:
   - Use Redis for caching
   - Implement file cleanup

## 📚 API Documentation

### Endpoints

- `GET /health` - Health check
- `GET /api/v1/engines` - Available OCR engines
- `POST /api/v1/upload` - Upload and process document
- `POST /api/v1/process` - Process existing document
- `GET /api/v1/documents/{id}` - Get document result

### Response Format

```json
{
  "success": true,
  "message": "Document processed successfully",
  "data": {
    "document_id": "uuid",
    "ocr_engine": "landingai",
    "processing_time": 2.5,
    "chunks": [...],
    "markdown": "extracted content"
  }
}
```

## 🤝 Contributing

1. Fork the repository
2. Create feature branch
3. Make changes and test
4. Submit pull request

## 📄 License

MIT License - see LICENSE file for details

## 🆘 Support

- Check the troubleshooting section
- Review API documentation
- Open an issue on GitHub
