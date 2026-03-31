"""
Streamlit frontend for Document AI application
"""
import streamlit as st
import requests
import time
from pathlib import Path
import sys
import os

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from frontend.components.file_uploader import render_file_uploader
from frontend.components.result_viewer import render_result_viewer
from frontend.components.sidebar import render_sidebar
from frontend.utils.api_client import APIClient
from shared.models.document import OCREngine

# Page configuration
st.set_page_config(
    page_title="Document AI",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        text-align: center;
        padding: 2rem 0;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        margin: -2rem -2rem 2rem -2rem;
        border-radius: 0 0 1rem 1rem;
    }
    .upload-section {
        background: #f8f9fa;
        padding: 2rem;
        border-radius: 1rem;
        margin: 1rem 0;
    }
    .result-section {
        background: white;
        padding: 2rem;
        border-radius: 1rem;
        border: 1px solid #e9ecef;
        margin: 1rem 0;
    }
    .success-message {
        background: #d4edda;
        color: #155724;
        padding: 1rem;
        border-radius: 0.5rem;
        border: 1px solid #c3e6cb;
    }
    .error-message {
        background: #f8d7da;
        color: #721c24;
        padding: 1rem;
        border-radius: 0.5rem;
        border: 1px solid #f5c6cb;
    }
    .processing-indicator {
        text-align: center;
        padding: 2rem;
    }
</style>
""", unsafe_allow_html=True)


def render_header():
    """Render application header"""
    st.markdown("""
    <div class="main-header">
        <h1>🚀 Document AI</h1>
        <p>Advanced Document Processing with Multiple OCR Engines</p>
    </div>
    """, unsafe_allow_html=True)


def render_home_page():
    """Render home page"""
    st.markdown("## Welcome to Document AI")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        ### 📄 Upload Documents
        - Support for PDF, PNG, JPG, TIFF
        - Drag & drop interface
        - File validation and preview
        """)
    
    with col2:
        st.markdown("""
        ### 🔍 Multiple OCR Engines
        - Tesseract (Traditional)
        - PaddleOCR (Deep Learning)
        - LandingAI ADE (AI-powered)
        """)
    
    with col3:
        st.markdown("""
        ### 📊 Rich Results
        - Structured text extraction
        - Bounding box visualization
        - Table and form extraction
        """)


def render_upload_page(api_client: APIClient):
    """Render document upload page"""
    st.markdown("## 📤 Upload Document")
    
    # Render file uploader
    uploaded_file, ocr_engine, enable_ai_analysis = render_file_uploader()
    
    # Show AI status prominently when file is uploaded
    if uploaded_file and ocr_engine:
        st.markdown("---")
        
        # AI Status Banner
        if enable_ai_analysis:
            st.markdown("""
            <div style="padding: 1rem; background-color: #d4edda; border-radius: 0.5rem; border-left: 5px solid #28a745; margin-bottom: 1rem;">
                <h4 style="color: #155724; margin: 0;">🧠 AI Analysis ENABLED</h4>
                <p style="color: #155724; margin: 0;">Your document will be processed with intelligent AI analysis for insights, summaries, and recommendations.</p>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div style="padding: 1rem; background-color: #fff3cd; border-radius: 0.5rem; border-left: 5px solid #ffc107; margin-bottom: 1rem;">
                <h4 style="color: #856404; margin: 0;">⚠️ AI Analysis DISABLED</h4>
                <p style="color: #856404; margin: 0;">Only basic OCR will be performed. Enable AI analysis for intelligent insights.</p>
            </div>
            """, unsafe_allow_html=True)
        
        # Show file info
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("File Name", uploaded_file.name)
        
        with col2:
            st.metric("File Size", f"{uploaded_file.size / 1024:.1f} KB")
        
        with col3:
            st.metric("OCR Engine", ocr_engine.title())
        
        # Process button
        if st.button("🚀 Process Document", type="primary", width='stretch'):
            with st.spinner("🤖 Processing document with AI analysis..."):
                try:
                    # Upload and process
                    result = api_client.upload_document(
                        file=uploaded_file,
                        ocr_engine=ocr_engine,
                        enable_ai_analysis=enable_ai_analysis
                    )
                    
                    if result["success"]:
                        st.session_state.processing_result = result["data"]
                        st.session_state.current_page = "results"
                        st.rerun()
                    else:
                        st.error(f"Processing failed: {result.get('error', 'Unknown error')}")
                
                except Exception as e:
                    st.error(f"Error processing document: {e}")


def render_results_page(api_client: APIClient):
    """Render results page"""
    if "processing_result" not in st.session_state:
        st.warning("No processing results available. Please upload a document first.")
        if st.button("📤 Go to Upload Page"):
            st.session_state.current_page = "upload"
            st.rerun()
        return
    
    result = st.session_state.processing_result
    
    st.markdown("## 📊 Processing Results")
    
    # Success message
    if result.get("success"):
        st.markdown("""
        <div class="success-message">
            ✅ Document processed successfully!
        </div>
        """, unsafe_allow_html=True)
    
    # Processing metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("OCR Engine", result["ocr_engine"].title())
    
    with col2:
        st.metric("Processing Time", f"{result['processing_time']:.2f}s")
    
    with col3:
        st.metric("Document Type", result["document_type"].title())
    
    with col4:
        chunks = result.get("chunks", [])
        if chunks is None:
            chunks = []
        chunks_count = len(chunks)
        st.metric("Chunks Extracted", chunks_count)
    
    # Render result viewer
    render_result_viewer(result)
    
    # Action buttons
    st.markdown("---")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🔄 Process with Different Engine"):
            st.session_state.current_page = "upload"
            st.rerun()
    
    with col2:
        if st.button("📥 Download Results"):
            # Implement download functionality
            st.info("Download functionality coming soon!")
    
    with col3:
        if st.button("🏠 Back to Home"):
            st.session_state.current_page = "home"
            st.rerun()


def render_history_page(api_client: APIClient):
    """Render processing history page"""
    st.markdown("## 📚 Processing History")
    
    st.info("History functionality will be available in a future version!")
    
    # Placeholder for history
    st.markdown("""
    ### Features Coming Soon:
    - Processing history timeline
    - Document search and filtering
    - Result comparison
    - Export functionality
    """)


def main():
    """Main application"""
    # Initialize session state
    if "current_page" not in st.session_state:
        st.session_state.current_page = "home"
    
    # Render header
    render_header()
    
    # Render sidebar
    api_client = render_sidebar()
    
    # Page routing
    if st.session_state.current_page == "home":
        render_home_page()
    elif st.session_state.current_page == "upload":
        render_upload_page(api_client)
    elif st.session_state.current_page == "results":
        render_results_page(api_client)
    elif st.session_state.current_page == "history":
        render_history_page(api_client)
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style='text-align: center; color: #666; padding: 1rem;'>
        Document AI Application | Powered by Multiple OCR Engines
    </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
