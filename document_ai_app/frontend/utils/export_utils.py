"""
Export utilities for extracted data
"""
import pandas as pd
import io
import json
from typing import Dict, Any, List
from shared.models.document import ExtractedChunk


def create_excel_export(result_data: Dict[str, Any]) -> io.BytesIO:
    """
    Create Excel file from extracted data
    
    Args:
        result_data: Processing result data
        
    Returns:
        Excel file as BytesIO
    """
    # Create Excel writer
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        
        # Sheet 1: Summary Information
        summary_data = {
            'Metric': ['Document ID', 'OCR Engine', 'Processing Time (s)', 
                      'Document Type', 'Page Count', 'Total Chunks', 'Success'],
            'Value': [
                result_data.get('document_id', 'N/A'),
                result_data.get('ocr_engine', 'N/A'),
                f"{result_data.get('processing_time', 0):.2f}",
                result_data.get('document_type', 'N/A'),
                result_data.get('page_count', 'N/A'),
                len(result_data.get('chunks', []) if result_data.get('chunks', []) is not None else 0),
                result_data.get('success', False)
            ]
        }
        summary_df = pd.DataFrame(summary_data)
        summary_df.to_excel(writer, sheet_name='Summary', index=False)
        
        # Sheet 2: All Extracted Chunks
        chunks = result_data.get('chunks', [])
        if chunks:
            chunks_data = []
            for i, chunk in enumerate(chunks):
                chunks_data.append({
                    'Chunk ID': chunk.get('chunk_id', f'chunk_{i}'),
                    'Type': chunk.get('chunk_type', 'unknown'),
                    'Page': chunk.get('page', 'N/A'),
                    'Confidence': chunk.get('confidence', 'N/A'),
                    'Text': chunk.get('text', ''),
                    'X0': chunk.get('bbox', {}).get('x0', '') if chunk.get('bbox') else '',
                    'Y0': chunk.get('bbox', {}).get('y0', '') if chunk.get('bbox') else '',
                    'X1': chunk.get('bbox', {}).get('x1', '') if chunk.get('bbox') else '',
                    'Y1': chunk.get('bbox', {}).get('y1', '') if chunk.get('bbox') else ''
                })
            
            chunks_df = pd.DataFrame(chunks_data)
            chunks_df.to_excel(writer, sheet_name='All Chunks', index=False)
            
            # Sheet 3: Table Data (if any)
            table_chunks = [chunk for chunk in chunks if chunk.get('chunk_type') == 'table']
            if table_chunks:
                table_data = []
                for i, chunk in enumerate(table_chunks):
                    table_data.append({
                        'Table ID': chunk.get('chunk_id', f'table_{i}'),
                        'Page': chunk.get('page', 'N/A'),
                        'Extracted Text': chunk.get('text', ''),
                        'Confidence': chunk.get('confidence', 'N/A')
                    })
                
                table_df = pd.DataFrame(table_data)
                table_df.to_excel(writer, sheet_name='Tables', index=False)
            
            # Sheet 4: Form Data (if any)
            form_chunks = [chunk for chunk in chunks if chunk.get('chunk_type') == 'form']
            if form_chunks:
                form_data = []
                for i, chunk in enumerate(form_chunks):
                    form_data.append({
                        'Form ID': chunk.get('chunk_id', f'form_{i}'),
                        'Page': chunk.get('page', 'N/A'),
                        'Extracted Text': chunk.get('text', ''),
                        'Confidence': chunk.get('confidence', 'N/A')
                    })
                
                form_df = pd.DataFrame(form_data)
                form_df.to_excel(writer, sheet_name='Forms', index=False)
            
            # Sheet 5: Raw Text
            raw_text = result_data.get('raw_text', '') or result_data.get('markdown', '')
            if raw_text:
                text_data = pd.DataFrame({'Content': [raw_text]})
                text_data.to_excel(writer, sheet_name='Raw Text', index=False)
    
    output.seek(0)
    return output


def create_structured_excel(result_data: Dict[str, Any]) -> io.BytesIO:
    """
    Create structured Excel file with better formatting for tables/invoices
    
    Args:
        result_data: Processing result data
        
    Returns:
        Excel file as BytesIO
    """
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        
        chunks = result_data.get('chunks', [])
        
        # Try to extract structured data from text
        structured_data = extract_structured_data(chunks)
        
        # Sheet 1: Summary
        summary_data = {
            'Field': ['Document ID', 'OCR Engine', 'Processing Time', 'Total Items Found'],
            'Value': [
                result_data.get('document_id', 'N/A'),
                result_data.get('ocr_engine', 'N/A'),
                f"{result_data.get('processing_time', 0):.2f}s",
                len(structured_data)
            ]
        }
        pd.DataFrame(summary_data).to_excel(writer, sheet_name='Summary', index=False)
        
        # Sheet 2: Structured Data
        if structured_data:
            df = pd.DataFrame(structured_data)
            df.to_excel(writer, sheet_name='Extracted Data', index=False)
        else:
            # Fallback to chunk data
            chunks_data = []
            for chunk in chunks:
                chunks_data.append({
                    'Type': chunk.get('chunk_type', 'unknown'),
                    'Content': chunk.get('text', ''),
                    'Page': chunk.get('page', 'N/A')
                })
            pd.DataFrame(chunks_data).to_excel(writer, sheet_name='Extracted Data', index=False)
        
        # Sheet 3: Line Items (if invoice-like data detected)
        line_items = extract_line_items(chunks)
        if line_items:
            pd.DataFrame(line_items).to_excel(writer, sheet_name='Line Items', index=False)
    
    output.seek(0)
    return output


def extract_structured_data(chunks: List[Dict[str, Any]]) -> List[Dict[str, str]]:
    """
    Extract structured data from chunks
    
    Args:
        chunks: List of extracted chunks
        
    Returns:
        List of structured data items
    """
    structured_data = []
    
    for chunk in chunks:
        text = chunk.get('text', '').strip()
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
                        'Field': key,
                        'Value': value,
                        'Type': chunk.get('chunk_type', 'text'),
                        'Page': chunk.get('page', 1),
                        'Confidence': chunk.get('confidence', 'N/A')
                    })
            elif any(keyword in line.lower() for keyword in ['$', 'amount', 'total', 'price']):
                # Likely a monetary value or important line item
                structured_data.append({
                    'Field': 'Extracted Line',
                    'Value': line,
                    'Type': chunk.get('chunk_type', 'text'),
                    'Page': chunk.get('page', 1),
                    'Confidence': chunk.get('confidence', 'N/A')
                })
    
    return structured_data


def extract_line_items(chunks: List[Dict[str, Any]]) -> List[Dict[str, str]]:
    """
    Extract line items from invoice-like documents
    
    Args:
        chunks: List of extracted chunks
        
    Returns:
        List of line items
    """
    line_items = []
    
    for chunk in chunks:
        text = chunk.get('text', '').strip()
        if not text:
            continue
        
        lines = text.split('\n')
        for i, line in enumerate(lines):
            line = line.strip()
            
            # Look for patterns that suggest line items
            if ('$' in line or 'amount' in line.lower() or 
                any(char.isdigit() for char in line)) and len(line) > 10:
                
                # Try to extract description and amount
                parts = line.split()
                description = ' '.join(parts[:-2]) if len(parts) > 2 else line
                amount = parts[-1] if parts else ''
                
                if '$' in amount or amount.replace('.', '').isdigit():
                    line_items.append({
                        'Description': description,
                        'Amount': amount,
                        'Page': chunk.get('page', 1),
                        'Line Number': i + 1
                    })
    
    return line_items


def create_csv_export(result_data: Dict[str, Any]) -> str:
    """
    Create CSV export of extracted data
    
    Args:
        result_data: Processing result data
        
    Returns:
        CSV string
    """
    chunks = result_data.get('chunks', [])
    
    # Create structured data
    structured_data = extract_structured_data(chunks)
    
    if structured_data:
        df = pd.DataFrame(structured_data)
        return df.to_csv(index=False)
    else:
        # Fallback to simple chunk data
        chunks_data = []
        for chunk in chunks:
            chunks_data.append({
                'Type': chunk.get('chunk_type', 'unknown'),
                'Text': chunk.get('text', ''),
                'Page': chunk.get('page', 'N/A')
            })
        df = pd.DataFrame(chunks_data)
        return df.to_csv(index=False)


def create_enhanced_excel_export(result_data: Dict[str, Any]) -> io.BytesIO:
    """
    Create enhanced Excel file with AI analysis and detailed invoice data
    
    Args:
        result_data: Processing result data with AI analysis
        
    Returns:
        Enhanced Excel file as BytesIO
    """
    # Create Excel writer
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        
        # Sheet 1: Invoice Summary
        create_invoice_summary_sheet(writer, result_data)
        
        # Sheet 2: Detailed Line Items
        create_detailed_line_items_sheet(writer, result_data)
        
        # Sheet 3: AI Analysis
        create_ai_analysis_sheet(writer, result_data)
        
        # Sheet 4: Raw OCR Data
        create_raw_ocr_sheet(writer, result_data)
        
        # Sheet 5: All Chunks
        create_chunks_sheet(writer, result_data)
    
    output.seek(0)
    return output


def create_invoice_summary_sheet(writer, result_data: Dict[str, Any]):
    """Create invoice summary sheet with all header information"""
    ai_analysis = result_data.get('ai_analysis', {})
    entities = ai_analysis.get('extracted_entities', {})
    
    summary_data = {
        'Field': [
            'Invoice Number',
            'Invoice Date', 
            'Due Date',
            'Purchase Order',
            'Vendor Name',
            'Vendor Address',
            'Vendor Phone',
            'Vendor Email',
            'Customer Name',
            'Customer Account',
            'Billing Address',
            'Shipping Address',
            'Subtotal',
            'Tax Amount',
            'Total Amount',
            'Currency',
            'Payment Terms'
        ],
        'Value': [
            entities.get('invoice_number', ''),
            entities.get('invoice_date', ''),
            entities.get('due_date', ''),
            entities.get('purchase_order', ''),
            entities.get('vendor_name', ''),
            entities.get('vendor_address', ''),
            entities.get('vendor_phone', ''),
            entities.get('vendor_email', ''),
            entities.get('customer_name', ''),
            entities.get('customer_account', ''),
            entities.get('billing_address', ''),
            entities.get('shipping_address', ''),
            entities.get('subtotal', ''),
            entities.get('tax_amount', ''),
            entities.get('total_amount', ''),
            entities.get('currency', ''),
            entities.get('payment_terms', '')
        ]
    }
    
    df = pd.DataFrame(summary_data)
    df.to_excel(writer, sheet_name='Invoice Summary', index=False)


def create_detailed_line_items_sheet(writer, result_data: Dict[str, Any]):
    """Create detailed line items sheet with all invoice table data"""
    ai_analysis = result_data.get('ai_analysis', {})
    entities = ai_analysis.get('extracted_entities', {})
    line_items = entities.get('line_items', [])
    
    if not line_items:
        # Create empty sheet with headers
        empty_data = {
            'Item Number': [],
            'Description': [],
            'Quantity': [],
            'Unit Price': [],
            'Total Price': [],
            'CPT/HCPCS Code': [],
            'Service Code': [],
            'Diagnosis Code': [],
            'Modifier': [],
            'Units': [],
            'Date of Service': [],
            'Category': [],
            'Taxable': [],
            'Discount': []
        }
        df = pd.DataFrame(empty_data)
        df.to_excel(writer, sheet_name='Line Items', index=False)
        return
    
    # Create detailed line items data
    line_items_data = []
    for item in line_items:
        line_items_data.append({
            'Item Number': item.get('item_number', ''),
            'Description': item.get('description', ''),
            'Quantity': item.get('quantity', ''),
            'Unit Price': item.get('unit_price', ''),
            'Total Price': item.get('total_price', ''),
            'CPT/HCPCS Code': item.get('cpt_code', ''),
            'Service Code': item.get('service_code', ''),
            'Diagnosis Code': item.get('diagnosis_code', ''),
            'Modifier': item.get('modifier', ''),
            'Units': item.get('units', ''),
            'Date of Service': item.get('date_of_service', ''),
            'Category': item.get('category', ''),
            'Taxable': item.get('taxable', ''),
            'Discount': item.get('discount', '')
        })
    
    df = pd.DataFrame(line_items_data)
    df.to_excel(writer, sheet_name='Line Items', index=False)


def create_ai_analysis_sheet(writer, result_data: Dict[str, Any]):
    """Create AI analysis sheet with insights and recommendations"""
    ai_analysis = result_data.get('ai_analysis', {})
    
    # AI Summary
    summary_data = {
        'Analysis Field': [
            'Document Type',
            'AI Summary',
            'Confidence Score',
            'Processing Steps',
            'Total Insights',
            'Total Recommendations'
        ],
        'Value': [
            ai_analysis.get('document_type', ''),
            ai_analysis.get('summary', ''),
            ai_analysis.get('confidence_score', ''),
            ', '.join(ai_analysis.get('processing_steps', [])),
            len(ai_analysis.get('key_insights', [])),
            len(ai_analysis.get('recommendations', []))
        ]
    }
    
    df_summary = pd.DataFrame(summary_data)
    df_summary.to_excel(writer, sheet_name='AI Analysis', index=False, startrow=0)
    
    # Key Insights
    insights = ai_analysis.get('key_insights', [])
    if insights:
        insights_data = {
            'Insight Number': list(range(1, len(insights) + 1)),
            'Key Insight': insights
        }
        df_insights = pd.DataFrame(insights_data)
        df_insights.to_excel(writer, sheet_name='AI Analysis', index=False, startrow=len(summary_data) + 3)
    
    # Recommendations
    recommendations = ai_analysis.get('recommendations', [])
    if recommendations:
        rec_data = {
            'Recommendation Number': list(range(1, len(recommendations) + 1)),
            'Recommendation': recommendations
        }
        df_rec = pd.DataFrame(rec_data)
        df_rec.to_excel(writer, sheet_name='AI Analysis', index=False, startrow=len(summary_data) + len(insights) + 6)


def create_raw_ocr_sheet(writer, result_data: Dict[str, Any]):
    """Create raw OCR data sheet"""
    chunks = result_data.get('chunks', [])
    
    raw_data = []
    for i, chunk in enumerate(chunks):
        raw_data.append({
            'Chunk ID': chunk.get('chunk_id', f'chunk_{i}'),
            'Type': chunk.get('chunk_type', 'unknown'),
            'Page': chunk.get('page', 'N/A'),
            'Confidence': chunk.get('confidence', 'N/A'),
            'Text': chunk.get('text', ''),
            'Bounding Box': str(chunk.get('bbox', ''))
        })
    
    df = pd.DataFrame(raw_data)
    df.to_excel(writer, sheet_name='Raw OCR Data', index=False)


def create_chunks_sheet(writer, result_data: Dict[str, Any]):
    """Create chunks sheet for compatibility"""
    chunks = result_data.get('chunks', [])
    
    chunks_data = []
    for i, chunk in enumerate(chunks):
        chunks_data.append({
            'Chunk ID': chunk.get('chunk_id', f'chunk_{i}'),
            'Type': chunk.get('chunk_type', 'unknown'),
            'Page': chunk.get('page', 'N/A'),
            'Text': chunk.get('text', ''),
            'Confidence': chunk.get('confidence', 'N/A')
        })
    
    df = pd.DataFrame(chunks_data)
    df.to_excel(writer, sheet_name='All Chunks', index=False)
