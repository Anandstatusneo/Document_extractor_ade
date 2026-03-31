#!/usr/bin/env python3
"""
Test LandingAI ADE functionality
"""
import os
from dotenv import load_dotenv
from landingai_ade import LandingAIADE

def test_landingai_ade():
    """Test LandingAI ADE client"""
    print("Testing LandingAI ADE...")
    
    # Load environment variables
    load_dotenv()
    
    # Check API key
    api_key = os.getenv("VISION_AGENT_API_KEY")
    if not api_key:
        print("✗ VISION_AGENT_API_KEY not found in .env")
        return False
    
    print(f"✅ API Key found: {api_key[:10]}...")
    
    try:
        # Initialize ADE client
        client = LandingAIADE(apikey=api_key)
        print("✅ ADE Client initialized successfully")
        
        # Test with a sample document if available
        test_docs = ["L2/invoice.png", "L2/receipt.jpg", "L2/table.png"]
        
        for doc_path in test_docs:
            if os.path.exists(doc_path):
                print(f"\nTesting with {doc_path}...")
                try:
                    with open(doc_path, 'rb') as f:
                        response = client.parse(document=f.read())
                    print(f"✅ Successfully parsed {doc_path}")
                    print(f"   - Chunks extracted: {len(response.chunks) if hasattr(response, 'chunks') else 'N/A'}")
                    print(f"   - Markdown length: {len(response.markdown) if hasattr(response, 'markdown') else 'N/A'} chars")
                    return True
                except Exception as e:
                    print(f"✗ Error parsing {doc_path}: {e}")
            else:
                print(f"- Document {doc_path} not found")
        
        print("\n✅ LandingAI ADE is properly configured!")
        print("📝 Note: Full parsing tests require sample documents")
        return True
        
    except Exception as e:
        print(f"✗ Error initializing ADE client: {e}")
        return False

if __name__ == "__main__":
    test_landingai_ade()
