# 📄 Document AI: Multi-Agent Document Extraction

A high-performance, agentic system for document intelligence. This project evolves from traditional OCR to a **Specialist Multi-Agent Pipeline** that classifies, extracts, and validates complex documents with high precision.

---

## 🚀 Key Features

*   **🤖 Multi-Agent Pipeline**: 5+ specialist agents (Classifier, OCR Quality, Field Extractor, Table Extractor, Validator) orchestrated via a concurrent `asyncio` workflow.
*   **📡 Hybrid OCR Engine**: Support for **TrOCR** (Handwriting), **Docling** (Structure), **LandingAI** (Visual Forms), and **Tesseract/PaddleOCR**.
*   **🎨 Agentic UI (React)**: An interactive frontend featuring a real-time **Agent Execution Trace** to visualize the pipeline's reasoning, confidence, and bottlenecks.
*   **⚡ Groq Integration**: Optimized for Llama 3 models with **429-fallback** logic and aggressive token trimming for free-tier resilience.
*   **📊 Structured Export**: Download results as **JSON, Markdown, or Section-Aware CSV**.

---

## 🏗️ Architecture: The Specialist Pipeline

Instead of a single "Extract everything" prompt, the system breaks the document down into specialized reasoning stages:

1.  **🔍 Classifier Agent**: Detects document type (Invoice, Prescription, etc.) and domain.
2.  **📡 OCR Quality Agent**: Assesses readability and flags "hallucination-prone" zones.
3.  **📑 Field Extractor**: Extracts key-value pairs grouped by semantic sections.
4.  **📊 Table Extractor**: Parses complex grids, CPT codes, and line-item totals.
5.  **✅ Validator**: Cross-checks data consistency (e.g., math verification, missing fields).
6.  **💬 Summary Agent**: Generates professional-grade summaries and actionable recommendations.

---

## 📂 Project Structure

```bash
.
├── document_ai_app/          # 🎯 Core Application
│   ├── backend/              # FastAPI + Specialist Agents
│   │   ├── services/         # multi_agent_service.py, ocr_service.py
│   │   ├── models/           # Pydantic (AgentStep, MultiAgentResult)
│   │   └── api/              # main.py
│   ├── frontend_react/       # Modern React UI (Vite)
│   ├── frontend/             # Streamlit (Legacy UI)
│   └── scripts/              # start_backend.sh, start_frontend.sh
├── L1 - L11/                 # 📚 Educational Labs (Learning Path)
├── venv/                     # Python Environment
├── .env                      # API Configuration
└── setup.sh                  # One-click environment setup
```

---

## 🔧 Installation & Setup

### 1. Requirements
*   Python 3.10+
*   Tesseract OCR (`brew install tesseract` on Mac)
*   **Groq API Key** (for multi-agent features)
*   **LandingAI API Key** (optional, for ADE features)

### 2. Quick Install
```bash
# Run the setup script to create venv and install all dependencies
./setup.sh
```

### 3. Environment Variables
Create a `.env` in the root (or `document_ai_app/.env`):
```env
GROQ_API_KEY=your_key_here
VISION_AGENT_API_KEY=your_landingai_key_here
LOG_LEVEL=INFO
```

### 4. Running the Application
```bash
cd document_ai_app

# Start Backend (Port 8000)
./scripts/start_backend.sh

# Start Frontend (Port 3000)
# In a new terminal:
cd frontend_react
npm install && npm run dev
```

---

## 📖 Educational Path (Labs)

This project started as a course exploring document AI. You can still find the core lessons in the root directory:

*   **L1-L4**: Foundational OCR (Tesseract, PaddleOCR).
*   **L6**: Layout Analysis & Reading Order.
*   **L8-L9**: Introduction to Agentic Extraction (ADE).
*   **L11**: RAG Pipeline with ChromaDB.

---

## 🤝 Contributing & Support
For detailed internal logic on the multi-agent system, refer to the [walkthrough.md](.agent/brain/walkthrough.md) (if available) or check the Specialist Agent implementations in `backend/services/multi_agent_service.py`.
