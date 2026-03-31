# 🚀 Getting Started with Document AI

This guide will help you set up and run the Document AI course from scratch.

## 📋 Prerequisites

- **Python 3.10+** (3.13.3 tested)
- **Git** to clone the repository
- **Tesseract OCR** (for basic OCR lessons)

## ⚡ Quick Setup

### Option 1: Automated Setup (Recommended)

```bash
# Clone the repository
git clone https://github.com/Ahmed-El-Zainy/Document-AI-From-OCR-to-Agentic-Doc-Extraction.git
cd Document-AI-From-OCR-to-Agentic-Doc-Extraction

# Run the setup script
./setup.sh
```

### Option 2: Manual Setup

```bash
# 1. Create virtual environment
python3 -m venv venv
source venv/bin/activate

# 2. Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# 3. Install Tesseract OCR
# macOS:
brew install tesseract
# Ubuntu/Debian:
sudo apt-get install tesseract-ocr
# Windows: Download from https://github.com/UB-Mannheim/tesseract/wiki

# 4. Set up environment variables
cp .env.example .env
# Edit .env with your API keys
```

## 🔑 API Keys Setup

Edit the `.env` file with your API keys:

### Required for Core Lessons
- **VISION_AGENT_API_KEY**: Get from [LandingAI](https://landing.ai)
- **HF_TOKEN**: Get from [Hugging Face](https://huggingface.co/settings/tokens)
- **GROQ_API_KEY**: Get from [Groq](https://console.groq.com/keys)

### Optional
- **OPENAI_API_KEY**: Get from [OpenAI](https://platform.openai.com/api-keys)
- **AWS credentials**: Only needed for Lab 6 (AWS RAG Pipeline)

## 📚 Course Structure

The course is organized into progressive lessons:

| Lesson | Directory | Topic | Difficulty |
|--------|-----------|-------|------------|
| **L2** | `L2/` | Basic OCR with Tesseract | ⭐ Beginner |
| **L4** | `L4/` | Advanced OCR with PaddleOCR | ⭐⭐ Intermediate |
| **L6** | `L6/` | Layout Analysis with LayoutReader | ⭐⭐⭐ Intermediate |
| **L8** | `L8/` | Agentic Document Extraction | ⭐⭐⭐ Advanced |
| **L9** | `L9/` | Batch Processing | ⭐⭐⭐ Advanced |
| **L11** | `L11/` | RAG with ChromaDB | ⭐⭐⭐⭐ Advanced |
| **Lab 6** | `rag_pipeline_aws/` | AWS RAG Pipeline | ⭐⭐⭐⭐⭐ Expert |

## 🏃‍♂️ Running Your First Lesson

### 1. Start with Basic OCR (L2)

```bash
# Activate environment
source venv/bin/activate

# Start Jupyter Lab
jupyter lab

# Navigate to L2/L2.ipynb and run the cells
```

### 2. Test Your Setup

Run the test script to verify everything works:

```bash
python test_ocr.py
```

Expected output:
```
Testing Tesseract OCR...
✓ Tesseract version: 5.5.2
Testing with L2/invoice.png...
✓ Successfully extracted text from L2/invoice.png
```

## 🛠️ Troubleshooting

### Common Issues

#### 1. Tesseract Not Found
```bash
# macOS
brew install tesseract

# Ubuntu/Debian
sudo apt-get install tesseract-ocr

# Verify installation
tesseract --version
```

#### 2. PaddlePaddle Installation Issues
```bash
# Uninstall existing versions
pip uninstall paddlepaddle paddlepaddle-gpu

# Install correct version
pip install paddlepaddle==3.0.0 -i https://www.paddlepaddle.org.cn/packages/stable/cpu/
```

#### 3. Large Model Downloads Time Out
The L11 notebook has been updated to use `all-MiniLM-L6-v2` instead of the larger BGE-M3 model for faster downloads.

#### 4. API Key Issues
```bash
# Check your .env file
cat .env

# Make sure it's formatted correctly:
VISION_AGENT_API_KEY=your_actual_key_here
```

## 📖 Lesson-by-Lesson Guide

### L2: Basic OCR with Tesseract
- **Focus**: Traditional OCR techniques
- **Skills**: Image preprocessing, text extraction, regex patterns
- **Output**: Structured text from invoices and receipts

### L4: Advanced OCR with PaddleOCR  
- **Focus**: Deep learning-based OCR
- **Skills**: Multi-language support, handwriting recognition
- **Output**: Better accuracy on complex documents

### L6: Layout Analysis
- **Focus**: Document structure understanding
- **Skills**: Reading order, layout detection
- **Output**: Structured document understanding

### L8: Agentic Document Extraction
- **Focus**: AI-powered extraction with LandingAI ADE
- **Skills**: Visual grounding, chunk detection
- **Output**: Structured data with bounding boxes

### L9: Batch Processing
- **Focus**: Processing multiple documents
- **Skills**: Parallel processing, error handling
- **Output**: Scalable document processing

### L11: RAG Pipeline
- **Focus**: Retrieval-Augmented Generation
- **Skills**: Vector databases, semantic search
- **Output**: Question-answering system

### Lab 6: AWS RAG Pipeline
- **Focus**: Production deployment
- **Skills**: Cloud services, serverless processing
- **Output**: Production-ready document AI system

## 🎯 Learning Path

1. **Start with L2** - Learn basic OCR concepts
2. **Progress to L4** - Improve accuracy with deep learning
3. **Move to L6** - Understand document layout
4. **Master L8/L9** - Build agentic extraction systems
5. **Complete L11** - Create RAG pipelines
6. **Deploy with Lab 6** - Production-ready systems

## 📞 Getting Help

- **Issues**: Report bugs on GitHub
- **Questions**: Check the README.md file
- **Documentation**: Each lesson has detailed explanations
- **Community**: Join discussions in GitHub Issues

## 🎉 Success Criteria

You're successful when you can:
- ✅ Extract text from various document types
- ✅ Handle complex layouts and tables
- ✅ Build agentic extraction systems
- ✅ Create RAG pipelines for document Q&A
- ✅ Deploy systems to production

Happy learning! 🚀
