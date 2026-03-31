"""
Document-related data models
"""
from typing import List, Optional, Dict, Any, Union
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field


class OCREngine(str, Enum):
    """OCR engine types"""
    TESSERACT = "tesseract"
    TROCR     = "trocr"
    LANDINGAI = "landingai"
    DOCLING   = "docling"


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


class AgentStep(BaseModel):
    """Trace record for one agent in the multi-agent pipeline"""
    agent_name:     str   = Field(..., description="Agent identifier")
    role:           str   = Field(..., description="Agent role description")
    status:         str   = Field(..., description="success | error | skipped")
    confidence:     float = Field(..., description="Agent confidence 0-1")
    duration_ms:    int   = Field(..., description="Wall-clock duration in ms")
    output_summary: str   = Field(..., description="One-line human-readable summary")
    output:         Dict[str, Any] = Field(default_factory=dict, description="Agent's full output")
    error:          Optional[str]  = Field(None, description="Error detail if status=='error'")


class MultiAgentResult(BaseModel):
    """Aggregated result from the full multi-agent pipeline"""
    document_type:      str             = Field(...)
    domain:             str             = Field(...)
    summary:            str             = Field(...)
    key_insights:       List[str]       = Field(default_factory=list)
    extracted_fields:   List[Dict[str, Any]] = Field(default_factory=list)
    tables:             List[Dict[str, Any]] = Field(default_factory=list)
    validation_flags:   List[str]       = Field(default_factory=list)
    recommendations:    List[str]       = Field(default_factory=list)
    overall_confidence: float           = Field(0.0)
    agent_trace:        List[AgentStep] = Field(default_factory=list)
    processing_steps:   List[str]       = Field(default_factory=list)


class BoundingBox(BaseModel):
    """Bounding box coordinates"""
    x0: float = Field(..., description="Left coordinate (normalized 0-1)")
    y0: float = Field(..., description="Top coordinate (normalized 0-1)")
    x1: float = Field(..., description="Right coordinate (normalized 0-1)")
    y1: float = Field(..., description="Bottom coordinate (normalized 0-1)")


class ExtractedChunk(BaseModel):
    """Extracted document chunk"""
    chunk_id: str = Field(..., description="Unique chunk identifier")
    chunk_type: ChunkType = Field(..., description="Type of chunk")
    text: str = Field(..., description="Extracted text content")
    bbox: Optional[BoundingBox] = Field(None, description="Bounding box coordinates")
    page: Optional[int] = Field(None, description="Page number (0-indexed)")
    confidence: Optional[float] = Field(None, description="Confidence score (0-1)")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")


class ProcessingResult(BaseModel):
    """Document processing result"""
    document_id: str = Field(..., description="Document identifier")
    ocr_engine: OCREngine = Field(..., description="OCR engine used")
    processing_time: float = Field(..., description="Processing time in seconds")
    success: bool = Field(..., description="Processing success status")
    error: Optional[str] = Field(None, description="Error message if failed")
    ai_analysis: Optional[Dict[str, Any]] = Field(None, description="AI analysis (legacy)")
    multi_agent_result: Optional[Dict[str, Any]] = Field(None, description="Multi-agent pipeline result")

    # Extracted content
    markdown: Optional[str] = Field(None, description="Full document as markdown")
    raw_text: Optional[str] = Field(None, description="Raw extracted text")
    chunks: Optional[List[ExtractedChunk]] = Field(None, description="Extracted chunks")

    # Document metadata
    document_type: DocumentType = Field(..., description="Document type")
    page_count: Optional[int] = Field(None, description="Number of pages")
    file_size: int = Field(..., description="File size in bytes")

    # Processing metadata
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional processing metadata")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    model_version: Optional[str] = Field(None, description="Model version used")


class DocumentUpload(BaseModel):
    """Document upload request"""
    filename: str = Field(..., description="Original filename")
    file_size: int = Field(..., description="File size in bytes")
    content_type: str = Field(..., description="MIME type")
    ocr_engine: OCREngine = Field(default=OCREngine.TESSERACT, description="OCR engine to use")
    
    class Config:
        schema_extra = {
            "example": {
                "filename": "invoice.pdf",
                "file_size": 1024000,
                "content_type": "application/pdf",
                "ocr_engine": "landingai"
            }
        }


class ProcessingRequest(BaseModel):
    """Document processing request"""
    document_id: str = Field(..., description="Document identifier")
    ocr_engine: OCREngine = Field(default=OCREngine.TESSERACT, description="OCR engine to use")
    extract_tables: bool = Field(default=True, description="Extract tables")
    extract_figures: bool = Field(default=True, description="Extract figures")
    extract_forms: bool = Field(default=True, description="Extract forms")
    
    class Config:
        schema_extra = {
            "example": {
                "document_id": "doc_123",
                "ocr_engine": "landingai",
                "extract_tables": True,
                "extract_figures": True,
                "extract_forms": True
            }
        }


class APIResponse(BaseModel):
    """Standard API response"""
    success: bool = Field(..., description="Request success status")
    message: str = Field(..., description="Response message")
    data: Optional[Any] = Field(None, description="Response data")
    error: Optional[str] = Field(None, description="Error details")
    
    class Config:
        schema_extra = {
            "example": {
                "success": True,
                "message": "Document processed successfully",
                "data": {},
                "error": None
            }
        }


class HealthCheck(BaseModel):
    """Health check response"""
    status: str = Field(..., description="Service status")
    version: str = Field(..., description="API version")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    services: Dict[str, str] = Field(..., description="Service statuses")
