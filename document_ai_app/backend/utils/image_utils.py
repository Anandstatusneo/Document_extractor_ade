"""
Image processing utilities
"""
import os
from typing import List, Optional
from pathlib import Path
import io

try:
    from PIL import Image, ImageEnhance, ImageFilter
    import fitz  # PyMuPDF
    PIL_AVAILABLE = True
    PYMUPDF_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Some image processing libraries not available: {e}")
    PIL_AVAILABLE = False
    PYMUPDF_AVAILABLE = False


def preprocess_image(
    image_path: str, 
    enhance_contrast: bool = True,
    enhance_sharpness: bool = True,
    denoise: bool = True
) -> Optional[Image.Image]:
    """
    Preprocess image for better OCR results
    
    Args:
        image_path: Path to image file
        enhance_contrast: Whether to enhance contrast
        enhance_sharpness: Whether to enhance sharpness
        denoise: Whether to apply denoising
        
    Returns:
        Preprocessed PIL Image or None if failed
    """
    if not PIL_AVAILABLE:
        print("PIL not available for image preprocessing")
        return None
    
    try:
        image = Image.open(image_path)
        
        # Convert to RGB if necessary
        if image.mode != 'RGB':
            image = image.convert('RGB')
        
        # Enhance contrast
        if enhance_contrast:
            enhancer = ImageEnhance.Contrast(image)
            image = enhancer.enhance(2.0)
        
        # Enhance sharpness
        if enhance_sharpness:
            enhancer = ImageEnhance.Sharpness(image)
            image = enhancer.enhance(2.0)
        
        # Apply denoising
        if denoise:
            image = image.filter(ImageFilter.MedianFilter(size=3))
        
        return image
        
    except Exception as e:
        print(f"Error preprocessing image {image_path}: {e}")
        return None


def convert_pdf_to_images(pdf_path: str, dpi: int = 200) -> List[Image.Image]:
    """
    Convert PDF to list of images
    
    Args:
        pdf_path: Path to PDF file
        dpi: Resolution for conversion
        
    Returns:
        List of PIL Images
    """
    if not PYMUPDF_AVAILABLE:
        print("PyMuPDF not available for PDF conversion")
        return []
    
    if not PIL_AVAILABLE:
        print("PIL not available for image processing")
        return []
    
    try:
        pdf_document = fitz.open(pdf_path)
        images = []
        
        for page_num in range(len(pdf_document)):
            page = pdf_document.load_page(page_num)
            
            # Convert page to image
            pix = page.get_pixmap(matrix=fitz.Matrix(dpi/72, dpi/72))
            img_data = pix.tobytes("png")
            
            # Convert to PIL Image
            image = Image.open(io.BytesIO(img_data))
            image = image.convert('RGB')
            images.append(image)
        
        pdf_document.close()
        return images
        
    except Exception as e:
        print(f"Error converting PDF {pdf_path} to images: {e}")
        return []


def resize_image(
    image: Image.Image, 
    max_width: int = 2000, 
    max_height: int = 2000
) -> Image.Image:
    """
    Resize image while maintaining aspect ratio
    
    Args:
        image: PIL Image
        max_width: Maximum width
        max_height: Maximum height
        
    Returns:
        Resized PIL Image
    """
    if not PIL_AVAILABLE:
        return image
    
    width, height = image.size
    
    # Calculate new dimensions
    if width > max_width or height > max_height:
        ratio = min(max_width / width, max_height / height)
        new_width = int(width * ratio)
        new_height = int(height * ratio)
        
        return image.resize((new_width, new_height), Image.Resampling.LANCZOS)
    
    return image


def save_image(image: Image.Image, output_path: str, quality: int = 95) -> bool:
    """
    Save PIL Image to file
    
    Args:
        image: PIL Image to save
        output_path: Output file path
        quality: JPEG quality (1-100)
        
    Returns:
        True if successful, False otherwise
    """
    if not PIL_AVAILABLE:
        return False
    
    try:
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Save based on file extension
        if output_path.lower().endswith('.jpg') or output_path.lower().endswith('.jpeg'):
            image.save(output_path, 'JPEG', quality=quality)
        elif output_path.lower().endswith('.png'):
            image.save(output_path, 'PNG')
        else:
            # Default to PNG
            image.save(output_path, 'PNG')
        
        return True
        
    except Exception as e:
        print(f"Error saving image to {output_path}: {e}")
        return False


def get_image_info(image_path: str) -> Optional[dict]:
    """
    Get image information
    
    Args:
        image_path: Path to image file
        
    Returns:
        Dictionary with image info or None if failed
    """
    if not PIL_AVAILABLE:
        return None
    
    try:
        with Image.open(image_path) as image:
            return {
                'width': image.width,
                'height': image.height,
                'mode': image.mode,
                'format': image.format,
                'size_bytes': os.path.getsize(image_path)
            }
    except Exception as e:
        print(f"Error getting image info for {image_path}: {e}")
        return None


def create_thumbnail(image: Image.Image, size: tuple = (150, 150)) -> Optional[Image.Image]:
    """
    Create thumbnail from image
    
    Args:
        image: PIL Image
        size: Thumbnail size (width, height)
        
    Returns:
        Thumbnail PIL Image or None if failed
    """
    if not PIL_AVAILABLE:
        return None
    
    try:
        # Create a copy to avoid modifying original
        thumbnail = image.copy()
        thumbnail.thumbnail(size, Image.Resampling.LANCZOS)
        return thumbnail
    except Exception as e:
        print(f"Error creating thumbnail: {e}")
        return None
