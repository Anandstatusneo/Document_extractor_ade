"""
OCR Service with AI Agent Integration
"""
import logging
import asyncio
import time
import uuid
import io
import os
import dataclasses
from pathlib import Path
from typing import List, Dict, Any, Optional

# OCR imports
try:
    import pytesseract
    from PIL import Image
    TESSERACT_AVAILABLE = True
except ImportError:
    TESSERACT_AVAILABLE = False

# TrOCR – Microsoft's Transformer OCR for handwriting
try:
    from transformers import TrOCRProcessor, VisionEncoderDecoderModel
    TROCR_AVAILABLE = True
except ImportError:
    TROCR_AVAILABLE = False

try:
    from landingai_ade import LandingAIADE
    LANDINGAI_AVAILABLE = True
except ImportError:
    LANDINGAI_AVAILABLE = False

try:
    from docling.document_converter import DocumentConverter
    from docling.datamodel.base_models import InputFormat
    from docling.datamodel.pipeline_options import PdfPipelineOptions
    from docling.backend.pypdfium2_backend import PyPdfiumDocumentBackend
    DOCLING_AVAILABLE = True
except ImportError:
    DOCLING_AVAILABLE = False

# Image processing
try:
    import fitz  # PyMuPDF
    PYPDF_AVAILABLE = True
except ImportError:
    PYPDF_AVAILABLE = False

try:
    from paddleocr import PaddleOCR
    PADDLEOCR_AVAILABLE = True
except ImportError:
    PADDLEOCR_AVAILABLE = False

from core.config import settings
from models.document import OCREngine, ExtractedChunk, ProcessingResult, DocumentType, ChunkType, BoundingBox
from services.ai_agent_service import ai_agent_service
from services.multi_agent_service import multi_agent_service

logger = logging.getLogger(__name__)


# Helper functions for image and PDF processing
def convert_pdf_to_images(file_path: str) -> list:
    """Convert PDF to list of images"""
    if not PYPDF_AVAILABLE:
        raise ImportError("PyMuPDF is required for PDF processing")
    
    doc = fitz.open(file_path)
    images = []
    
    for page_num in range(len(doc)):
        page = doc.load_page(page_num)
        pix = page.get_pixmap()
        img_data = pix.tobytes("png")
        image = Image.open(io.BytesIO(img_data))
        images.append(image)
    
    doc.close()
    return images


def preprocess_image(file_path: str) -> Image.Image:
    """Preprocess image for OCR"""
    if not TESSERACT_AVAILABLE:
        raise ImportError("PIL is required for image processing")
    
    image = Image.open(file_path)
    
    # Convert to RGB if necessary
    if image.mode != 'RGB':
        image = image.convert('RGB')
    
    return image


class OCRService:
    """OCR processing service with multiple engine support"""
    
    def __init__(self):
        self.trocr_processor = None
        self.trocr_model = None
        self.landingai_client = None
        self.docling_converter = None
        self.paddle_ocr = None
        self._init_engines()
    
    def _init_engines(self):
        """Initialize OCR engines"""
        # ── TrOCR ───────────────────────────────────────────────────
        # Model is loaded lazily on first call to avoid blocking startup
        if TROCR_AVAILABLE:
            logger.info("TrOCR (transformers) is available – model will load on first use")
        else:
            logger.warning("TrOCR not available – install: pip install transformers torch")

        try:
            # Initialize LandingAI ADE
            if LANDINGAI_AVAILABLE and settings.VISION_AGENT_API_KEY:
                self.landingai_client = LandingAIADE(
                    apikey=settings.VISION_AGENT_API_KEY
                )
                logger.info("LandingAI ADE initialized successfully")
            else:
                if not LANDINGAI_AVAILABLE:
                    logger.warning("LandingAI not available, install landingai-ade")
                else:
                    logger.warning("VISION_AGENT_API_KEY not found, LandingAI ADE disabled")
                self.landingai_client = None
        except Exception as e:
            logger.warning(f"Failed to initialize LandingAI ADE: {e}")
            self.landingai_client = None
        
        try:
            # Initialize Docling
            if DOCLING_AVAILABLE:
                pipeline_options = PdfPipelineOptions()
                pipeline_options.do_ocr = True
                pipeline_options.do_table_structure = True
                
                self.docling_converter = DocumentConverter(
                    format_options={
                        InputFormat.PDF: pipeline_options,
                    }
                )
                logger.info("Docling initialized successfully with enhanced configuration")
            else:
                logger.warning("Docling not available, install docling")
                self.docling_converter = None
        except Exception as e:
            logger.warning(f"Failed to initialize Docling: {e}")
            self.docling_converter = None
        
        try:
            # Initialize PaddleOCR
            if PADDLEOCR_AVAILABLE:
                self.paddle_ocr = PaddleOCR(use_angle_cls=True, lang='en', show_log=False)
                logger.info("PaddleOCR initialized successfully")
            else:
                logger.warning("PaddleOCR not available, install paddleocr paddlepaddle")
                self.paddle_ocr = None
        except Exception as e:
            logger.warning(f"Failed to initialize PaddleOCR: {e}")
            self.paddle_ocr = None
    
    async def process_document(
        self, 
        file_path: str, 
        ocr_engine: OCREngine = OCREngine.TESSERACT,
        extract_tables: bool = True,
        extract_figures: bool = True,
        extract_forms: bool = True,
        enable_ai_analysis: bool = True
    ) -> ProcessingResult:
        """
        Process document with specified OCR engine
        
        Args:
            file_path: Path to document file
            ocr_engine: OCR engine to use
            extract_tables: Whether to extract tables
            extract_figures: Whether to extract figures
            extract_forms: Whether to extract forms
            enable_ai_analysis: Whether to enable AI analysis
            
        Returns:
            ProcessingResult with extracted data and AI insights
        """
        start_time = time.time()
        document_id = str(uuid.uuid4())
        
        # Determine document type and file size
        document_type = self._get_document_type(file_path)
        file_size = os.path.getsize(file_path)
        
        try:
            logger.info(f"Processing document {document_id} with {ocr_engine}")
            
            # Route to appropriate OCR engine
            if ocr_engine == OCREngine.TESSERACT:
                result = await self._process_with_tesseract(file_path, document_id, document_type, file_size, start_time)
            elif ocr_engine == OCREngine.TROCR:
                result = await self._process_with_trocr(file_path, document_id, document_type, file_size, start_time)
            elif ocr_engine == OCREngine.LANDINGAI:
                result = await self._process_with_landingai(file_path, document_id, document_type, file_size, start_time, extract_tables, extract_figures, extract_forms)
            elif ocr_engine == OCREngine.DOCLING:
                result = await self._process_with_docling(file_path, document_id, document_type, file_size, start_time)
            else:
                raise ValueError(f"Unsupported OCR engine: {ocr_engine}")
            
            # Perform AI analysis if enabled
            ai_analysis = None
            logger.info(f"AI analysis enabled: {enable_ai_analysis}")
            
            if enable_ai_analysis and result.success:
                try:
                    # Primary: extract text from structured chunks (with page headers)
                    text_content = self._extract_text_content(result.chunks)
                    logger.info(f"Text from chunks: {len(text_content)} chars, {len(result.chunks)} chunks")

                    # Fallback 1: use raw_text assembled from per-page markdown
                    if not text_content.strip() and result.raw_text:
                        text_content = result.raw_text
                        logger.info(f"Fallback to raw_text: {len(text_content)} chars")

                    # Fallback 2: use markdown
                    if not text_content.strip() and result.markdown:
                        text_content = result.markdown
                        logger.info(f"Fallback to markdown: {len(text_content)} chars")

                    logger.info(f"Final text content for AI: {len(text_content)} chars")

                    # ── Run legacy single-prompt + multi-agent pipeline concurrently ──
                    legacy_task = ai_agent_service.analyze_document_intelligently(
                        ocr_result=result.model_dump(),
                        document_content=text_content,
                    )
                    multi_task = multi_agent_service.run(text_content)

                    ai_analysis, ma_result = await asyncio.gather(
                        legacy_task, multi_task, return_exceptions=True
                    )

                    # Store legacy result
                    if isinstance(ai_analysis, Exception):
                        logger.error(f"Legacy AI analysis error: {ai_analysis}")
                        result.ai_analysis = None
                    else:
                        result.ai_analysis = dataclasses.asdict(ai_analysis)
                        logger.info("Legacy AI analysis completed")

                    # Store multi-agent result
                    if isinstance(ma_result, Exception):
                        logger.error(f"Multi-agent pipeline error: {ma_result}")
                        result.multi_agent_result = None
                    else:
                        import dataclasses as _dc
                        from services.multi_agent_service import AgentStep as _AS
                        # Serialize dataclasses to dicts
                        def _ser(obj):
                            if _dc.is_dataclass(obj) and not isinstance(obj, type):
                                return _dc.asdict(obj)
                            return obj
                        result.multi_agent_result = {
                            "document_type":     ma_result.document_type,
                            "domain":            ma_result.domain,
                            "summary":           ma_result.summary,
                            "key_insights":      ma_result.key_insights,
                            "extracted_fields":  ma_result.extracted_fields,
                            "tables":            ma_result.tables,
                            "validation_flags":  ma_result.validation_flags,
                            "recommendations":   ma_result.recommendations,
                            "overall_confidence": ma_result.overall_confidence,
                            "agent_trace":       [_ser(s) for s in ma_result.agent_trace],
                            "processing_steps":  ma_result.processing_steps,
                        }
                        logger.info(f"Multi-agent pipeline: {len(ma_result.agent_trace)} agents, confidence={ma_result.overall_confidence:.2f}")

                except Exception as e:
                    logger.error(f"Error during AI analysis: {e}")
                    result.ai_analysis = None
                    result.multi_agent_result = None
            
            # Enrich metadata with the actual filename so the frontend can
            # call /api/v1/documents/{file_name}/pages/{n} to preview pages
            file_name = Path(file_path).name
            if result.metadata is None:
                result.metadata = {}
            result.metadata["file_name"] = file_name

            return result
            
        except Exception as e:
            logger.error(f"Error processing document: {e}")
            return ProcessingResult(
                document_id=document_id,
                ocr_engine=ocr_engine.value,
                processing_time=time.time() - start_time,
                chunks=[],
                success=False,
                error=str(e),
                document_type=document_type,
                file_size=file_size,
                page_count=1
            )
    
    def _get_document_type(self, file_path: str) -> DocumentType:
        """Determine document type from file extension"""
        file_ext = Path(file_path).suffix.lower()
        if file_ext == '.pdf':
            return DocumentType.PDF
        elif file_ext in ['.png', '.jpg', '.jpeg', '.tiff', '.bmp', '.gif']:
            return DocumentType.IMAGE
        else:
            return DocumentType.UNKNOWN
    
    def _extract_text_content(self, chunks: list) -> str:
        """Extract and organise text from chunks, grouped by page.

        Emits '=== PAGE N ===' headers so the AI prompt receives properly
        structured multi-page content rather than a single merged string.
        """
        from collections import defaultdict
        pages: dict = defaultdict(list)

        for chunk in chunks:
            if chunk.text and chunk.text.strip():
                page_num = getattr(chunk, "page", 0) or 0
                pages[page_num].append(chunk.text.strip())

        if not pages:
            return ""

        parts = []
        for page_num in sorted(pages.keys()):
            parts.append(f"\n=== PAGE {page_num} ===\n")
            parts.extend(pages[page_num])

        return "\n".join(parts)
    
    async def _process_with_trocr(
        self, file_path: str, document_id: str, document_type: DocumentType, file_size: int, start_time: float
    ) -> ProcessingResult:
        """Process document with TrOCR (microsoft/trocr-large-handwritten).

        TrOCR is a Transformer-based OCR model fine-tuned for handwritten AND
        printed text. Each PDF page is converted to a PIL image, split into
        line-height strips if needed, then decoded into text. The LLM
        (ai_agent_service / Groq) is called afterwards for structured data
        extraction and field-level confidence.
        """
        if not TROCR_AVAILABLE:
            return ProcessingResult(
                document_id=document_id,
                ocr_engine=OCREngine.TROCR.value,
                processing_time=time.time() - start_time,
                success=False,
                error="TrOCR not installed. Run: pip install transformers torch",
                document_type=document_type,
                file_size=file_size,
                page_count=1,
            )

        try:
            # ── Lazy-load model (cached after first call) ────────────────
            if self.trocr_processor is None or self.trocr_model is None:
                logger.info("Loading TrOCR model: microsoft/trocr-large-handwritten")
                self.trocr_processor = TrOCRProcessor.from_pretrained(
                    "microsoft/trocr-large-handwritten"
                )
                self.trocr_model = VisionEncoderDecoderModel.from_pretrained(
                    "microsoft/trocr-large-handwritten"
                )
                logger.info("TrOCR model loaded successfully")

            import torch
            device = "cuda" if torch.cuda.is_available() else "cpu"
            self.trocr_model.to(device)  # type: ignore

            # ── Build page image list ─────────────────────────────────
            file_ext = Path(file_path).suffix.lower()
            page_pil_images: list[tuple[int, Image.Image]] = []

            if file_ext == ".pdf" and PYPDF_AVAILABLE:
                doc = fitz.open(file_path)
                for page_num in range(len(doc)):
                    page  = doc.load_page(page_num)
                    pix   = page.get_pixmap(dpi=200)
                    img   = Image.open(io.BytesIO(pix.tobytes("png"))).convert("RGB")
                    page_pil_images.append((page_num + 1, img))
                doc.close()
                logger.info(f"TrOCR: converted {len(page_pil_images)} PDF pages")
            else:
                img = Image.open(file_path).convert("RGB")
                page_pil_images.append((1, img))

            total_pages = len(page_pil_images)
            all_text: list[str] = []
            chunks: list       = []

            # ── Run TrOCR per page ───────────────────────────────────
            for page_num, pil_img in page_pil_images:
                try:
                    # TrOCR processes one image patch at a time;
                    # we split a tall page into 384-px horizontal strips
                    # that match the model's expected patch size.
                    w, h      = pil_img.size
                    strip_h   = 384
                    page_lines: list[str] = []

                    for y_start in range(0, h, strip_h):
                        strip = pil_img.crop((0, y_start, w, min(y_start + strip_h, h)))
                        pixel_values = self.trocr_processor(
                            images=strip, return_tensors="pt"
                        ).pixel_values.to(device)

                        with torch.no_grad():
                            generated_ids = self.trocr_model.generate(pixel_values)  # type: ignore

                        line_text = self.trocr_processor.batch_decode(
                            generated_ids, skip_special_tokens=True
                        )[0].strip()

                        if line_text:
                            page_lines.append(line_text)

                    page_text = "\n".join(page_lines)
                    if page_text.strip():
                        all_text.append(page_text)
                        chunks.append(ExtractedChunk(
                            chunk_id=f"{document_id}_trocr_p{page_num}",
                            chunk_type=ChunkType.TEXT,
                            text=page_text,
                            page=page_num,
                            confidence=0.90,
                        ))
                        logger.info(f"TrOCR page {page_num}/{total_pages}: {len(page_text)} chars")
                    else:
                        logger.warning(f"TrOCR returned empty text for page {page_num}")

                except Exception as page_err:
                    logger.error(f"TrOCR error on page {page_num}: {page_err}")

            full_text        = "\n\n".join(all_text)
            processing_time  = time.time() - start_time

            if not full_text.strip():
                return ProcessingResult(
                    document_id=document_id,
                    ocr_engine=OCREngine.TROCR.value,
                    processing_time=processing_time,
                    success=False,
                    error="TrOCR returned no text. Ensure the image quality is sufficient.",
                    document_type=document_type,
                    file_size=file_size,
                    page_count=total_pages,
                )

            return ProcessingResult(
                document_id=document_id,
                ocr_engine=OCREngine.TROCR.value,
                processing_time=processing_time,
                success=True,
                raw_text=full_text,
                markdown=full_text,
                chunks=chunks,
                document_type=document_type,
                file_size=file_size,
                page_count=total_pages,
            )

        except Exception as e:
            logger.error(f"TrOCR processing error: {e}")
            return ProcessingResult(
                document_id=document_id,
                ocr_engine=OCREngine.TROCR.value,
                processing_time=time.time() - start_time,
                chunks=[],
                success=False,
                error=f"TrOCR error: {str(e)}",
                document_type=document_type,
                file_size=file_size,
                page_count=1,
            )


    async def _process_with_tesseract(
        self, file_path: str, document_id: str, document_type: DocumentType, file_size: int, start_time: float
    ) -> ProcessingResult:
        """Process document with Tesseract OCR"""
        images = []
        
        # Determine document type
        from pathlib import Path
        file_ext = Path(file_path).suffix.lower()
        
        if file_ext == '.pdf':
            images = convert_pdf_to_images(file_path)
        else:
            images = [preprocess_image(file_path)]
        
        all_text = []
        chunks = []
        
        for page_num, image in enumerate(images):
            # Extract text
            text = pytesseract.image_to_string(image)
            all_text.append(text)
            
            # Create simple chunk
            chunk = ExtractedChunk(
                chunk_id=f"{document_id}_page_{page_num}",
                chunk_type=ChunkType.TEXT,
                text=text.strip(),
                page=page_num,
                confidence=0.8  # Tesseract doesn't provide confidence easily
            )
            chunks.append(chunk)
        
        processing_time = time.time() - start_time
        
        return ProcessingResult(
            document_id=document_id,
            ocr_engine=OCREngine.TESSERACT.value,
            processing_time=processing_time,
            success=True,
            markdown="\n\n".join(all_text),
            raw_text="\n".join(all_text),
            chunks=chunks,
            document_type=document_type,
            file_size=file_size,
            page_count=len(images)
        )
    
    async def _process_with_paddleocr(
        self, file_path: str, document_id: str,
        document_type: DocumentType, file_size: int, start_time: float
    ) -> ProcessingResult:
        """Process document with PaddleOCR"""
        if not self.paddle_ocr:
            logger.error("PaddleOCR not initialized")
            return ProcessingResult(
                document_id=document_id,
                ocr_engine=OCREngine.PADDLEOCR.value,
                processing_time=time.time() - start_time,
                success=False,
                error="PaddleOCR not available or not initialized",
                document_type=document_type,
                file_size=file_size,
                page_count=1
            )
        
        # Convert PDF to images or process single image
        images = []
        if document_type == DocumentType.PDF:
            if PYPDF_AVAILABLE:
                images = convert_pdf_to_images(file_path)
            else:
                logger.error("PyMuPDF not available for PDF processing")
                return ProcessingResult(
                    document_id=document_id,
                    ocr_engine=OCREngine.PADDLEOCR.value,
                    processing_time=time.time() - start_time,
                    chunks=[],
                    success=False,
                    error="PyMuPDF not available for PDF processing",
                    document_type=document_type,
                    file_size=file_size,
                    page_count=1
                )
        else:
            if TESSERACT_AVAILABLE:
                images = [preprocess_image(file_path)]
            else:
                logger.error("PIL not available for image processing")
                return ProcessingResult(
                    document_id=document_id,
                    ocr_engine=OCREngine.PADDLEOCR.value,
                    processing_time=time.time() - start_time,
                    success=False,
                    error="Image processing libraries not available",
                    document_type=document_type,
                    file_size=file_size,
                    page_count=1
                )
        
        all_text = []
        chunks = []
        
        try:
            for page_num, image in enumerate(images):
                # Extract text with PaddleOCR
                result = self.paddle_ocr.ocr(str(image), cls=True)
                
                if result and len(result) > 0:
                    page_text = []
                    for line in result:
                        if line and len(line) > 0:
                            for word_info in line:
                                if word_info and len(word_info) >= 2:
                                    text = word_info[1][0]
                                    bbox_coords = word_info[0]
                                    
                                    if text.strip():
                                        page_text.append(text)
                                        
                                        # Create chunk
                                        chunk = ExtractedChunk(
                                            chunk_id=f"{document_id}_paddle_{page_num}_{len(chunks)}",
                                            chunk_type=ChunkType.TEXT,
                                            text=text.strip(),
                                            page=page_num + 1,
                                            confidence=0.8,  # PaddleOCR doesn't provide confidence easily
                                            bbox=BoundingBox(
                                                x1=bbox_coords[0][0],
                                                y1=bbox_coords[0][1],
                                                x2=bbox_coords[2][0],
                                                y2=bbox_coords[2][1]
                                            ) if len(bbox_coords) == 4 else None
                                        )
                                        chunks.append(chunk)
                    
                    all_text.extend(page_text)
            
            processing_time = time.time() - start_time
            
            return ProcessingResult(
                document_id=document_id,
                ocr_engine=OCREngine.PADDLEOCR.value,
                processing_time=processing_time,
                chunks=chunks,
                success=True,
                markdown=" ".join(all_text),
                raw_text=" ".join(all_text),
                document_type=document_type,
                page_count=len(images),
                file_size=file_size
            )
            
        except Exception as e:
            logger.error(f"Error processing with PaddleOCR: {e}")
            return ProcessingResult(
                document_id=document_id,
                ocr_engine=OCREngine.PADDLEOCR.value,
                processing_time=time.time() - start_time,
                chunks=[],
                success=False,
                error=f"PaddleOCR processing error: {str(e)}",
                document_type=document_type,
                file_size=file_size,
                page_count=1
            )
    
    async def _process_with_landingai(
        self, file_path: str, document_id: str,
        document_type: DocumentType, file_size: int, start_time: float,
        extract_tables: bool, extract_figures: bool, extract_forms: bool
    ) -> ProcessingResult:
        """Process document with LandingAI ADE"""
        if not self.landingai_client:
            return ProcessingResult(
                document_id=document_id,
                ocr_engine=OCREngine.LANDINGAI.value,
                processing_time=time.time() - start_time,
                success=False,
                error="LandingAI ADE not initialized",
                document_type=document_type,
                file_size=file_size,
                page_count=1
            )
        
        try:
            # Enhanced PDF processing for better extraction (inspired by L8 notebook)
            chunks = []
            markdown = ""
            response_metadata = None
            
            if document_type == DocumentType.PDF:
                # Pass PDF directly to LandingAI ADE (as shown in L9 notebook)
                # ADE handles PDFs natively with split="page" for per-page processing
                from pathlib import Path
                pdf_path = Path(file_path)
                
                logger.info(f"Processing PDF directly with DPT-2 model: {pdf_path.name}")
                response = self.landingai_client.parse(
                    document=pdf_path,
                    split="page",  # Per-page processing (from L9 notebook)
                    model="dpt-2-latest"
                )
                
                # Store metadata
                if hasattr(response, 'metadata'):
                    response_metadata = response.metadata
                
                all_chunks = []
                all_text = []

                # Process splits if available (per-page results)
                if hasattr(response, 'splits') and response.splits:
                    total_pages = len(response.splits)
                    for page_num, split in enumerate(response.splits):
                        try:
                            page_md = ""
                            # Extract markdown from each page split
                            if hasattr(split, 'markdown') and split.markdown:
                                import re
                                page_md = re.sub(r'<a id=[\'"][^\'"]*[\'"]></a>', '', split.markdown)
                                page_md = re.sub(r'::<[^>]*::>', '', page_md)
                                page_md = page_md.strip()
                                all_text.append(page_md)

                            # Try to get structured chunks from the split
                            page_chunks = self._extract_chunks_from_landingai_response(
                                split, document_id, page_num + 1
                            )

                            # Guaranteed fallback: always make at least one text chunk per page
                            # using the markdown content, so chunks are never empty
                            if not page_chunks and page_md:
                                page_chunks = [ExtractedChunk(
                                    chunk_id=f"{document_id}_page_{page_num + 1}_text",
                                    chunk_type=ChunkType.TEXT,
                                    text=page_md,
                                    page=page_num + 1,
                                    confidence=0.9,
                                )]
                                logger.info(f"Page {page_num + 1}/{total_pages}: created 1 text chunk from markdown ({len(page_md)} chars)")
                            else:
                                logger.info(f"Page {page_num + 1}/{total_pages}: {len(page_chunks)} structured chunks")

                            all_chunks.extend(page_chunks)
                        except Exception as e:
                            logger.warning(f"Error processing page split {page_num + 1}: {e}")
                            continue

                # If per-split chunk extraction yielded nothing, fall back to full-response chunks
                if not all_chunks:
                    all_chunks = self._extract_chunks_from_landingai_response(response, document_id, 1)

                # Also get markdown from the top-level response if per-page text is empty
                if not all_text and hasattr(response, 'markdown') and response.markdown:
                    import re
                    md = re.sub(r'<a id=[\'"][^\'\"]*[\'"]></a>', '', response.markdown)
                    md = re.sub(r'::<[^>]*::>', '', md)
                    all_text.append(md)
                
                markdown = "\n\n".join(all_text)
                chunks = all_chunks
                
            else:
                # Process non-PDF files with DPT-2 model
                logger.info("Processing non-PDF document with DPT-2 model")
                with open(file_path, 'rb') as f:
                    response = self.landingai_client.parse(
                        document=f.read(),
                        model="dpt-2-latest"  # Use the latest DPT-2 model
                    )
                
                # Store metadata
                if hasattr(response, 'metadata'):
                    response_metadata = response.metadata
                
                # Extract chunks from response
                chunks = self._extract_chunks_from_landingai_response(response, document_id, 1)
                
                # Get markdown content
                markdown = getattr(response, 'markdown', '')
                if markdown:
                    # Clean markdown content
                    import re
                    markdown = re.sub(r'<a id=[\'"][^\'"]*[\'"]></a>', '', markdown)
                    markdown = re.sub(r'::<[^>]*::>', '', markdown)
            
            processing_time = time.time() - start_time
            
            # Enhanced result with metadata
            result = ProcessingResult(
                document_id=document_id,
                ocr_engine=OCREngine.LANDINGAI.value,
                processing_time=processing_time,
                success=True,
                markdown=markdown,
                raw_text=markdown,
                chunks=chunks,
                document_type=document_type,
                page_count=len(response.splits) if (document_type == DocumentType.PDF and hasattr(response, 'splits') and response.splits) else 1,
                file_size=file_size,
                model_version="dpt-2-latest"  # Track model version
            )
            
            # Add enhanced metadata if available
            if response_metadata:
                result.metadata = {
                    "job_id": getattr(response_metadata, 'job_id', None),
                    "duration_ms": getattr(response_metadata, 'duration_ms', None),
                    "total_chunks": len(chunks),
                    "model": "dpt-2-latest"
                }
            
            logger.info(f"LandingAI processing completed: {len(chunks)} chunks, {processing_time:.2f}s")
            return result
            
        except Exception as e:
            logger.error(f"Error processing with LandingAI: {e}")
            return ProcessingResult(
                document_id=document_id,
                ocr_engine=OCREngine.LANDINGAI.value,
                processing_time=time.time() - start_time,
                chunks=[],
                success=False,
                error=f"LandingAI processing error: {str(e)}",
                document_type=document_type,
                file_size=file_size,
                page_count=1
            )
    
    def _extract_chunks_from_landingai_response(self, response, document_id: str, page_num: int) -> List[ExtractedChunk]:
        """Extract chunks from LandingAI response with enhanced processing"""
        chunks = []
        
        if hasattr(response, 'chunks') and response.chunks:
            for chunk_data in response.chunks:
                # Enhanced chunk type mapping from L8 notebook
                chunk_type_mapping = {
                    'chunkText': ChunkType.TEXT,
                    'chunkTable': ChunkType.TABLE,
                    'chunkFigure': ChunkType.FIGURE,
                    'chunkLogo': ChunkType.LOGO,
                    'chunkForm': ChunkType.FORM,
                    'chunkMarginalia': ChunkType.MARGINALIA,
                    'chunkScanCode': ChunkType.SCAN_CODE,
                    'chunkAttestation': ChunkType.ATTESTATION,
                    'chunkCard': ChunkType.CARD,
                    # Additional types from L8 notebook
                    'text': ChunkType.TEXT,
                    'table': ChunkType.TABLE,
                    'figure': ChunkType.FIGURE,
                    'logo': ChunkType.LOGO,
                    'form': ChunkType.FORM,
                    'marginalia': ChunkType.MARGINALIA,
                    'scan_code': ChunkType.SCAN_CODE,
                    'attestation': ChunkType.ATTESTATION,
                    'card': ChunkType.CARD
                }
                
                # Get chunk type with fallback
                chunk_type_str = getattr(chunk_data, 'type', getattr(chunk_data, 'chunk_type', 'text'))
                chunk_type = chunk_type_mapping.get(chunk_type_str, ChunkType.TEXT)
                
                # Enhanced bounding box conversion
                bbox = None
                if hasattr(chunk_data, 'grounding') and hasattr(chunk_data.grounding, 'box'):
                    box = chunk_data.grounding.box
                    if hasattr(box, 'bottom') and hasattr(box, 'left') and hasattr(box, 'right') and hasattr(box, 'top'):
                        bbox = BoundingBox(
                            x0=float(box.left),
                            y0=float(box.top), 
                            x1=float(box.right),
                            y1=float(box.bottom)
                        )
                elif hasattr(chunk_data, 'bbox') and chunk_data.bbox:
                    if len(chunk_data.bbox) == 4:
                        bbox = BoundingBox(
                            x0=float(chunk_data.bbox[0]),
                            y0=float(chunk_data.bbox[1]),
                            x1=float(chunk_data.bbox[2]),
                            y1=float(chunk_data.bbox[3])
                        )
                
                # Enhanced text extraction with markdown processing
                text = getattr(chunk_data, 'text', '')
                markdown_content = getattr(chunk_data, 'markdown', '')
                
                # Use markdown if available, otherwise use text
                content = markdown_content if markdown_content else text
                
                # Clean up content (remove special markdown tags)
                if content:
                    # Remove chunk ID references
                    import re
                    content = re.sub(r'<a id=[\'"][^\'"]*[\'"]></a>', '', content)
                    # Remove special tags like ::logo::, ::figure:: etc.
                    content = re.sub(r'::<[^>]*::>', '', content)
                    # Clean up extra whitespace
                    content = re.sub(r'\n\s*\n', '\n', content).strip()
                
                # Get page number from grounding or default to provided page_num
                chunk_page = page_num
                if hasattr(chunk_data, 'grounding') and hasattr(chunk_data.grounding, 'page'):
                    chunk_page = chunk_data.grounding.page + 1  # Convert to 1-based indexing
                
                # Get confidence score
                confidence = getattr(chunk_data, 'confidence', None)
                if confidence is None and hasattr(chunk_data, 'score'):
                    confidence = chunk_data.score
                
                chunk = ExtractedChunk(
                    chunk_id=getattr(chunk_data, 'id', f"{document_id}_{len(chunks)}"),
                    chunk_type=chunk_type,
                    text=content,
                    bbox=bbox,
                    page=chunk_page,
                    confidence=confidence
                )
                chunks.append(chunk)
        
        return chunks
    
    async def _process_with_docling(
        self, file_path: str, document_id: str,
        document_type: DocumentType, file_size: int, start_time: float
    ) -> ProcessingResult:
        try:
            chunks = []
            all_text = []
            
            # Process document with Docling
            result = self.docling_converter.convert(file_path)
            
            # Extract text from Docling result
            if result and hasattr(result, 'pages'):
                for page_num, page in enumerate(result.pages):
                    # Extract text blocks
                    if hasattr(page, 'texts') and page.texts:
                        for text_block in page.texts:
                            if hasattr(text_block, 'text') and text_block.text.strip():
                                chunk = ExtractedChunk(
                                    chunk_id=f"{document_id}_docling_{page_num}_{len(chunks)}",
                                    chunk_type=ChunkType.TEXT,
                                    text=text_block.text.strip(),
                                    page=page_num + 1,
                                    confidence=0.9,  # Docling typically has high confidence
                                    bbox=BoundingBox(
                                        x1=getattr(text_block, 'x', 0),
                                        y1=getattr(text_block, 'y', 0),
                                        x2=getattr(text_block, 'x', 0) + getattr(text_block, 'width', 100),
                                        y2=getattr(text_block, 'y', 0) + getattr(text_block, 'height', 20)
                                    )
                                )
                                chunks.append(chunk)
                                all_text.append(text_block.text.strip())
                    
                    # Extract tables
                    if hasattr(page, 'tables') and page.tables:
                        for table_idx, table in enumerate(page.tables):
                            table_text = self._extract_table_text(table)
                            if table_text.strip():
                                chunk = ExtractedChunk(
                                    chunk_id=f"{document_id}_docling_table_{page_num}_{table_idx}",
                                    chunk_type=ChunkType.TABLE,
                                    text=table_text,
                                    page=page_num + 1,
                                    confidence=0.85,
                                    bbox=BoundingBox(
                                        x1=getattr(table, 'x', 0),
                                        y1=getattr(table, 'y', 0),
                                        x2=getattr(table, 'x', 0) + getattr(table, 'width', 200),
                                        y2=getattr(table, 'y', 0) + getattr(table, 'height', 100)
                                    )
                                )
                                chunks.append(chunk)
                                all_text.append(table_text)
            
            processing_time = time.time() - start_time
            
            return ProcessingResult(
                document_id=document_id,
                ocr_engine=OCREngine.DOCLING.value,
                processing_time=processing_time,
                chunks=chunks,
                success=True,
                markdown=" ".join(all_text),
                raw_text=" ".join(all_text),
                document_type=document_type,
                page_count=len(result.pages) if result and hasattr(result, 'pages') else 1,
                file_size=file_size
            )
        except Exception as e:
            logger.error(f"Error processing with Docling: {e}")
            return ProcessingResult(
                document_id=document_id,
                ocr_engine=OCREngine.DOCLING.value,
                processing_time=time.time() - start_time,
                chunks=[],
                success=False,
                error=f"Docling processing error: {str(e)}",
                document_type=document_type,
                file_size=file_size,
                page_count=1
            )
    
    def _extract_table_text(self, table) -> str:
        """Extract text from table object"""
        try:
            if hasattr(table, 'rows'):
                table_text = []
                for row in table.rows:
                    if hasattr(row, 'cells'):
                        row_text = []
                        for cell in row.cells:
                            if hasattr(cell, 'text'):
                                row_text.append(cell.text.strip())
                        table_text.append(" | ".join(row_text))
                return "\n".join(table_text)
            elif hasattr(table, 'text'):
                return table.text
            else:
                return str(table)
        except Exception:
            return str(table)


# Global OCR service instance
ocr_service = OCRService()
