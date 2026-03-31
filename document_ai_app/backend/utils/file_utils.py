"""
File processing utilities
"""
import os
import mimetypes
from pathlib import Path
from typing import Optional

from models.document import DocumentType


def get_document_type(file_path: str) -> DocumentType:
    """
    Determine document type from file extension
    
    Args:
        file_path: Path to file
        
    Returns:
        DocumentType enum value
    """
    file_extension = Path(file_path).suffix.lower()
    
    if file_extension == '.pdf':
        return DocumentType.PDF
    elif file_extension in {'.png', '.jpg', '.jpeg', '.tiff', '.bmp', '.gif'}:
        return DocumentType.IMAGE
    else:
        return DocumentType.UNKNOWN


def get_file_size(file_path: str) -> int:
    """
    Get file size in bytes
    
    Args:
        file_path: Path to file
        
    Returns:
        File size in bytes
    """
    try:
        return os.path.getsize(file_path)
    except OSError:
        return 0


def get_content_type(file_path: str) -> str:
    """
    Get MIME content type for file
    
    Args:
        file_path: Path to file
        
    Returns:
        MIME content type string
    """
    content_type, _ = mimetypes.guess_type(file_path)
    return content_type or 'application/octet-stream'


def validate_file(file_path: str, max_size: int = 50 * 1024 * 1024) -> tuple[bool, Optional[str]]:
    """
    Validate file for processing
    
    Args:
        file_path: Path to file
        max_size: Maximum allowed file size in bytes
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not os.path.exists(file_path):
        return False, "File does not exist"
    
    if not os.path.isfile(file_path):
        return False, "Path is not a file"
    
    file_size = get_file_size(file_path)
    if file_size > max_size:
        return False, f"File size {file_size} exceeds maximum allowed size {max_size}"
    
    if file_size == 0:
        return False, "File is empty"
    
    document_type = get_document_type(file_path)
    if document_type == DocumentType.UNKNOWN:
        return False, "Unsupported file type"
    
    return True, None


def create_upload_directory(upload_dir: str = "uploads") -> str:
    """
    Create upload directory if it doesn't exist
    
    Args:
        upload_dir: Directory path
        
    Returns:
        Created directory path
    """
    os.makedirs(upload_dir, exist_ok=True)
    return upload_dir


def generate_unique_filename(original_filename: str) -> str:
    """
    Generate unique filename to avoid conflicts
    
    Args:
        original_filename: Original filename
        
    Returns:
        Unique filename
    """
    import uuid
    from pathlib import Path
    
    file_extension = Path(original_filename).suffix
    unique_id = str(uuid.uuid4())[:8]
    return f"{unique_id}_{original_filename}"


def cleanup_old_files(directory: str, max_age_hours: int = 24) -> int:
    """
    Clean up old files in directory
    
    Args:
        directory: Directory to clean
        max_age_hours: Maximum age in hours
        
    Returns:
        Number of files deleted
    """
    import time
    
    if not os.path.exists(directory):
        return 0
    
    current_time = time.time()
    max_age_seconds = max_age_hours * 3600
    deleted_count = 0
    
    try:
        for filename in os.listdir(directory):
            file_path = os.path.join(directory, filename)
            if os.path.isfile(file_path):
                file_age = current_time - os.path.getmtime(file_path)
                if file_age > max_age_seconds:
                    os.remove(file_path)
                    deleted_count += 1
    except OSError as e:
        print(f"Error cleaning up directory {directory}: {e}")
    
    return deleted_count
