"""
Shared document models between frontend and backend
"""
from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel


class OCREngine(str, Enum):
    """Available OCR engines"""
    TESSERACT = "tesseract"
    PADDLEOCR = "paddleocr"
    LANDINGAI = "landingai"
    DOCLING = "docling"


class DocumentType(str, Enum):
    """Document types"""
    PDF = "pdf"
    IMAGE = "image"
    UNKNOWN = "unknown"


class ChunkType(str, Enum):
    """Types of extracted chunks"""
    TEXT = "text"
    TABLE = "table"
    FIGURE = "figure"
    LOGO = "logo"
    FORM = "form"
    MARGINALIA = "marginalia"
    SCAN_CODE = "scan_code"
    ATTESTATION = "attestation"
    CARD = "card"


class BoundingBox(BaseModel):
    """Bounding box coordinates"""
    x0: float
    y0: float
    x1: float
    y1: float


class ExtractedChunk(BaseModel):
    """Extracted document chunk"""
    chunk_id: str
    chunk_type: ChunkType
    text: str
    bbox: Optional[BoundingBox] = None
    page: Optional[int] = None
    confidence: Optional[float] = None
    metadata: Optional[Dict[str, Any]] = None


class ProcessingResult(BaseModel):
    """Document processing result"""
    document_id: str
    ocr_engine: OCREngine
    processing_time: float
    success: bool
    error_message: Optional[str] = None
    
    # Extracted content
    markdown: Optional[str] = None
    raw_text: Optional[str] = None
    chunks: Optional[List[ExtractedChunk]] = None
    
    # Document metadata
    document_type: DocumentType
    page_count: Optional[int] = None
    file_size: int
    
    # Processing metadata
    created_at: Optional[str] = None
    model_version: Optional[str] = None
