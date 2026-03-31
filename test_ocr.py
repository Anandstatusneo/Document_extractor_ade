#!/usr/bin/env python3
"""
Test basic OCR functionality with Tesseract
"""
import pytesseract
from PIL import Image
import os

def test_tesseract():
    """Test Tesseract OCR installation"""
    print("Testing Tesseract OCR...")
    
    # Check Tesseract version
    try:
        version = pytesseract.get_tesseract_version()
        print(f"✓ Tesseract version: {version}")
    except Exception as e:
        print(f"✗ Tesseract not found: {e}")
        return False
    
    # Test with a simple image if available
    test_images = [
        "L2/invoice.png",
        "L2/receipt.jpg", 
        "L2/table.png"
    ]
    
    for img_path in test_images:
        if os.path.exists(img_path):
            try:
                print(f"\nTesting with {img_path}...")
                image = Image.open(img_path)
                text = pytesseract.image_to_string(image)
                print(f"✓ Successfully extracted text from {img_path}")
                print(f"First 200 characters: {text[:200]}...")
                return True
            except Exception as e:
                print(f"✗ Error processing {img_path}: {e}")
        else:
            print(f"- Image {img_path} not found")
    
    print("\n✓ Tesseract is properly installed and ready!")
    return True

if __name__ == "__main__":
    test_tesseract()
