# 🚀 Document AI Application

A modern, production-ready Document AI application with Streamlit frontend and FastAPI backend.

## 📁 Project Structure

```
document_ai_app/
├── backend/                    # FastAPI backend services
│   ├── api/                   # API endpoints
│   │   ├── __init__.py
│   │   ├── main.py           # FastAPI app entry point
│   │   ├── routes/           # API route handlers
│   │   │   ├── __init__.py
│   │   │   ├── documents.py  # Document processing endpoints
│   │   │   └── health.py     # Health check endpoints
│   │   └── middleware/       # Custom middleware
│   ├── core/                 # Core business logic
│   │   ├── __init__.py
│   │   ├── config.py         # Configuration settings
│   │   ├── security.py       # Authentication & security
│   │   └── exceptions.py     # Custom exceptions
│   ├── models/               # Pydantic models
│   │   ├── __init__.py
│   │   ├── document.py       # Document-related models
│   │   └── response.py       # API response models
│   ├── services/             # Business services
│   │   ├── __init__.py
│   │   ├── ocr_service.py    # OCR processing services
│   │   ├── ade_service.py    # LandingAI ADE services
│   │   └── storage_service.py # File storage services
│   └── utils/                # Utility functions
│       ├── __init__.py
│       ├── file_utils.py     # File handling utilities
│       └── image_utils.py    # Image processing utilities
├── frontend/                 # Streamlit frontend
│   ├── pages/                # Streamlit pages
│   │   ├── __init__.py
│   │   ├── home.py          # Home page
│   │   ├── upload.py        # Document upload page
│   │   ├── results.py       # Results display page
│   │   └── history.py       # Processing history page
│   ├── components/           # Reusable UI components
│   │   ├── __init__.py
│   │   ├── file_uploader.py # File upload component
│   │   ├── result_viewer.py # Result display component
│   │   └── sidebar.py      # Navigation sidebar
│   ├── assets/              # Static assets
│   │   ├── css/            # Custom CSS styles
│   │   ├── images/         # Image assets
│   │   └── js/             # JavaScript files
│   ├── utils/              # Frontend utilities
│   │   ├── __init__.py
│   │   └── api_client.py  # Backend API client
│   └── main.py             # Streamlit app entry point
├── shared/                 # Shared code between frontend/backend
│   ├── models/            # Shared data models
│   │   ├── __init__.py
│   │   └── document.py   # Document models
│   └── config/           # Shared configuration
│       ├── __init__.py
│       └── settings.py   # Application settings
├── tests/                # Test suite
│   ├── __init__.py
│   ├── test_api/        # API tests
│   ├── test_services/   # Service tests
│   └── test_utils/      # Utility tests
├── docs/                # Documentation
│   ├── api.md          # API documentation
│   ├── deployment.md   # Deployment guide
│   └── user_guide.md   # User guide
├── scripts/            # Utility scripts
│   ├── setup.sh       # Environment setup
│   ├── start_backend.sh # Backend startup script
│   └── start_frontend.sh # Frontend startup script
├── requirements.txt    # Python dependencies
├── docker-compose.yml  # Docker configuration
├── Dockerfile.backend  # Backend Dockerfile
├── Dockerfile.frontend # Frontend Dockerfile
└── .env.example       # Environment variables template
```

## 🏗️ Architecture

### Backend (FastAPI)
- **RESTful API** for document processing
- **Multiple OCR engines**: Tesseract, PaddleOCR, LandingAI ADE
- **Async processing** for better performance
- **File storage** with local/cloud options
- **Authentication** and security middleware

### Frontend (Streamlit)
- **Modern UI** with file upload functionality
- **Real-time processing** status
- **Interactive results** display with bounding boxes
- **Processing history** and document management
- **Responsive design** for mobile/desktop

### Key Features
- 📄 **Multi-format support**: PDF, PNG, JPG, TIFF
- 🔍 **Multiple OCR options**: Basic, Advanced, AI-powered
- 📊 **Structured extraction**: Tables, forms, key-value pairs
- 🎯 **Visual grounding**: Bounding box visualization
- 📈 **Processing analytics**: Success rates, timing metrics
- 💾 **Document management**: History, search, export

## 🚀 Quick Start

### 1. Setup Environment
```bash
cd document_ai_app
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure Environment
```bash
cp .env.example .env
# Edit .env with your API keys
```

### 3. Start Services
```bash
# Start backend
./scripts/start_backend.sh

# Start frontend (new terminal)
./scripts/start_frontend.sh
```

### 4. Access Application
- Frontend: http://localhost:8501
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

## 📚 Usage

1. **Upload Document**: Drag & drop or browse for PDF/image files
2. **Choose OCR Engine**: Select Tesseract, PaddleOCR, or LandingAI ADE
3. **Process**: Click to extract text and structure
4. **View Results**: Interactive display with extracted data
5. **Export**: Download results as JSON, CSV, or Markdown

## 🔧 Development

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
docker-compose up -d
```

## 📖 Documentation

- [API Documentation](docs/api.md)
- [Deployment Guide](docs/deployment.md)
- [User Guide](docs/user_guide.md)

## 🤝 Contributing

1. Fork the repository
2. Create feature branch
3. Make changes and test
4. Submit pull request

## 📄 License

MIT License - see LICENSE file for details
