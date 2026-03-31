#!/usr/bin/env python3
"""
Test LandingAI ADE specifically
"""
import requests
import json

def test_landingai_processing():
    """Test LandingAI ADE document processing"""
    
    # API endpoint
    url = "http://localhost:8000/api/v1/upload"
    
    # File to upload
    file_path = "invoice.png"
    
    try:
        with open(file_path, 'rb') as f:
            files = {'file': (file_path, f, 'image/png')}
            data = {'ocr_engine': 'landingai'}
            
            print("🚀 Testing LandingAI ADE document processing...")
            response = requests.post(url, files=files, data=data)
            
            if response.status_code == 200:
                result = response.json()
                print("✅ LandingAI ADE processing successful!")
                print(f"Processing time: {result.get('data', {}).get('processing_time', 'N/A')}s")
                print(f"OCR Engine: {result.get('data', {}).get('ocr_engine', 'N/A')}")
                print(f"Success: {result.get('success', False)}")
                print(f"Chunks extracted: {len(result.get('data', {}).get('chunks', []))}")
                
                # Show sample extracted text
                markdown = result.get('data', {}).get('markdown', '')
                if markdown:
                    print(f"\n📄 LandingAI ADE Extracted Text Preview:")
                    print(markdown[:400] + "..." if len(markdown) > 400 else markdown)
                
                # Show chunk types
                chunks = result.get('data', {}).get('chunks', [])
                if chunks:
                    chunk_types = {}
                    for chunk in chunks:
                        chunk_type = chunk.get('chunk_type', 'unknown')
                        chunk_types[chunk_type] = chunk_types.get(chunk_type, 0) + 1
                    
                    print(f"\n🧩 Chunk Types Found:")
                    for chunk_type, count in chunk_types.items():
                        print(f"  - {chunk_type}: {count}")
                
                return True
            else:
                print(f"❌ LandingAI ADE processing failed with status {response.status_code}")
                print(f"Error: {response.text}")
                return False
                
    except Exception as e:
        print(f"❌ Error during LandingAI ADE processing: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Testing LandingAI ADE Integration")
    print("=" * 50)
    
    success = test_landingai_processing()
    
    if success:
        print("\n🎉 LandingAI ADE is working perfectly!")
        print("\n🌐 You can now use all three OCR engines:")
        print("  • Tesseract: Fast, traditional OCR")
        print("  • PaddleOCR: Deep learning-based OCR")
        print("  • LandingAI ADE: AI-powered agentic extraction ✨")
    else:
        print("\n❌ LandingAI ADE test failed")
