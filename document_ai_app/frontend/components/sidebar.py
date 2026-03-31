"""
Sidebar component for Streamlit
"""
import streamlit as st
import requests
from typing import Dict, Any

from frontend.utils.api_client import APIClient


def render_sidebar() -> APIClient:
    """
    Render application sidebar
    
    Returns:
        Configured API client
    """
    with st.sidebar:
        st.markdown("## 🚀 Document AI")
        
        # Navigation
        st.markdown("### 📍 Navigation")
        
        page_options = {
            "home": "🏠 Home",
            "upload": "📤 Upload Document",
            "results": "📊 Results",
            "history": "📚 History"
        }
        
        selected_page = st.selectbox(
            "Choose Page:",
            options=list(page_options.keys()),
            format_func=lambda x: page_options[x],
            index=list(page_options.keys()).index(st.session_state.get("current_page", "home")),
            key="page_selector"
        )
        
        if selected_page != st.session_state.get("current_page"):
            st.session_state.current_page = selected_page
            st.rerun()
        
        st.markdown("---")
        
        # API Configuration
        st.markdown("### ⚙️ API Configuration")
        
        api_url = st.text_input(
            "Backend URL:",
            value="http://localhost:8000",
            help="URL of the backend API"
        )
        
        # Test connection
        if st.button("🔗 Test Connection", key="test_connection"):
            with st.spinner("Testing connection..."):
                try:
                    response = requests.get(f"{api_url}/health", timeout=5)
                    if response.status_code == 200:
                        st.success("✅ Connection successful!")
                    else:
                        st.error(f"❌ Connection failed: {response.status_code}")
                except requests.exceptions.RequestException as e:
                    st.error(f"❌ Connection failed: {e}")
        
        st.markdown("---")
        
        # OCR Engine Status
        st.markdown("### 🔍 OCR Engine Status")
        
        try:
            api_client = APIClient(api_url)
            # Show available engines
            try:
                engines_response = api_client.get_available_engines()
                
                if engines_response.get("success"):
                    engines = engines_response.get("data", {})
                    
                    for engine_id, engine_info in engines.items():
                        status = "✅" if engine_info.get("available") else "❌"
                        st.write(f"{status} {engine_info.get('name', engine_id)}")
                        
                        if not engine_info.get("available"):
                            st.caption(f"Not available: {engine_info.get('description', '')}")
                else:
                    st.error("Failed to fetch engine status")
            
            except Exception as e:
                st.error(f"Error checking engines: {e}")
                st.caption("Make sure the backend is running on http://localhost:8000")
        
        except Exception as e:
            st.error(f"Error checking engines: {e}")
        
        st.markdown("---")
        
        # Quick Stats
        st.markdown("### 📈 Quick Stats")
        
        # Show current session stats
        if "processing_result" in st.session_state:
            result = st.session_state.processing_result
            st.metric("Last Processing", f"{result.get('processing_time', 0):.1f}s")
            chunks = result.get("chunks", [])
            if chunks is None:
                chunks = []
            st.metric("Chunks Extracted", len(chunks))
        else:
            st.write("No processing done yet")
        
        st.markdown("---")
        
        # Help & Info
        st.markdown("### ℹ️ Help")
        
        with st.expander("📖 How to Use"):
            st.markdown("""
            1. **Upload**: Go to Upload page and select a document
            2. **Choose Engine**: Select OCR engine based on document type
            3. **Process**: Click process to extract text
            4. **View Results**: Check Results page for extracted data
            
            **Engine Recommendations:**
            - **Tesseract**: Fast, good for simple text
            - **PaddleOCR**: Better for complex layouts
            - **LandingAI**: Best for structured extraction
            """)
        
        with st.expander("🔧 Troubleshooting"):
            st.markdown("""
            **Common Issues:**
            
            - **Large files**: May take longer to process
            - **Poor quality**: Try image preprocessing
            - **Complex layouts**: Use LandingAI ADE
            - **Connection errors**: Check backend URL
            
            **Tips:**
            - Use high-resolution scans
            - Ensure good lighting for images
            - Try different OCR engines
            """)
        
        st.markdown("---")
        
        # About
        st.markdown("### ℹ️ About")
        st.markdown("""
        **Document AI v1.0**
        
        Advanced document processing with multiple OCR engines.
        
        Features:
        - Multiple OCR engines
        - Structured extraction
        - Visual grounding
        - Batch processing
        """)
        
        # Create API client
        api_client = APIClient(api_url)
        
        return api_client


def render_settings_panel():
    """Render settings panel (placeholder)"""
    st.markdown("### ⚙️ Settings")
    
    # Theme settings
    theme = st.selectbox(
        "Theme:",
        options=["Light", "Dark", "Auto"],
        index=0
    )
    
    # Language settings
    language = st.selectbox(
        "Language:",
        options=["English", "Auto-detect"],
        index=0
    )
    
    # Processing settings
    st.markdown("**Processing Defaults:**")
    
    default_engine = st.selectbox(
        "Default OCR Engine:",
        options=["tesseract", "paddleocr", "landingai"],
        index=0
    )
    
    preprocess_images = st.checkbox(
        "Preprocess Images",
        value=True
    )
    
    include_confidence = st.checkbox(
        "Include Confidence Scores",
        value=False
    )
    
    if st.button("💾 Save Settings"):
        st.success("Settings saved (in development)")


def render_help_panel():
    """Render help panel"""
    st.markdown("### ❓ Need Help?")
    
    help_topics = {
        "getting_started": "Getting Started",
        "ocr_engines": "OCR Engines",
        "file_formats": "Supported Formats",
        "troubleshooting": "Troubleshooting"
    }
    
    selected_topic = st.selectbox(
        "Select Topic:",
        options=list(help_topics.keys()),
        format_func=lambda x: help_topics[x]
    )
    
    if selected_topic == "getting_started":
        st.markdown("""
        **Getting Started Guide:**
        
        1. **Upload Document**: Use the Upload page to select your file
        2. **Choose OCR Engine**: Select based on your document type
        3. **Configure Options**: Set extraction preferences
        4. **Process**: Click the process button
        5. **View Results**: Check the Results page
        """)
    
    elif selected_topic == "ocr_engines":
        st.markdown("""
        **OCR Engines:**
        
        **Tesseract**
        - Fast processing
        - Good for clean text
        - Limited layout understanding
        
        **PaddleOCR**
        - Deep learning based
        - Better accuracy
        - Handwriting support
        
        **LandingAI ADE**
        - AI-powered extraction
        - Structured data extraction
        - Visual grounding
        """)
    
    elif selected_topic == "file_formats":
        st.markdown("""
        **Supported Formats:**
        
        **Documents:**
        - PDF (.pdf)
        
        **Images:**
        - PNG (.png)
        - JPEG (.jpg, .jpeg)
        - TIFF (.tiff)
        - BMP (.bmp)
        
        **Limitations:**
        - Max file size: 50MB
        - Encrypted PDFs not supported
        """)
    
    elif selected_topic == "troubleshooting":
        st.markdown("""
        **Common Issues:**
        
        **Processing Fails:**
        - Check file format
        - Ensure file isn't corrupted
        - Verify API connection
        
        **Poor Results:**
        - Try different OCR engine
        - Check image quality
        - Ensure text is clear
        
        **Slow Processing:**
        - Large files take longer
        - LandingAI ADE is slower but more accurate
        - Consider file size limits
        """)
