"""
Result viewer component for Streamlit
"""
import streamlit as st
import json
from typing import Dict, Any
import pandas as pd
from PIL import Image, ImageDraw, ImageFont
import io
import base64


def extract_text_content(result: Dict[str, Any]) -> str:
    """Extract text content from processing result"""
    text_parts = []
    
    # Extract from chunks
    chunks = result.get("chunks", [])
    for chunk in chunks:
        if isinstance(chunk, dict) and chunk.get("text"):
            text_parts.append(chunk["text"])
        elif hasattr(chunk, "text"):
            text_parts.append(chunk.text)
    
    # Add raw text if available
    if result.get("raw_text"):
        text_parts.append(result["raw_text"])
    
    # Add markdown if available
    if result.get("markdown"):
        text_parts.append(result["markdown"])
    
    return "\n\n".join(text_parts)

from utils.export_utils import create_excel_export, create_structured_excel, create_csv_export, create_enhanced_excel_export


def render_result_viewer(result: Dict[str, Any]):
    """
    Render processing results
    
    Args:
        result: Processing result dictionary
    """
    if not result.get("success"):
        st.error(f"Processing failed: {result.get('error', 'Unknown error')}")
        return
    
    st.markdown('<div class="result-section">', unsafe_allow_html=True)
    
    # Tabs for different views
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(["📄 Extracted Text", "🧩 Chunks", "📊 Structured Data", "📈 Table View", "🤖 AI Analysis", "🔍 JSON"])
    
    with tab1:
        render_text_view(result)
    
    with tab2:
        render_chunks_view(result)
    
    with tab3:
        render_structured_data_view(result)
    
    with tab4:
        render_table_view(result)
    
    with tab5:
        render_ai_analysis_view(result)
    
    with tab6:
        render_json_view(result)
    
    # Export preview and download buttons
    st.markdown("---")
    render_export_preview(result)
    st.markdown("---")
    create_download_buttons(result)
    
    st.markdown('</div>', unsafe_allow_html=True)


def render_text_view(result: Dict[str, Any]):
    """Render extracted text view"""
    st.markdown("### 📄 Extracted Content")
    
    # Display options
    col1, col2 = st.columns([1, 1])
    
    with col1:
        view_format = st.radio(
            "View Format:",
            options=["Markdown", "Raw Text"],
            index=0,
            key="text_view_format"
        )
    
    with col2:
        show_line_numbers = st.checkbox(
            "Show Line Numbers",
            value=True,
            key="show_line_numbers"
        )
    
    # Display content
    content = ""
    if view_format == "Markdown" and result.get("markdown"):
        content = result["markdown"]
    elif result.get("raw_text"):
        content = result["raw_text"]
    else:
        content = "No text content available"
    
    if show_line_numbers:
        lines = content.split('\n')
        numbered_lines = [f"{i+1:3d}: {line}" for i, line in enumerate(lines)]
        content = '\n'.join(numbered_lines)
    
    st.text_area(
        "Extracted Text:",
        value=content,
        height=400,
        key="extracted_text_display",
        help="Full extracted text from the document"
    )
    
    # Copy button
    if st.button("📋 Copy Text", key="copy_text"):
        st.write("Text copied to clipboard (in development)")


def render_chunks_view(result: Dict[str, Any]):
    """Render chunks view with filtering"""
    st.markdown("### 🧩 Extracted Chunks")
    
    chunks = result.get("chunks", [])
    
    if not chunks:
        st.info("No chunks available")
        return
    
    # Chunk statistics
    col1, col2, col3, col4 = st.columns(4)
    
    chunk_types = {}
    for chunk in chunks:
        chunk_type = chunk.get("chunk_type", "unknown")
        chunk_types[chunk_type] = chunk_types.get(chunk_type, 0) + 1
    
    with col1:
        st.metric("Total Chunks", len(chunks))
    
    with col2:
        st.metric("Text Chunks", chunk_types.get("text", 0))
    
    with col3:
        st.metric("Table Chunks", chunk_types.get("table", 0))
    
    with col4:
        st.metric("Figure Chunks", chunk_types.get("figure", 0))
    
    # Filtering options
    st.markdown("**Filter Chunks:**")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        selected_types = st.multiselect(
            "Chunk Types:",
            options=list(chunk_types.keys()),
            default=list(chunk_types.keys()),
            key="chunk_type_filter"
        )
    
    with col2:
        confidence_threshold = st.slider(
            "Min Confidence:",
            min_value=0.0,
            max_value=1.0,
            value=0.0,
            step=0.1,
            key="confidence_filter"
        )
    
    # Get page count safely
    page_count = result.get("page_count", 1)
    if page_count is None or not isinstance(page_count, int) or page_count < 1:
        page_count = 1
    
    with col3:
        page_filter = st.selectbox(
            "Page:",
            options=["All"] + [f"Page {i}" for i in range(1, page_count + 1)],
            index=0,
            key="page_filter"
        )
    
    # Filter chunks
    filtered_chunks = []
    for chunk in chunks:
        # Type filter
        if selected_types and chunk.get("chunk_type") not in selected_types:
            continue
        
        # Confidence filter
        confidence = chunk.get("confidence", 1.0)
        if confidence is None:
            confidence = 1.0
        if confidence < confidence_threshold:
            continue
        
        # Page filter
        if page_filter != "All":
            page_num = int(page_filter.split()[1])
            if chunk.get("page") != page_num:
                continue
        
        filtered_chunks.append(chunk)
    
    st.write(f"Showing {len(filtered_chunks)} of {len(chunks)} chunks")
    
    # Display chunks
    for i, chunk in enumerate(filtered_chunks):
        with st.expander(f"📦 {chunk.get('chunk_type', 'unknown').title()} Chunk #{i+1}"):
            col1, col2 = st.columns([3, 1])
            
            with col1:
                st.markdown("**Content:**")
                st.text_area(
                    "Text:",
                    value=chunk.get("text", ""),
                    height=100,
                    key=f"chunk_text_{i}",
                    disabled=True
                )
            
            with col2:
                st.markdown("**Metadata:**")
                st.write(f"Type: `{chunk.get('chunk_type', 'unknown')}`")
                st.write(f"Page: `{chunk.get('page', 'N/A')}`")
                
                confidence = chunk.get("confidence")
                if confidence is not None:
                    st.write(f"Confidence: `{confidence:.2f}`")
                
                bbox = chunk.get("bbox")
                if bbox:
                    st.write(f"Location: `{bbox['x0']:.2f}, {bbox['y0']:.2f}`")
                
                chunk_id = chunk.get("chunk_id")
                if chunk_id:
                    st.write(f"ID: `{chunk_id[:8]}...`")


def render_structured_data_view(result: Dict[str, Any]):
    """Render structured data in table format"""
    st.markdown("### 📊 Structured Data Extraction")
    
    chunks = result.get("chunks", [])
    
    if not chunks:
        st.info("No data available for structured view")
        return
    
    # Extract structured data
    structured_data = []
    
    for chunk in chunks:
        text = chunk.get("text", "").strip()
        if not text:
            continue
        
        # Try to extract key-value pairs
        lines = text.split('\n')
        for line in lines:
            line = line.strip()
            if ':' in line and len(line) > 5:
                parts = line.split(':', 1)
                if len(parts) == 2:
                    key = parts[0].strip()
                    value = parts[1].strip()
                    
                    structured_data.append({
                        "Field": key,
                        "Value": value,
                        "Type": chunk.get("chunk_type", "text"),
                        "Page": chunk.get("page", 1),
                        "Confidence": chunk.get("confidence", "N/A")
                    })
            elif any(keyword in line.lower() for keyword in ['$', 'amount', 'total', 'price']):
                # Likely a monetary value or important line item
                structured_data.append({
                    "Field": "Extracted Line",
                    "Value": line,
                    "Type": chunk.get("chunk_type", "text"),
                    "Page": chunk.get("page", 1),
                    "Confidence": chunk.get("confidence", "N/A")
                })
    
    if structured_data:
        st.write(f"📊 Found {len(structured_data)} structured data items")
        
        # Create DataFrame and display
        df = pd.DataFrame(structured_data)
        
        # Format the display
        st.dataframe(
            df,
            column_config={
                "Field": st.column_config.TextColumn("Field", width="medium"),
                "Value": st.column_config.TextColumn("Value", width="large"),
                "Type": st.column_config.TextColumn("Type", width="small"),
                "Page": st.column_config.NumberColumn("Page", width="small"),
                "Confidence": st.column_config.TextColumn("Confidence", width="small")
            },
            hide_index=True,
            width='stretch'
        )
        
        # Add search functionality
        st.markdown("**🔍 Search Structured Data:**")
        search_term = st.text_input("Search in fields or values:", key="structured_search_main")
        
        if search_term:
            filtered_data = [item for item in structured_data 
                           if search_term.lower() in item.get("Field", "").lower() 
                           or search_term.lower() in item.get("Value", "").lower()]
            
            if filtered_data:
                st.write(f"Found {len(filtered_data)} matching items:")
                filtered_df = pd.DataFrame(filtered_data)
                st.dataframe(filtered_df, hide_index=True, width='stretch')
            else:
                st.warning("No matching items found")
    
    else:
        st.info("No structured field-value pairs found. Try the Table View or check the Chunks tab.")


def render_table_view(result: Dict[str, Any]):
    """Render data in proper table format"""
    st.markdown("### 📈 Table View")
    
    chunks = result.get("chunks", [])
    
    if not chunks:
        st.info("No data available for table view")
        return
    
    # Create different table views
    st.markdown("**📋 Table Options:**")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        show_all_chunks = st.checkbox("All Chunks", value=True)
    
    with col2:
        show_text_only = st.checkbox("Text Only", value=False)
    
    with col3:
        show_with_metadata = st.checkbox("With Metadata", value=False)
    
    # Prepare table data
    table_data = []
    
    for i, chunk in enumerate(chunks):
        if show_text_only:
            table_data.append({
                "#": i + 1,
                "Text": chunk.get("text", ""),
                "Page": chunk.get("page", 1)
            })
        elif show_with_metadata:
            table_data.append({
                "#": i + 1,
                "Type": chunk.get("chunk_type", "unknown"),
                "Text": chunk.get("text", ""),
                "Page": chunk.get("page", 1),
                "Confidence": chunk.get("confidence", "N/A"),
                "Chunk ID": chunk.get("chunk_id", ""),
                "Has BBox": "✅" if chunk.get("bbox") else "❌"
            })
        else:
            # Default view
            table_data.append({
                "#": i + 1,
                "Type": chunk.get("chunk_type", "unknown"),
                "Text Preview": chunk.get("text", "")[:100] + "..." if len(chunk.get("text", "")) > 100 else chunk.get("text", ""),
                "Page": chunk.get("page", 1),
                "Confidence": chunk.get("confidence", "N/A")
            })
    
    if table_data:
        df = pd.DataFrame(table_data)
        
        # Configure columns based on view type
        if show_text_only:
            column_config = {
                "#": st.column_config.NumberColumn("#", width="small"),
                "Text": st.column_config.TextColumn("Text", width="large"),
                "Page": st.column_config.NumberColumn("Page", width="small")
            }
        elif show_with_metadata:
            column_config = {
                "#": st.column_config.NumberColumn("#", width="small"),
                "Type": st.column_config.TextColumn("Type", width="small"),
                "Text": st.column_config.TextColumn("Text", width="large"),
                "Page": st.column_config.NumberColumn("Page", width="small"),
                "Confidence": st.column_config.TextColumn("Confidence", width="small"),
                "Chunk ID": st.column_config.TextColumn("Chunk ID", width="medium"),
                "Has BBox": st.column_config.TextColumn("Has BBox", width="small")
            }
        else:
            column_config = {
                "#": st.column_config.NumberColumn("#", width="small"),
                "Type": st.column_config.TextColumn("Type", width="small"),
                "Text Preview": st.column_config.TextColumn("Text Preview", width="large"),
                "Page": st.column_config.NumberColumn("Page", width="small"),
                "Confidence": st.column_config.TextColumn("Confidence", width="small")
            }
        
        # Display the table
        st.dataframe(
            df,
            column_config=column_config,
            hide_index=True,
            width='stretch'
        )
        
        # Add filtering options
        st.markdown("**🔍 Filter Table:**")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Filter by chunk type
            chunk_types = list(set(chunk.get("chunk_type", "unknown") for chunk in chunks))
            selected_types = st.multiselect(
                "Filter by Type:",
                options=chunk_types,
                default=chunk_types,
                key="table_type_filter"
            )
        
        with col2:
            # Filter by page
            pages = list(set(chunk.get("page", 1) for chunk in chunks))
            selected_pages = st.multiselect(
                "Filter by Page:",
                options=pages,
                default=pages,
                key="table_page_filter"
            )
        
        # Apply filters
        if selected_types != chunk_types or selected_pages != pages:
            filtered_chunks = [chunk for chunk in chunks 
                             if chunk.get("chunk_type", "unknown") in selected_types 
                             and chunk.get("page", 1) in selected_pages]
            
            # Rebuild filtered table data
            filtered_table_data = []
            for i, chunk in enumerate(filtered_chunks):
                if show_text_only:
                    filtered_table_data.append({
                        "#": i + 1,
                        "Text": chunk.get("text", ""),
                        "Page": chunk.get("page", 1)
                    })
                elif show_with_metadata:
                    filtered_table_data.append({
                        "#": i + 1,
                        "Type": chunk.get("chunk_type", "unknown"),
                        "Text": chunk.get("text", ""),
                        "Page": chunk.get("page", 1),
                        "Confidence": chunk.get("confidence", "N/A"),
                        "Chunk ID": chunk.get("chunk_id", ""),
                        "Has BBox": "✅" if chunk.get("bbox") else "❌"
                    })
                else:
                    filtered_table_data.append({
                        "#": i + 1,
                        "Type": chunk.get("chunk_type", "unknown"),
                        "Text Preview": chunk.get("text", "")[:100] + "..." if len(chunk.get("text", "")) > 100 else chunk.get("text", ""),
                        "Page": chunk.get("page", 1),
                        "Confidence": chunk.get("confidence", "N/A")
                    })
            
            if filtered_table_data:
                filtered_df = pd.DataFrame(filtered_table_data)
                st.write(f"Showing {len(filtered_table_data)} of {len(table_data)} items")
                st.dataframe(
                    filtered_df,
                    column_config=column_config,
                    hide_index=True,
                    width='stretch'
                )
            else:
                st.warning("No items match the selected filters")
    
    else:
        st.warning("No data available to display")


def render_statistics_view(result: Dict[str, Any]):
    """Render processing statistics"""
    st.markdown("### 📊 Processing Statistics")
    
    # Processing metrics
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Document Information:**")
        st.write(f"- Document Type: {result.get('document_type', 'unknown').title()}")
        st.write(f"- Page Count: {result.get('page_count', 'N/A')}")
        st.write(f"- File Size: {result.get('file_size', 0) / 1024:.1f} KB")
        st.write(f"- OCR Engine: {result.get('ocr_engine', 'unknown').title()}")
    
    with col2:
        st.markdown("**Processing Metrics:**")
        st.write(f"- Processing Time: {result.get('processing_time', 0):.2f} seconds")
        st.write(f"- Success Status: {'✅ Success' if result.get('success') else '❌ Failed'}")
        chunks = result.get('chunks', [])
        if chunks is None:
            chunks = []
        st.write(f"- Chunks Extracted: {len(chunks)}")
        
        if result.get('model_version'):
            st.write(f"- Model Version: {result['model_version']}")
    
    # Chunk type distribution
    chunks = result.get("chunks", [])
    if chunks:
        st.markdown("**Chunk Type Distribution:**")
        
        chunk_types = {}
        for chunk in chunks:
            chunk_type = chunk.get("chunk_type", "unknown")
            chunk_types[chunk_type] = chunk_types.get(chunk_type, 0) + 1
        
        # Create pie chart
        chart_data = pd.DataFrame(
            list(chunk_types.items()),
            columns=["Type", "Count"]
        )
        
        st.bar_chart(chart_data.set_index("Type"))
        
        # Confidence distribution
        confidences = [chunk.get("confidence") for chunk in chunks if chunk.get("confidence") is not None]
        if confidences:
            st.markdown("**Confidence Score Distribution:**")
            confidence_df = pd.DataFrame(confidences, columns=["Confidence"])
            st.bar_chart(confidence_df, x="Confidence")



def _fetch_pdf_page(document_id: str, page_num: int, backend_url: str = "http://localhost:8000"):
    """Fetch a single PDF page as PNG bytes from the backend."""
    import requests as _req
    try:
        resp = _req.get(f"{backend_url}/api/v1/documents/{document_id}/pages/{page_num}", timeout=15)
        if resp.status_code == 200:
            return resp.content
    except Exception:
        pass
    return None


def _fetch_page_count(document_id: str, backend_url: str = "http://localhost:8000") -> int:
    """Fetch total page count for a PDF document from the backend."""
    import requests as _req
    try:
        resp = _req.get(f"{backend_url}/api/v1/documents/{document_id}/page_count", timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            return data.get("data", {}).get("page_count", 1)
    except Exception:
        pass
    return 1


def _confidence_badge(conf: float) -> str:
    """Return an emoji badge string for a confidence value (0.0–1.0)."""
    try:
        conf = float(conf)
    except (TypeError, ValueError):
        conf = 0.9
    if conf >= 0.85:
        return f"🟢 {conf:.0%}"
    elif conf >= 0.55:
        return f"🟡 {conf:.0%}"
    else:
        return f"🔴 {conf:.0%}"


def render_ai_analysis_view(result: dict):
    """AI Analysis tab: side-by-side PDF viewer (left) + structured extracted data (right)."""
    import streamlit as st
    import pandas as pd

    st.markdown("### 🤖 AI Analysis & Document Viewer")

    ai_analysis = result.get("ai_analysis")
    if not ai_analysis:
        st.warning("🤖 AI Analysis was not run. Make sure **Enable AI Analysis** is checked when uploading.")
        return

    doc_type = ai_analysis.get("document_type", "general")
    confidence = ai_analysis.get("confidence_score", 0.0)
    steps = ai_analysis.get("processing_steps", [])

    # ── Header metrics ──────────────────────────────────────────────────────
    m1, m2, m3 = st.columns(3)
    type_emoji = {
        "invoice": "🧾", "prescription": "💊", "medical_form": "🏥",
        "receipt": "🧾", "contract": "📝", "report": "📊",
        "form": "📋", "table": "📈", "general": "📄",
        "medical_invoice": "🏥",
    }.get(doc_type.lower(), "📄")
    with m1:
        st.metric(f"{type_emoji} Document Type", doc_type.replace("_", " ").title())
    with m2:
        st.metric("🎯 Overall Confidence", _confidence_badge(confidence))
    with m3:
        st.metric("⚡ Processing Steps", len(steps))

    # ── Summary banner ───────────────────────────────────────────────────────
    summary = ai_analysis.get("summary", "")
    if summary:
        st.info(f"📝 {summary}")

    st.markdown("---")

    # ── Side-by-side layout ─────────────────────────────────────────────────
    document_id = result.get("document_id", "")
    doc_is_pdf = str(result.get("document_type", "")).lower() == "pdf"
    backend_url = st.session_state.get("backend_url", "http://localhost:8000")

    if doc_is_pdf and document_id:
        left_col, right_col = st.columns([4, 6])
    else:
        left_col = None
        right_col = st.container()

    # ── LEFT: PDF Page Viewer ───────────────────────────────────────────────
    if left_col is not None:
        with left_col:
            st.markdown("#### 📄 Document Preview")

            page_count_key = f"pdf_page_count_{document_id}"
            page_idx_key   = f"pdf_page_idx_{document_id}"

            if page_count_key not in st.session_state:
                st.session_state[page_count_key] = _fetch_page_count(document_id, backend_url)
            if page_idx_key not in st.session_state:
                st.session_state[page_idx_key] = 0

            page_count   = st.session_state[page_count_key]
            current_page = st.session_state[page_idx_key]

            nav1, nav2, nav3 = st.columns([1, 2, 1])
            with nav1:
                if st.button("⬅ Prev", key=f"pdf_prev_{document_id}", disabled=current_page <= 0):
                    st.session_state[page_idx_key] -= 1
                    st.rerun()
            with nav2:
                st.markdown(
                    f"<div style='text-align:center;padding-top:6px'>"
                    f"Page {current_page + 1} / {page_count}</div>",
                    unsafe_allow_html=True,
                )
            with nav3:
                if st.button("Next ➡", key=f"pdf_next_{document_id}", disabled=current_page >= page_count - 1):
                    st.session_state[page_idx_key] += 1
                    st.rerun()

            img_bytes = _fetch_pdf_page(document_id, current_page, backend_url)
            if img_bytes:
                st.image(img_bytes, caption=f"Page {current_page + 1}", use_container_width=True)
            else:
                st.warning("⚠️ Could not load page preview")

    # ── RIGHT: Extracted Data ───────────────────────────────────────────────
    with right_col:
        # Key Insights
        insights = ai_analysis.get("key_insights", [])
        if insights:
            st.markdown("#### 🔍 Key Insights")
            for i, insight in enumerate(insights, 1):
                st.markdown(f"> **{i}.** {insight}")

        entities = ai_analysis.get("extracted_entities", {})
        if entities:
            st.markdown("#### 🏷️ Extracted Data")

            # ── All fields with per-field confidence color coding ───────
            all_fields = entities.get("all_fields_in_order", [])
            if all_fields and isinstance(all_fields, list):
                st.markdown("**📋 All Fields — with Confidence Scores:**")
                rows = []
                for item in all_fields:
                    if isinstance(item, dict):
                        conf_val = item.get("confidence", 0.9)
                        rows.append({
                            "Field":      item.get("field", ""),
                            "Value":      str(item.get("value", "")),
                            "Category":   item.get("category", "").replace("_", " ").title(),
                            "Confidence": _confidence_badge(conf_val),
                        })
                if rows:
                    df_fields = pd.DataFrame(rows)
                    st.dataframe(
                        df_fields,
                        column_config={
                            "Field":      st.column_config.TextColumn("Field",      width="medium"),
                            "Value":      st.column_config.TextColumn("Value",      width="large"),
                            "Category":   st.column_config.TextColumn("Category",   width="small"),
                            "Confidence": st.column_config.TextColumn("Confidence", width="small"),
                        },
                        hide_index=True,
                        use_container_width=True,
                    )

            # ── Section-by-section breakdown ────────────────────────────
            section_keys = [k for k in entities.keys() if k != "all_fields_in_order"]
            if section_keys:
                st.markdown("**📂 Data by Section:**")
                for section_key in section_keys:
                    section_data  = entities[section_key]
                    section_title = section_key.replace("_", " ").title()

                    with st.expander(f"📌 {section_title}", expanded=True):
                        if isinstance(section_data, dict):
                            rows = [
                                {"Field": k.replace("_", " ").title(), "Value": str(v)}
                                for k, v in section_data.items()
                                if v not in [None, "", [], {}]
                            ]
                            if rows:
                                df = pd.DataFrame(rows)
                                st.dataframe(df, hide_index=True, use_container_width=True,
                                             column_config={
                                                 "Field": st.column_config.TextColumn("Field", width="medium"),
                                                 "Value": st.column_config.TextColumn("Value", width="large"),
                                             })
                            else:
                                st.caption("No data in this section")

                        elif isinstance(section_data, list) and section_data:
                            if isinstance(section_data[0], dict):
                                has_cpt = any("cpt_code" in item for item in section_data)
                                if has_cpt:
                                    priority = ["cpt_code", "description", "quantity", "unit_price",
                                                "total_price", "date_of_service", "diagnosis_code", "modifier"]
                                    all_keys = list(dict.fromkeys(
                                        priority + [k for row in section_data for k in row.keys()]
                                    ))
                                    present_keys = [k for k in all_keys if any(k in row for row in section_data)]
                                    col_rename = {
                                        "cpt_code": "CPT Code", "description": "Description",
                                        "quantity": "Qty",       "unit_price":  "Unit Price",
                                        "total_price": "Total",  "date_of_service": "Date of Service",
                                        "diagnosis_code": "Dx Code", "modifier": "Modifier",
                                    }
                                    rows = [{k: row.get(k, "") for k in present_keys} for row in section_data]
                                    df = pd.DataFrame(rows, columns=present_keys)
                                    df.rename(columns={k: v for k, v in col_rename.items() if k in df.columns}, inplace=True)
                                    st.dataframe(df, hide_index=True, use_container_width=True,
                                                 column_config={
                                                     "CPT Code":    st.column_config.TextColumn("CPT Code",    width="small"),
                                                     "Description": st.column_config.TextColumn("Description", width="large"),
                                                 })
                                else:
                                    df = pd.DataFrame(section_data)
                                    st.dataframe(df, hide_index=True, use_container_width=True)
                            else:
                                for item in section_data:
                                    st.markdown(f"• {item}")
                        elif isinstance(section_data, list):
                            st.caption("Empty section")
                        else:
                            st.write(f"**{section_title}:** {section_data}")
        else:
            st.info("No structured entities extracted by AI.")

        # ── Recommendations ─────────────────────────────────────────────
        recommendations = ai_analysis.get("recommendations", [])
        if recommendations:
            st.markdown("---")
            st.markdown("#### 💡 AI Recommendations")
            for i, rec in enumerate(recommendations, 1):
                st.success(f"**{i}.** {rec}")

        # ── Processing pipeline ──────────────────────────────────────────
        with st.expander("🔧 Processing Pipeline"):
            for step in steps:
                st.write(f"✅ {step}")
            st.write(f"• Confidence: {confidence:.0%}")
            st.write(f"• Document Type: {doc_type}")


def render_json_view(result: Dict[str, Any]):
    """Render raw JSON view"""
    st.markdown("### 🔍 Raw JSON Data")
    
    # Display options
    col1, col2 = st.columns(2)
    
    with col1:
        show_full_json = st.checkbox(
            "Show Full JSON",
            value=False,
            help="Show complete JSON response including all metadata"
        )
    
    with col2:
        if st.button("📥 Download JSON"):
            json_data = json.dumps(result, indent=2, ensure_ascii=False)
            st.download_button(
                label="Download",
                data=json_data,
                file_name="processing_result.json",
                mime="application/json"
            )
    
    # Prepare JSON data
    if show_full_json:
        json_data = json.dumps(result, indent=2, ensure_ascii=False)
    else:
        # Show only essential data
        essential_data = {
            "success": result.get("success"),
            "ocr_engine": result.get("ocr_engine"),
            "processing_time": result.get("processing_time"),
            "document_type": result.get("document_type"),
            "page_count": result.get("page_count"),
            "chunks_count": len(result.get("chunks", []) if result.get("chunks", []) is not None else 0),
            "markdown_preview": result.get("markdown", "")[:500] + "..." if result.get("markdown") else ""
        }
        json_data = json.dumps(essential_data, indent=2, ensure_ascii=False)
    
    # Display JSON with proper formatting
    st.json(json.loads(json_data))


def render_export_preview(result: Dict[str, Any]):
    """Render a preview of what will be exported to Excel"""
    st.markdown("### 📋 Excel Export Preview")
    
    chunks = result.get("chunks", [])
    
    if not chunks:
        st.info("No data available for export")
        return
    
    # Analyze chunks for preview
    chunk_types = {}
    for chunk in chunks:
        chunk_type = chunk.get("chunk_type", "unknown")
        chunk_types[chunk_type] = chunk_types.get(chunk_type, 0) + 1
    
    # Show summary
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Chunks", len(chunks))
    
    with col2:
        st.metric("Text Chunks", chunk_types.get("text", 0))
    
    with col3:
        st.metric("Table Chunks", chunk_types.get("table", 0))
    
    with col4:
        st.metric("Form Chunks", chunk_types.get("form", 0))
    
    # Show sample structured data
    st.markdown("**Sample Extracted Data:**")
    
    # Extract some sample data
    sample_data = []
    for chunk in chunks[:5]:  # Show first 5 chunks
        text = chunk.get("text", "").strip()
        if text and len(text) > 10:
            sample_data.append({
                "Type": chunk.get("chunk_type", "unknown"),
                "Page": chunk.get("page", 1),
                "Preview": text[:100] + "..." if len(text) > 100 else text
            })
    
    if sample_data:
        df = pd.DataFrame(sample_data)
        st.dataframe(df, width='stretch')
    
    # Show what sheets will be created
    st.markdown("**Excel Sheets That Will Be Created:**")
    
    sheets_info = [
        "📊 **Summary** - Document metadata and processing info",
        "📋 **Extracted Data** - Structured field-value pairs",
        "📄 **All Chunks** - Complete list of extracted chunks",
        "📈 **Tables** - Table-specific data (if found)",
        "📝 **Forms** - Form field data (if found)",
        "📚 **Raw Text** - Full extracted text"
    ]
    
    for sheet_info in sheets_info:
        st.write(f"• {sheet_info}")
    
    # Highlight special features
    if chunk_types.get("table", 0) > 0:
        st.success(f"✅ {chunk_types.get('table', 0)} table(s) detected - will be exported in structured format")
    
    if chunk_types.get("form", 0) > 0:
        st.success(f"✅ {chunk_types.get('form', 0)} form(s) detected - will be exported with field extraction")
    
    # Check for invoice-like patterns
    invoice_indicators = 0
    for chunk in chunks:
        text = chunk.get("text", "").lower()
        if any(indicator in text for indicator in ["invoice", "bill", "amount", "total", "$", "due"]):
            invoice_indicators += 1
    
    if invoice_indicators > 0:
        st.info(f"💰 Invoice-like patterns detected in {invoice_indicators} chunks - special line item extraction will be applied")


def create_download_buttons(result: Dict[str, Any]):
    """Create download buttons for different formats"""
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        # Text download
        text_content = extract_text_content(result)
        st.download_button(
            label="📄 Download Text",
            data=text_content,
            file_name=f"extracted_text_{result.get('document_id', 'unknown')}.txt",
            mime="text/plain",
            key="download_text"
        )
    
    with col2:
        # JSON download
        json_content = json.dumps(result, indent=2, ensure_ascii=False)
        st.download_button(
            label="🔍 Download JSON",
            data=json_content,
            file_name=f"ocr_result_{result.get('document_id', 'unknown')}.json",
            mime="application/json",
            key="download_json"
        )
    
    with col3:
        # CSV download
        csv_content = create_csv_export(result)
        st.download_button(
            label="📊 Download CSV",
            data=csv_content,
            file_name=f"extracted_data_{result.get('document_id', 'unknown')}.csv",
            mime="text/csv",
            key="download_csv"
        )
    
    with col4:
        # Excel download (Enhanced if AI analysis available)
        if result.get('ai_analysis'):
            # Use enhanced Excel export with AI analysis
            excel_content = create_enhanced_excel_export(result)
            st.download_button(
                label="📈 Download Enhanced Excel",
                data=excel_content.getvalue(),
                file_name=f"ai_analysis_{result.get('document_id', 'unknown')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                key="download_enhanced_excel"
            )
        else:
            # Use standard Excel export
            excel_content = create_excel_export(result)
            st.download_button(
                label="📈 Download Excel",
                data=excel_content.getvalue(),
                file_name=f"ocr_result_{result.get('document_id', 'unknown')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                key="download_excel"
            )
    
    # Additional export options
    st.markdown("### 📋 Advanced Export Options")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("📚 Complete Excel (All Sheets)"):
            try:
                excel_data = create_excel_export(result)
                st.download_button(
                    label="Download Complete Excel",
                    data=excel_data.getvalue(),
                    file_name="complete_extraction.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
            except Exception as e:
                st.error(f"Error creating complete Excel file: {e}")
    
    with col2:
        if st.button("🧹 Clean Data Excel"):
            try:
                # Create a cleaner version with better formatting
                excel_data = create_structured_excel(result)
                st.download_button(
                    label="Download Clean Excel",
                    data=excel_data.getvalue(),
                    file_name="clean_extraction.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
            except Exception as e:
                st.error(f"Error creating clean Excel file: {e}")
