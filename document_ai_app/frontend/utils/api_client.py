"""
API client for communicating with backend
"""
import requests
import streamlit as st
from typing import Dict, Any, Optional
import logging
from pathlib import Path

from shared.models.document import OCREngine

logger = logging.getLogger(__name__)


class APIClient:
    """Client for communicating with Document AI backend API"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        """
        Initialize API client
        
        Args:
            base_url: Base URL of the backend API
        """
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        self.session.timeout = 30  # 30 second timeout
    
    def _handle_response(self, response: requests.Response) -> Dict[str, Any]:
        """
        Handle API response
        
        Args:
            response: Requests response object
            
        Returns:
            Parsed response data
        """
        try:
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            logger.error(f"HTTP error: {e}")
            return {
                "success": False,
                "error": f"HTTP {response.status_code}: {response.text}"
            }
        except requests.exceptions.RequestException as e:
            logger.error(f"Request error: {e}")
            return {
                "success": False,
                "error": f"Request failed: {str(e)}"
            }
        except ValueError as e:
            logger.error(f"JSON decode error: {e}")
            return {
                "success": False,
                "error": f"Invalid response format: {str(e)}"
            }
    
    def health_check(self) -> Dict[str, Any]:
        """
        Check API health
        
        Returns:
            Health check response
        """
        try:
            response = self.session.get(f"{self.base_url}/health")
            return self._handle_response(response)
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return {
                "success": False,
                "error": f"Health check failed: {str(e)}"
            }
    
    def get_available_engines(self) -> Dict[str, Any]:
        """
        Get available OCR engines
        
        Returns:
            Available engines response
        """
        try:
            response = self.session.get(f"{self.base_url}/api/v1/engines")
            return self._handle_response(response)
        except Exception as e:
            logger.error(f"Failed to get engines: {e}")
            return {
                "success": False,
                "error": f"Failed to get engines: {str(e)}"
            }
    
    def upload_document(self, file, ocr_engine: str, enable_ai_analysis: bool = True) -> Dict[str, Any]:
        """
        Upload and process document
        
        Args:
            file: Uploaded file object
            ocr_engine: OCR engine to use
            enable_ai_analysis: Whether to enable AI analysis
            
        Returns:
            API response
        """
        try:
            # Prepare files and data
            files = {'file': (file.name, file, file.type)}
            data = {
                'ocr_engine': ocr_engine,
                'enable_ai_analysis': str(enable_ai_analysis).lower()
            }
            
            # Make request
            response = self.session.post(
                f"{self.base_url}/api/v1/upload",
                files=files,
                data=data
            )
            
            return response.json()
            
        except Exception as e:
            logger.error(f"Error uploading document: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def process_document(
        self,
        document_id: str,
        ocr_engine: OCREngine = OCREngine.TESSERACT,
        extract_tables: bool = True,
        extract_figures: bool = True,
        extract_forms: bool = True
    ) -> Dict[str, Any]:
        """
        Process existing document
        
        Args:
            document_id: Document ID
            ocr_engine: OCR engine to use
            extract_tables: Whether to extract tables
            extract_figures: Whether to extract figures
            extract_forms: Whether to extract forms
            
        Returns:
            Processing result
        """
        try:
            # Handle both string and enum inputs
            ocr_engine_value = ocr_engine.value if hasattr(ocr_engine, 'value') else ocr_engine
            
            data = {
                "document_id": document_id,
                "ocr_engine": ocr_engine_value,
                "extract_tables": extract_tables,
                "extract_figures": extract_figures,
                "extract_forms": extract_forms
            }
            
            response = self.session.post(
                f"{self.base_url}/api/v1/process",
                json=data
            )
            
            return self._handle_response(response)
            
        except Exception as e:
            logger.error(f"Process document failed: {e}")
            return {
                "success": False,
                "error": f"Processing failed: {str(e)}"
            }
    
    def get_document_result(self, document_id: str) -> Dict[str, Any]:
        """
        Get document processing result
        
        Args:
            document_id: Document ID
            
        Returns:
            Document result
        """
        try:
            response = self.session.get(f"{self.base_url}/api/v1/documents/{document_id}")
            return self._handle_response(response)
        except Exception as e:
            logger.error(f"Get document result failed: {e}")
            return {
                "success": False,
                "error": f"Failed to get result: {str(e)}"
            }
    
    def download_file(self, file_path: str) -> Optional[bytes]:
        """
        Download file from backend
        
        Args:
            file_path: Path to file
            
        Returns:
            File content as bytes or None if failed
        """
        try:
            response = self.session.get(f"{self.base_url}/uploads/{file_path}")
            response.raise_for_status()
            return response.content
        except Exception as e:
            logger.error(f"Download file failed: {e}")
            return None
    
    def test_connection(self) -> bool:
        """
        Test connection to backend
        
        Returns:
            True if connection successful
        """
        try:
            response = self.session.get(f"{self.base_url}/", timeout=5)
            return response.status_code == 200
        except Exception:
            return False


def create_api_client() -> APIClient:
    """
    Create API client with configuration from session state or defaults
    
    Returns:
        Configured API client
    """
    # Get API URL from session state or use default
    api_url = st.session_state.get("api_url", "http://localhost:8000")
    
    return APIClient(api_url)


def show_api_status(api_client: APIClient):
    """
    Show API status in sidebar
    
    Args:
        api_client: API client instance
    """
    with st.sidebar:
        # Test connection
        if api_client.test_connection():
            st.success("✅ API Connected")
        else:
            st.error("❌ API Disconnected")
            st.caption("Check backend URL and ensure server is running")
        
        # Show available engines
        engines_response = api_client.get_available_engines()
        if engines_response.get("success"):
            engines = engines_response.get("data", {})
            
            st.markdown("**OCR Engines:**")
            for engine_id, engine_info in engines.items():
                status = "✅" if engine_info.get("available") else "❌"
                st.caption(f"{status} {engine_info.get('name', engine_id)}")
        else:
            st.caption("Unable to fetch engine status")


def handle_api_error(error_response: Dict[str, Any]) -> str:
    """
    Handle API error and return user-friendly message
    
    Args:
        error_response: Error response from API
        
    Returns:
        User-friendly error message
    """
    if not error_response.get("success"):
        error = error_response.get("error", "Unknown error")
        
        # Common error patterns
        if "connection" in error.lower():
            return "Cannot connect to backend. Please check if the server is running."
        elif "timeout" in error.lower():
            return "Request timed out. Please try again or use a smaller file."
        elif "file size" in error.lower():
            return "File too large. Please use a file smaller than 50MB."
        elif "format" in error.lower():
            return "Unsupported file format. Please use PDF, PNG, JPG, or TIFF."
        elif "ocr" in error.lower():
            return "OCR processing failed. Please try a different OCR engine."
        else:
            return f"Processing error: {error}"
    
    return "Unknown error occurred"


def format_processing_time(seconds: float) -> str:
    """
    Format processing time in human-readable format
    
    Args:
        seconds: Processing time in seconds
        
    Returns:
        Formatted time string
    """
    if seconds < 1:
        return f"{seconds * 1000:.0f}ms"
    elif seconds < 60:
        return f"{seconds:.1f}s"
    else:
        minutes = seconds // 60
        remaining_seconds = seconds % 60
        return f"{int(minutes)}m {remaining_seconds:.0f}s"


def get_file_size_mb(file_size_bytes: int) -> float:
    """
    Convert file size to MB
    
    Args:
        file_size_bytes: File size in bytes
        
    Returns:
        File size in MB
    """
    return file_size_bytes / (1024 * 1024)


def validate_file_for_upload(uploaded_file) -> tuple[bool, str]:
    """
    Validate uploaded file
    
    Args:
        uploaded_file: Streamlit uploaded file object
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    # Check file size
    max_size_mb = 50
    file_size_mb = get_file_size_mb(uploaded_file.size)
    
    if file_size_mb > max_size_mb:
        return False, f"File size ({file_size_mb:.1f}MB) exceeds limit ({max_size_mb}MB)"
    
    # Check file type
    allowed_types = {
        "application/pdf": "PDF",
        "image/png": "PNG",
        "image/jpeg": "JPEG",
        "image/jpg": "JPG",
        "image/tiff": "TIFF",
        "image/bmp": "BMP"
    }
    
    if uploaded_file.type not in allowed_types:
        return False, f"Unsupported file type: {uploaded_file.type}"
    
    return True, ""
