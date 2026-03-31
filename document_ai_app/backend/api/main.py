"""
FastAPI main application
"""
import sys
import os
from pathlib import Path

# Add the backend directory to Python path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

import logging
from fastapi import FastAPI, HTTPException, UploadFile, File, BackgroundTasks, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
import uvicorn

from core.config import settings
from models.document import APIResponse, HealthCheck, ProcessingRequest, OCREngine
from services.ocr_service import ocr_service
from utils.file_utils import (
    validate_file, create_upload_directory, 
    generate_unique_filename, cleanup_old_files
)

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Document AI API for OCR and document processing",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create upload directory
create_upload_directory(settings.UPLOAD_DIR)

# Serve static files
app.mount("/uploads", StaticFiles(directory=settings.UPLOAD_DIR), name="uploads")


@app.on_event("startup")
async def startup_event():
    """Application startup"""
    logger.info(f"Starting {settings.PROJECT_NAME} v{settings.VERSION}")
    
    # Clean up old files
    deleted_count = cleanup_old_files(settings.UPLOAD_DIR, max_age_hours=24)
    if deleted_count > 0:
        logger.info(f"Cleaned up {deleted_count} old files")


@app.on_event("shutdown")
async def shutdown_event():
    """Application shutdown"""
    logger.info(f"Shutting down {settings.PROJECT_NAME}")


@app.get("/", response_model=HealthCheck)
async def root():
    """Root endpoint"""
    return HealthCheck(
        status="healthy",
        version=settings.VERSION,
        services={
            "ocr": "available",
            "tesseract": "available",
            "paddleocr": "available" if ocr_service.paddle_ocr else "unavailable",
            "landingai": "available" if ocr_service.landingai_client else "unavailable"
        }
    )


@app.get("/health", response_model=HealthCheck)
async def health_check():
    """Health check endpoint"""
    return HealthCheck(
        status="healthy",
        version=settings.VERSION,
        services={
            "ocr": "available",
            "tesseract": "available",
            "paddleocr": "available" if ocr_service.paddle_ocr else "unavailable",
            "landingai": "available" if ocr_service.landingai_client else "unavailable"
        }
    )


@app.post("/api/v1/upload", response_model=APIResponse)
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    ocr_engine: str = Form(None),
    enable_ai_analysis: bool = Form(True)  # New parameter for AI analysis
):
    """
    Upload and process document
    
    Args:
        file: Document file to upload
        ocr_engine: OCR engine to use for processing
        
    Returns:
        APIResponse with processing result
    """
    try:
        # Validate file
        if not file.filename:
            raise HTTPException(status_code=400, detail="No file provided")
        
        # Validate OCR engine
        logger.info(f"Raw OCR engine parameter: {ocr_engine}")
        logger.info(f"OCR engine type: {type(ocr_engine)}")
        logger.info(f"Enable AI analysis parameter: {enable_ai_analysis}")
        logger.info(f"Enable AI analysis type: {type(enable_ai_analysis)}")
        
        if not ocr_engine:
            ocr_engine = OCREngine.TESSERACT  # Default fallback
            logger.info(f"No OCR engine specified, using default: {ocr_engine}")
        else:
            logger.info(f"Using specified OCR engine: {ocr_engine}")
            # Convert string to enum if needed
            if isinstance(ocr_engine, str):
                try:
                    ocr_engine = OCREngine(ocr_engine.lower())
                    logger.info(f"Converted string to enum: {ocr_engine}")
                except ValueError:
                    logger.warning(f"Invalid OCR engine '{ocr_engine}', using default")
                    ocr_engine = OCREngine.TESSERACT
        
        # Generate unique filename
        unique_filename = generate_unique_filename(file.filename)
        file_path = f"{settings.UPLOAD_DIR}/{unique_filename}"
        
        # Save uploaded file
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        # Validate saved file
        is_valid, error_message = validate_file(file_path, settings.MAX_FILE_SIZE)
        if not is_valid:
            # Clean up invalid file
            if os.path.exists(file_path):
                os.remove(file_path)
            raise HTTPException(status_code=400, detail=error_message)
        
        # Process document with AI analysis
        logger.info(f"Starting document processing with AI analysis: {enable_ai_analysis}")
        result = await ocr_service.process_document(
            file_path=file_path,
            ocr_engine=ocr_engine,
            enable_ai_analysis=enable_ai_analysis
        )
        
        # Schedule cleanup in background
        background_tasks.add_task(cleanup_old_files, settings.UPLOAD_DIR, 24)

        # Inject the actual filename into metadata so the frontend can
        # call /api/v1/documents/{file_name}/pages/{n} for PDF page preview
        result_data = result.model_dump()
        if result_data.get("metadata") is None:
            result_data["metadata"] = {}
        result_data["metadata"]["file_name"] = unique_filename

        return APIResponse(
            success=True,
            message="Document processed successfully",
            data=result_data
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing document: {e}")
        return APIResponse(
            success=False,
            message="Failed to process document",
            error=str(e)
        )


@app.post("/api/v1/process", response_model=APIResponse)
async def process_document(request: ProcessingRequest):
    """
    Process uploaded document with specified parameters
    
    Args:
        request: Processing request parameters
        
    Returns:
        APIResponse with processing result
    """
    try:
        # Find uploaded file
        file_path = f"{settings.UPLOAD_DIR}/{request.document_id}"
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="Document not found")
        
        # Process document
        result = await ocr_service.process_document(
            file_path=file_path,
            ocr_engine=request.ocr_engine,
            extract_tables=request.extract_tables,
            extract_figures=request.extract_figures,
            extract_forms=request.extract_forms
        )
        
        return APIResponse(
            success=True,
            message="Document processed successfully",
            data=result.model_dump()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing document: {e}")
        return APIResponse(
            success=False,
            message="Failed to process document",
            error=str(e)
        )


@app.get("/api/v1/engines")
async def get_available_engines():
    """Get available OCR engines"""
    logger.info("🔧 Engines endpoint called - returning OCR engine status")
    
    engines = {
        "tesseract": {
            "name": "Tesseract",
            "description": "Traditional OCR engine",
            "available": True,
            "recommended_for": ["simple_documents", "printed_text"]
        },
        "paddleocr": {
            "name": "PaddleOCR",
            "description": "Deep learning-based OCR",
            "available": ocr_service.paddle_ocr is not None,
            "recommended_for": ["complex_layouts", "handwriting", "multiple_languages"]
        },
        "landingai": {
            "name": "LandingAI ADE",
            "description": "AI-powered agentic document extraction",
            "available": ocr_service.landingai_client is not None,
            "recommended_for": ["complex_documents", "tables", "forms", "structured_extraction"]
        }
    }
    
    response = APIResponse(
        success=True,
        message="Available OCR engines",
        data=engines
    )
    
    logger.info(f"✅ Engines response: {response}")
    return response


@app.get("/api/v1/documents/{document_id}")
async def get_document_result(document_id: str):
    """Get processing result for a specific document"""
    file_path = f"{settings.UPLOAD_DIR}/{document_id}"
    
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Document not found")
    
    # For now, return file info. In a real app, you'd store results in a database
    from ..utils.file_utils import get_file_size, get_content_type, get_document_type
    
    return APIResponse(
        success=True,
        message="Document found",
        data={
            "document_id": document_id,
            "file_size": get_file_size(file_path),
            "content_type": get_content_type(file_path),
            "document_type": get_document_type(file_path).value
        }
    )


@app.get("/api/v1/documents/{document_id}/page_count")
async def get_document_page_count(document_id: str):
    """Return the total number of pages in a PDF document."""
    # Strip query suffix if any (document_id may have the original filename appended)
    file_path = f"{settings.UPLOAD_DIR}/{document_id}"
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Document not found")

    ext = os.path.splitext(file_path)[1].lower()
    if ext != ".pdf":
        return APIResponse(success=True, message="Not a PDF", data={"page_count": 1})

    try:
        import fitz  # pymupdf
        doc = fitz.open(file_path)
        count = doc.page_count
        doc.close()
        return APIResponse(success=True, message="Page count", data={"page_count": count})
    except Exception as e:
        logger.error(f"Error getting page count: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/documents/{document_id}/pages/{page_num}")
async def get_document_page_image(document_id: str, page_num: int, dpi: int = 150):
    """
    Render a single PDF page as a PNG image.
    Returns base64-encoded PNG image data.
    page_num is 0-indexed.
    """
    from fastapi.responses import Response

    file_path = f"{settings.UPLOAD_DIR}/{document_id}"
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Document not found")

    ext = os.path.splitext(file_path)[1].lower()
    if ext != ".pdf":
        raise HTTPException(status_code=400, detail="File is not a PDF")

    try:
        import fitz  # pymupdf
        doc = fitz.open(file_path)
        if page_num < 0 or page_num >= doc.page_count:
            raise HTTPException(status_code=404, detail=f"Page {page_num} not found (doc has {doc.page_count} pages)")

        page = doc[page_num]
        zoom = dpi / 72  # 72 dpi is PyMuPDF default
        mat = fitz.Matrix(zoom, zoom)
        pix = page.get_pixmap(matrix=mat, alpha=False)
        img_bytes = pix.tobytes("png")
        doc.close()
        return Response(content=img_bytes, media_type="image/png")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error rendering PDF page: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler"""
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "message": "Internal server error",
            "error": str(exc) if settings.DEBUG else "An unexpected error occurred"
        }
    )


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower()
    )
