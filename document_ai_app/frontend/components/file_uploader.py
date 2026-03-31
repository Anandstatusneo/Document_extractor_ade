"""
File uploader component for Streamlit
"""
import streamlit as st
from typing import Tuple, Optional
import io
from PIL import Image

from shared.models.document import OCREngine


def render_file_uploader() -> Tuple[Optional[object], Optional[OCREngine], Optional[bool]]:
    """
    Render file uploader component
    
    Returns:
        Tuple of (uploaded_file, selected_ocr_engine, enable_ai_analysis)
    """
    st.markdown('<div class="upload-section">', unsafe_allow_html=True)
    
    # Initialize variables
    enable_ai_analysis = True  # Default to True
    uploaded_file = None
    ocr_engine = None
    
    # File uploader
    uploaded_file = st.file_uploader(
        "📁 Choose a document file",
        type=["pdf", "png", "jpg", "jpeg", "tiff", "bmp"],
        help="Supported formats: PDF, PNG, JPG, JPEG, TIFF, BMP (Max 50MB)",
        key="document_uploader"
    )
    
    if uploaded_file:
        # Show file preview
        col1, col2 = st.columns([1, 2])
        
        with col1:
            st.markdown("**File Preview:**")
            
            # Display preview based on file type
            if uploaded_file.type.startswith("image/"):
                try:
                    image = Image.open(uploaded_file)
                    st.image(image, caption=uploaded_file.name, width='stretch')
                except Exception as e:
                    st.error(f"Error displaying image: {e}")
            elif uploaded_file.type == "application/pdf":
                st.info("📄 PDF Document")
                st.write(f"Pages: Unknown (processing required)")
            else:
                st.info("📄 Document File")
        
        with col2:
            st.markdown("**File Information:**")
            
            # File details
            st.write(f"**Name:** {uploaded_file.name}")
            st.write(f"**Type:** {uploaded_file.type}")
            st.write(f"**Size:** {uploaded_file.size / 1024:.1f} KB")
            
            # File validation
            if uploaded_file.size > 50 * 1024 * 1024:  # 50MB
                st.error("⚠️ File size exceeds 50MB limit")
                return None, None, None
            
            # OCR Engine Selection
            st.markdown("**🔍 OCR Engine Selection:**")
        
            engine_descriptions = {
                "tesseract": "Fast and reliable for basic text extraction",
                "paddleocr": "Advanced OCR with multilingual support",
                "landingai": "AI-powered document analysis with table extraction",
                "docling": "State-of-the-art document parsing with layout analysis"
            }
        
            engine_recommendations = {
                "tesseract": {
                    "Best for": "Simple text documents",
                    "Speed": "Fast",
                    "Accuracy": "Good"
                },
                "paddleocr": {
                    "Best for": "Multilingual documents",
                    "Speed": "Medium",
                    "Accuracy": "High"
                },
                "landingai": {
                    "Best for": "Complex documents with tables",
                    "Speed": "Medium",
                    "Accuracy": "Very High"
                },
                "docling": {
                    "Best for": "Professional documents with complex layouts",
                    "Speed": "Medium",
                    "Accuracy": "Excellent"
                }
            }
        
            col1, col2 = st.columns([2, 1])
        
            with col1:
                ocr_engine = st.selectbox(
                    "Select OCR Engine:",
                    options=["tesseract", "paddleocr", "landingai", "docling"],
                    format_func=lambda x: f"{x.title()} - {engine_descriptions.get(x, '')}",
                    index=0,
                    help="Choose the OCR engine based on your document type and requirements",
                    key="ocr_engine_selector"
                )
        
            with col2:
                if st.button("ℹ️ Engine Info", key="engine_info"):
                    with st.expander("📋 Engine Recommendations", expanded=True):
                        for engine, info in engine_recommendations.items():
                            st.markdown(f"**{engine.title()}**")
                            for key, value in info.items():
                                st.write(f"• **{key}:** {value}")
                            st.markdown("---")
        
            # Show selected engine details
            recommendation = engine_recommendations.get(ocr_engine, {})
            if recommendation:
                st.markdown("**Engine Details:**")
                for key, value in recommendation.items():
                    st.write(f"• **{key}:** {value}")
            
            # AI Analysis Options
            st.markdown("**🤖 AI Analysis Options:**")
            
            # Show AI status prominently
            if uploaded_file:
                if enable_ai_analysis:
                    st.success("🧠 **AI Analysis ENABLED** - You'll get intelligent insights, summaries, and recommendations!")
                else:
                    st.warning("⚠️ **AI Analysis DISABLED** - Only basic OCR will be performed")
            
            col1, col2 = st.columns(2)
            
            with col1:
                enable_ai_analysis = st.checkbox(
                    "🤖 Enable AI Analysis",
                    value=True,
                    help="Enable intelligent document analysis with AI insights, summaries, and recommendations",
                    key="enable_ai_analysis"
                )
            
            with col2:
                if enable_ai_analysis:
                    st.success("✅ AI Active")
                else:
                    st.error("❌ AI Off")
            
            # Advanced Options (when AI is enabled)
            if enable_ai_analysis:
                with st.expander("🔧 Advanced AI Options"):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        analysis_depth = st.selectbox(
                            "Analysis Depth:",
                            options=["standard", "detailed"],
                            index=0,
                            help="Standard: Quick analysis, Detailed: Comprehensive analysis",
                            key="analysis_depth"
                        )
                    
                    with col2:
                        extract_entities = st.checkbox(
                            "Extract Entities",
                            value=True,
                            help="Extract names, dates, amounts, and other entities",
                            key="extract_entities"
                        )
    
    else:
        # Show upload instructions
        st.markdown("""
        **Instructions:**
        1. Click 'Choose a document file' or drag & drop
        2. Select your preferred OCR engine
        3. Click 'Process Document' to extract text
        
        **Supported Formats:**
        - PDF documents
        - PNG, JPG, JPEG images
        - TIFF, BMP formats
        
        **Tips:**
        - Use high-quality scans for better results
        - LandingAI ADE works best for complex documents
        - Tesseract is fastest for simple text documents
        """)
        
        ocr_engine = None
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    return uploaded_file, ocr_engine, enable_ai_analysis


def render_file_validation(file_size: int, file_type: str) -> bool:
    """
    Render file validation results
    
    Args:
        file_size: File size in bytes
        file_type: MIME type
        
    Returns:
        True if file is valid
    """
    is_valid = True
    warnings = []
    
    # Size validation
    if file_size > 50 * 1024 * 1024:  # 50MB
        is_valid = False
        warnings.append("❌ File size exceeds 50MB limit")
    elif file_size > 10 * 1024 * 1024:  # 10MB
        warnings.append("⚠️ Large file may take longer to process")
    
    # Type validation
    valid_types = [
        "application/pdf",
        "image/png",
        "image/jpeg",
        "image/jpg",
        "image/tiff",
        "image/bmp"
    ]
    
    if file_type not in valid_types:
        is_valid = False
        warnings.append("❌ Unsupported file type")
    
    # Display validation results
    if warnings:
        for warning in warnings:
            st.write(warning)
    
    if is_valid:
        st.success("✅ File validation passed")
    
    return is_valid


def render_processing_options() -> dict:
    """
    Render processing options
    
    Returns:
        Dictionary of processing options
    """
    st.markdown("**Processing Options:**")
    
    options = {}
    
    # Extraction options
    col1, col2, col3 = st.columns(3)
    
    with col1:
        options["extract_tables"] = st.checkbox(
            "📊 Extract Tables",
            value=True,
            help="Extract table data with structure"
        )
    
    with col2:
        options["extract_figures"] = st.checkbox(
            "🖼️ Extract Figures",
            value=True,
            help="Detect and extract figures/images"
        )
    
    with col3:
        options["extract_forms"] = st.checkbox(
            "📋 Extract Forms",
            value=True,
            help="Extract form fields and key-value pairs"
        )
    
    # Advanced options
    with st.expander("⚙️ Advanced Options"):
        options["preprocess_image"] = st.checkbox(
            "🔧 Preprocess Image",
            value=True,
            help="Apply image enhancement for better OCR"
        )
        
        options["include_confidence"] = st.checkbox(
            "📈 Include Confidence Scores",
            value=False,
            help="Include confidence scores for extracted text"
        )
        
        options["language"] = st.selectbox(
            "🌍 Document Language:",
            options=["English", "Auto-detect"],
            index=0,
            help="Specify document language for better accuracy"
        )
    
    return options
