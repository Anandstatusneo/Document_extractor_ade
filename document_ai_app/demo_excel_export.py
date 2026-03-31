#!/usr/bin/env python3
"""
Demo script to showcase Excel export functionality
"""
import requests
import pandas as pd
from frontend.utils.export_utils import create_structured_excel, create_excel_export, create_csv_export
import time

def test_excel_export_with_different_documents():
    """Test Excel export with different document types"""
    
    base_url = "http://localhost:8000/api/v1/upload"
    
    # Test documents
    test_files = [
        ("invoice.png", "Invoice Document"),
        ("table.png", "Table Document"),
    ]
    
    print("🚀 Excel Export Demo")
    print("=" * 50)
    
    for filename, doc_type in test_files:
        print(f"\n📄 Testing {doc_type}: {filename}")
        print("-" * 30)
        
        try:
            with open(filename, 'rb') as f:
                files = {'file': (filename, f, 'image/png')}
                data = {'ocr_engine': 'landingai'}
                
                # Process document
                response = requests.post(base_url, files=files, data=data)
                
                if response.status_code == 200:
                    result = response.json()
                    data = result.get('data', {})
                    
                    print(f"✅ Processing successful!")
                    print(f"🔧 OCR Engine: {data.get('ocr_engine')}")
                    print(f"⏱️ Processing Time: {data.get('processing_time', 0):.2f}s")
                    print(f"📊 Chunks Extracted: {len(data.get('chunks', []))}")
                    
                    # Analyze chunk types
                    chunks = data.get('chunks', [])
                    chunk_types = {}
                    for chunk in chunks:
                        chunk_type = chunk.get('chunk_type', 'unknown')
                        chunk_types[chunk_type] = chunk_types.get(chunk_type, 0) + 1
                    
                    print(f"🧩 Chunk Types: {dict(chunk_types)}")
                    
                    # Create different Excel exports
                    print(f"\n📈 Creating Excel exports...")
                    
                    # Structured Excel
                    structured_excel = create_structured_excel(data)
                    print(f"  ✅ Structured Excel: {len(structured_excel.getvalue())} bytes")
                    
                    # Complete Excel
                    complete_excel = create_excel_export(data)
                    print(f"  ✅ Complete Excel: {len(complete_excel.getvalue())} bytes")
                    
                    # CSV Export
                    csv_data = create_csv_export(data)
                    print(f"  ✅ CSV Export: {len(csv_data)} characters")
                    
                    # Show sample data
                    if chunks:
                        print(f"\n📝 Sample Extracted Text:")
                        sample_text = chunks[0].get('text', '')[:200]
                        print(f"  {sample_text}...")
                    
                    # Save demo files
                    with open(f"demo_{filename.replace('.', '_')}_structured.xlsx", "wb") as f:
                        f.write(structured_excel.getvalue())
                    
                    with open(f"demo_{filename.replace('.', '_')}_complete.xlsx", "wb") as f:
                        f.write(complete_excel.getvalue())
                    
                    print(f"\n💾 Demo files saved:")
                    print(f"  • demo_{filename.replace('.', '_')}_structured.xlsx")
                    print(f"  • demo_{filename.replace('.', '_')}_complete.xlsx")
                    
                else:
                    print(f"❌ Processing failed: {response.status_code}")
                    print(f"Error: {response.text}")
        
        except FileNotFoundError:
            print(f"⚠️ File {filename} not found, skipping...")
        except Exception as e:
            print(f"❌ Error processing {filename}: {e}")
    
    print(f"\n🎉 Excel Export Demo Complete!")
    print(f"\n📋 Features Demonstrated:")
    print(f"  • 📊 Structured Excel export with field-value pairs")
    print(f"  • 📚 Complete Excel export with multiple sheets")
    print(f"  • 📈 CSV export for data analysis")
    print(f"  • 🧩 Chunk type analysis and categorization")
    print(f"  • 📝 Text extraction and formatting")
    
    print(f"\n🌐 Try it in the UI:")
    print(f"  1. Open http://localhost:8501")
    print(f"  2. Upload a document")
    print(f"  3. View the Excel export preview")
    print(f"  4. Download in multiple formats")

if __name__ == "__main__":
    test_excel_export_with_different_documents()
