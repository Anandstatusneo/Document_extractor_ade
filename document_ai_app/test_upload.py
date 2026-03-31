#!/usr/bin/env python3
"""
Test document upload and processing
"""
import requests
import json

def test_document_upload():
    """Test uploading and processing a document"""
    
    # API endpoint
    url = "http://localhost:8000/api/v1/upload"
    
    # File to upload
    file_path = "invoice.png"
    
    try:
        with open(file_path, 'rb') as f:
            files = {'file': (file_path, f, 'image/png')}
            data = {'ocr_engine': 'tesseract'}
            
            print("🚀 Testing document upload...")
            response = requests.post(url, files=files, data=data)
            
            if response.status_code == 200:
                result = response.json()
                print("✅ Upload successful!")
                print(f"Processing time: {result.get('data', {}).get('processing_time', 'N/A')}s")
                print(f"OCR Engine: {result.get('data', {}).get('ocr_engine', 'N/A')}")
                print(f"Success: {result.get('success', False)}")
                print(f"Chunks extracted: {len(result.get('data', {}).get('chunks', []))}")
                
                # Show sample extracted text
                markdown = result.get('data', {}).get('markdown', '')
                if markdown:
                    print(f"\n📄 Extracted Text Preview:")
                    print(markdown[:300] + "..." if len(markdown) > 300 else markdown)
                
                return True
            else:
                print(f"❌ Upload failed with status {response.status_code}")
                print(f"Error: {response.text}")
                return False
                
    except Exception as e:
        print(f"❌ Error during upload: {e}")
        return False

def test_health_check():
    """Test API health check"""
    try:
        response = requests.get("http://localhost:8000/health")
        if response.status_code == 200:
            result = response.json()
            print("✅ Backend is healthy!")
            print(f"Version: {result.get('version')}")
            print(f"Services: {result.get('services')}")
            return True
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Health check error: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Testing Document AI Application")
    print("=" * 50)
    
    # Test health check
    print("\n1. Testing API Health...")
    health_ok = test_health_check()
    
    if health_ok:
        # Test document upload
        print("\n2. Testing Document Upload...")
        upload_ok = test_document_upload()
        
        if upload_ok:
            print("\n🎉 All tests passed!")
            print("\n📱 You can now access the application at: http://localhost:8501")
        else:
            print("\n❌ Upload test failed")
    else:
        print("\n❌ Backend is not responding")
