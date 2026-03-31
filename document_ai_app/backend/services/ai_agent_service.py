"""
AI Agent Service for Agentic Document Processing
"""
import logging
import json
import asyncio
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

try:
    from langchain_groq import ChatGroq
    GROQ_AVAILABLE = True
except ImportError:
    GROQ_AVAILABLE = False
    logger.warning("langchain-groq not available, install langchain-groq")

try:
    from langchain_core.prompts import PromptTemplate
    from langchain.chains import LLMChain
    LANGCHAIN_AVAILABLE = True
except ImportError:
    LANGCHAIN_AVAILABLE = False
    logger.warning("LangChain not available, AI analysis will be limited")

from core.config import settings

class DocumentType(Enum):
    """Document types for AI processing"""
    INVOICE = "invoice"
    RECEIPT = "receipt"
    CONTRACT = "contract"
    REPORT = "report"
    FORM = "form"
    TABLE = "table"
    GENERAL = "general"

@dataclass
class AIProcessingResult:
    """Result of AI processing"""
    document_type: str
    summary: str
    key_insights: List[str]
    extracted_entities: Dict[str, Any]
    recommendations: List[str]
    confidence_score: float
    processing_steps: List[str]

class AIAgentService:
    """AI Agent Service for intelligent document processing"""
    
    def __init__(self):
        self.openai_client = None
        self.langchain_llm = None
        self.agent_executor = None
        self._initialize_ai_services()
    
    def _initialize_ai_services(self):
        """Initialize AI services based on available API keys"""
        self.groq_llm = None
        self.langchain_llm = None
        self.openai_client = None

        # Primary: Groq (fast, free tier available)
        if GROQ_AVAILABLE and settings.GROQ_API_KEY:
            try:
                self.groq_llm = ChatGroq(
                    api_key=settings.GROQ_API_KEY,
                    model_name="llama-3.3-70b-versatile",
                    temperature=0.1,
                    max_tokens=4096,
                )
                logger.info("Groq LLM initialized (llama-3.3-70b-versatile)")
            except Exception as e:
                logger.warning(f"Failed to initialize Groq: {e}")
                self.groq_llm = None
        else:
            logger.warning("Groq not available or GROQ_API_KEY not set")

        # Fallback: OpenAI
        try:
            import openai as _openai
            if settings.OPENAI_API_KEY and settings.OPENAI_API_KEY != "your_openai_api_key_here":
                self.openai_client = _openai.OpenAI(api_key=settings.OPENAI_API_KEY)
                logger.info("OpenAI client initialized as fallback")
            else:
                logger.warning("OpenAI API key not found or is placeholder")
        except ImportError:
            logger.warning("openai package not available")
    
    async def analyze_document_intelligently(self,
                                       ocr_result: Dict[str, Any],
                                       document_content: str = None) -> AIProcessingResult:
        """
        Perform intelligent document analysis using Groq LLM.
        Auto-detects document type and extracts structured data.
        """
        try:
            if not document_content:
                document_content = self._extract_text_content(ocr_result)

            if not document_content or len(document_content.strip()) < 20:
                return self._create_fallback_result(document_content or "", "general")

            # Use Groq as primary, OpenAI as fallback
            llm = self.groq_llm
            if llm is None and self.openai_client is not None:
                return await self._analyze_with_openai(document_content)
            if llm is None:
                logger.warning("No LLM available, using fallback analysis")
                return self._create_fallback_result(document_content, "general")

            return await self._analyze_with_groq(document_content, llm)

        except Exception as e:
            logger.error(f"Error in intelligent document analysis: {e}")
            return self._create_fallback_result(document_content or "", "general")

    async def _analyze_with_groq(self, content: str, llm) -> AIProcessingResult:
        """Core analysis using Groq LLM with a unified smart prompt."""

        # ── Smart multi-page content sampler ─────────────────────────────────
        # _extract_text_content emits "=== PAGE N ===" headers. We sample
        # up to 2000 chars per page so ALL pages are represented in the prompt.
        # Groq llama-3.3-70b has 128k context — 24k chars is comfortably safe.
        MAX_TOTAL_CHARS = 24_000
        CHARS_PER_PAGE  = 2_000

        import re as _re
        page_blocks = _re.split(r'\n=== PAGE \d+ ===\n', content)
        if len(page_blocks) > 1:
            # Omit leading empty block before the first header
            page_blocks = [b for b in page_blocks if b.strip()]
            sampled_parts = [b[:CHARS_PER_PAGE] for b in page_blocks]
            document_text = "\n\n---\n\n".join(sampled_parts)[:MAX_TOTAL_CHARS]
        else:
            # No page headers — flat content; just cap at MAX_TOTAL_CHARS
            document_text = content[:MAX_TOTAL_CHARS]
        # ─────────────────────────────────────────────────────────────────────

        prompt = f"""You are an expert document intelligence system. Analyze the following document text and extract ALL information in a structured, ordered format.

DOCUMENT TEXT:
{document_text}

Instructions:
1. First detect the document type (invoice, prescription, medical_form, receipt, contract, report, form, table, general)
2. Extract ALL relevant fields grouped into logical named sections (patient_info, medications, billing, provider_info, etc.)
3. For medical/pharmacy: extract patient info, medications, dosages, prescriber, dates
4. For invoices/receipts: extract vendor, customer, line_items, totals, dates
5. For forms: extract all field-value pairs in order

CRITICAL CPT CODE RULE:
- If a description contains a 5-digit number followed by a dash, like "99243 - OFFICE/OP CONSLT...", ALWAYS split:
  - "cpt_code": "99243"
  - "description": "OFFICE/OP CONSLT..."
- HCPCS codes start with a letter (e.g. A0428) — same rule applies
- Never embed the CPT/HCPCS code inside the description field

CONFIDENCE RULE (very important):
- For EVERY item in all_fields_in_order, add a "confidence" float from 0.0 to 1.0:
  - 1.0 = value was clearly printed and unambiguous
  - 0.7-0.9 = value was slightly ambiguous but likely correct
  - 0.4-0.6 = value was inferred, partially legible, or uncertain
  - 0.0-0.3 = value is a guess, OCR may be wrong

Respond ONLY with valid JSON in this exact format:
{{
  "document_type": "detected type",
  "summary": "2-3 sentence summary of what this document is and its key purpose",
  "key_insights": [
    "Most important finding 1",
    "Most important finding 2",
    "Most important finding 3"
  ],
  "extracted_entities": {{
    "patient_info": {{
      "patient_name": "value",
      "date_of_birth": "value",
      "account_number": "value"
    }},
    "provider_info": {{
      "provider_name": "value",
      "npi": "value",
      "phone": "value"
    }},
    "line_items": [
      {{
        "cpt_code": "5-digit CPT or letter+4-digit HCPCS code",
        "description": "procedure description only, no code",
        "quantity": "qty",
        "unit_price": "price",
        "total_price": "line total",
        "date_of_service": "date",
        "diagnosis_code": "ICD-10 if present",
        "modifier": "modifier if present"
      }}
    ],
    "all_fields_in_order": [
      {{
        "field": "Field Name",
        "value": "Extracted Value",
        "category": "section name",
        "confidence": 0.95
      }}
    ]
  }},
  "recommendations": [
    "Actionable recommendation 1",
    "Actionable recommendation 2"
  ]
}}"""

        try:
            response = await llm.ainvoke(prompt)
            result_text = response.content if hasattr(response, 'content') else str(response)

            # Strip markdown code fences if present
            result_text = result_text.strip()
            if result_text.startswith("```"):
                result_text = result_text.split("```")[1]
                if result_text.startswith("json"):
                    result_text = result_text[4:]
            result_text = result_text.strip().rstrip("`")

            ai_data = json.loads(result_text)

            # ── Post-process: ensure CPT codes are always split from descriptions ──
            import re
            _CPT_RE = re.compile(r'^(\d{5})\s*[-–]\s*(.+)$', re.DOTALL)

            def _split_cpt(item: dict) -> dict:
                """If description contains a leading 5-digit code, move it to cpt_code."""
                desc = item.get("description", "")
                if desc and not item.get("cpt_code"):
                    m = _CPT_RE.match(desc.strip())
                    if m:
                        item["cpt_code"] = m.group(1)
                        item["description"] = m.group(2).strip()
                return item

            entities = ai_data.get("extracted_entities", {})
            for key, val in entities.items():
                if isinstance(val, list):
                    entities[key] = [_split_cpt(i) if isinstance(i, dict) else i for i in val]

            doc_type = ai_data.get("document_type", "general").lower()
            return AIProcessingResult(
                document_type=doc_type,
                summary=ai_data.get("summary", ""),
                key_insights=ai_data.get("key_insights", []),
                extracted_entities=ai_data.get("extracted_entities", {}),
                recommendations=ai_data.get("recommendations", []),
                confidence_score=0.88,
                processing_steps=["LandingAI ADE OCR", "Groq llama-3.3-70b analysis", "Structured extraction"]
            )

        except json.JSONDecodeError as e:
            logger.warning(f"Groq returned non-JSON response: {e}")
            # Try to extract partial JSON
            return self._create_fallback_result(content, "general")
        except Exception as e:
            logger.error(f"Groq analysis error: {e}")
            return self._create_fallback_result(content, "general")

    async def _analyze_with_openai(self, content: str) -> AIProcessingResult:
        """Fallback analysis using OpenAI."""
        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a document intelligence system. Respond only with valid JSON."},
                    {"role": "user", "content": f"Extract all structured data from this document:\n{content[:3000]}\n\nReturn JSON with: document_type, summary, key_insights (list), extracted_entities (dict), recommendations (list)"}
                ],
                temperature=0.1,
                max_tokens=2000
            )
            result = response.choices[0].message.content
            ai_data = json.loads(result)
            return AIProcessingResult(
                document_type=ai_data.get("document_type", "general"),
                summary=ai_data.get("summary", ""),
                key_insights=ai_data.get("key_insights", []),
                extracted_entities=ai_data.get("extracted_entities", {}),
                recommendations=ai_data.get("recommendations", []),
                confidence_score=0.85,
                processing_steps=["OCR extraction", "OpenAI gpt-3.5-turbo analysis"]
            )
        except Exception as e:
            logger.error(f"OpenAI analysis error: {e}")
            return self._create_fallback_result(content, "general")
    
    def _extract_text_content(self, ocr_result: Dict[str, Any]) -> str:
        """Extract text content from OCR result"""
        chunks = ocr_result.get("chunks", [])
        text_parts = []
        
        for chunk in chunks:
            text = chunk.get("text", "").strip()
            if text:
                text_parts.append(text)
        
        return " ".join(text_parts)
    
    async def _detect_document_type(self, content: str) -> DocumentType:
        """Detect document type using AI"""
        try:
            if not LANGCHAIN_AVAILABLE or not self.langchain_llm:
                return DocumentType.GENERAL
            
            # Create prompt for document type detection
            prompt_template = PromptTemplate(
                input_variables=["content"],
                template="""
                Analyze the following document content and determine the document type.
                
                Content: {content}
                
                Possible types:
                - invoice: Contains invoice numbers, line items, totals, payment terms
                - receipt: Contains purchase details, items, amounts, dates
                - contract: Contains legal terms, signatures, obligations
                - report: Contains analysis, findings, recommendations
                - form: Contains fields to be filled, structured data
                - table: Contains tabular data with rows and columns
                - general: None of the above or mixed content
                
                Respond with only the document type (one word).
                """
            )
            
            chain = LLMChain(llm=self.langchain_llm, prompt=prompt_template)
            result = await chain.arun(content=content[:2000])  # Limit content length
            
            # Map result to enum
            result_lower = result.lower().strip()
            if "invoice" in result_lower:
                return DocumentType.INVOICE
            elif "receipt" in result_lower:
                return DocumentType.RECEIPT
            elif "contract" in result_lower:
                return DocumentType.CONTRACT
            elif "report" in result_lower:
                return DocumentType.REPORT
            elif "form" in result_lower:
                return DocumentType.FORM
            elif "table" in result_lower:
                return DocumentType.TABLE
            else:
                return DocumentType.GENERAL
                
        except Exception as e:
            logger.error(f"Error detecting document type: {e}")
            return DocumentType.GENERAL
    
    async def _analyze_invoice(self, content: str, ocr_result: Dict[str, Any]) -> AIProcessingResult:
        """Analyze invoice document"""
        try:
            if not self.langchain_llm or not LANGCHAIN_AVAILABLE:
                logger.warning("LangChain not available, using fallback analysis")
                return self._create_fallback_result(content, "invoice")
            
            from langchain_core.prompts import PromptTemplate
            
            prompt_template = PromptTemplate(
                input_variables=["content"],
                template="""
                You are an expert invoice analyst with deep knowledge of medical, commercial, and service invoices. 
                Analyze the following invoice content and extract ALL information in a structured format suitable for Excel export.
                
                Focus on extracting:
                1. Invoice header information
                2. Complete line items table with ALL columns
                3. Totals and calculations
                4. Payment and billing details
                
                Content: {content}
                
                Provide response in JSON format with detailed table extraction:
                {{
                    "summary": "brief summary of the invoice purpose and total amount",
                    "key_insights": ["insight1", "insight2", "anomaly1", "pattern1"],
                    "extracted_entities": {{
                        "invoice_number": "exact invoice number",
                        "invoice_date": "YYYY-MM-DD format",
                        "due_date": "YYYY-MM-DD format or null",
                        "vendor_name": "company name",
                        "vendor_address": "complete address",
                        "vendor_phone": "phone number",
                        "vendor_email": "email if available",
                        "billing_address": "billing address",
                        "shipping_address": "shipping address if different",
                        "customer_name": "customer/bill to name",
                        "customer_account": "account number",
                        "purchase_order": "PO number if available",
                        "subtotal": "numeric subtotal",
                        "tax_amount": "tax amount",
                        "total_amount": "final total amount",
                        "payment_terms": "payment terms description",
                        "currency": "USD, EUR, etc.",
                        "line_items": [
                            {{
                                "item_number": "line number or SKU",
                                "description": "full item description with all details",
                                "quantity": "numeric quantity",
                                "unit_price": "price per unit",
                                "total_price": "quantity * unit_price",
                                "cpt_code": "CPT/HCPCS code if medical invoice",
                                "service_code": "service code if available",
                                "diagnosis_code": "ICD-10 code if medical invoice",
                                "modifier": "procedure modifier if medical",
                                "units": "units of service (e.g., hours, visits, units)",
                                "date_of_service": "YYYY-MM-DD if specified",
                                "category": "item category or classification",
                                "taxable": "true/false if taxable",
                                "discount": "discount amount if any"
                            }}
                        ]
                    }},
                    "recommendations": ["rec1", "rec2", "validation_check1", "potential_issue1"]
                }}
                
                IMPORTANT:
                - Extract ALL line items with complete information
                - For medical invoices, include CPT/HCPCS codes, diagnosis codes, modifiers
                - For commercial invoices, include SKUs, product codes, descriptions
                - Maintain exact numeric values for calculations
                - Preserve dates in YYYY-MM-DD format
                - Extract ALL visible columns from the invoice table
                - If information is not present, use null or empty string
                - Ensure line_items array contains ALL items from the invoice
                """
            )
            
            # Simple prompt execution without LangChain chains
            prompt = prompt_template.format(content=content[:2000])  # Limit content length
            
            # Use OpenAI directly
            if self.openai_client:
                response = await self.openai_client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": "You are an expert invoice analyst. Respond only with valid JSON."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.1
                )
                result = response.choices[0].message.content
            else:
                logger.warning("OpenAI client not available, using fallback")
                return self._create_fallback_result(content, "invoice")
            
            # Parse JSON result
            try:
                ai_analysis = json.loads(result)
                return AIProcessingResult(
                    document_type="invoice",
                    summary=ai_analysis.get("summary", ""),
                    key_insights=ai_analysis.get("key_insights", []),
                    extracted_entities=ai_analysis.get("extracted_entities", {}),
                    recommendations=ai_analysis.get("recommendations", []),
                    confidence_score=0.85,
                    processing_steps=["OCR extraction", "Document type detection", "Invoice analysis"]
                )
            except json.JSONDecodeError:
                logger.warning("Failed to parse AI analysis JSON")
                return self._create_fallback_result(content, "invoice")
                
        except Exception as e:
            logger.error(f"Error analyzing invoice: {e}")
            return self._create_fallback_result(content, "invoice")
    
    async def _analyze_contract(self, content: str, ocr_result: Dict[str, Any]) -> AIProcessingResult:
        """Analyze contract document"""
        try:
            if not LANGCHAIN_AVAILABLE or not self.langchain_llm:
                return self._create_fallback_result(content, "contract")
            
            prompt_template = PromptTemplate(
                input_variables=["content"],
                template="""
                You are a legal document expert. Analyze the following contract content and provide:
                
                1. A concise summary of the contract
                2. Key insights (important clauses, obligations, risks)
                3. Extracted entities (parties, effective date, term, key clauses)
                4. Recommendations (what to review, potential issues)
                
                Content: {content}
                
                Provide response in JSON format:
                {{
                    "summary": "brief summary",
                    "key_insights": ["insight1", "insight2"],
                    "extracted_entities": {{
                        "parties": [],
                        "effective_date": "",
                        "term": "",
                        "key_clauses": []
                    }},
                    "recommendations": ["rec1", "rec2"]
                }}
                """
            )
            
            chain = LLMChain(llm=self.langchain_llm, prompt=prompt_template)
            result = await chain.arun(content=content)
            
            try:
                ai_analysis = json.loads(result)
                return AIProcessingResult(
                    document_type="contract",
                    summary=ai_analysis.get("summary", ""),
                    key_insights=ai_analysis.get("key_insights", []),
                    extracted_entities=ai_analysis.get("extracted_entities", {}),
                    recommendations=ai_analysis.get("recommendations", []),
                    confidence_score=0.80,
                    processing_steps=["OCR extraction", "Document type detection", "Contract analysis"]
                )
            except json.JSONDecodeError:
                return self._create_fallback_result(content, "contract")
                
        except Exception as e:
            logger.error(f"Error analyzing contract: {e}")
            return self._create_fallback_result(content, "contract")
    
    async def _analyze_report(self, content: str, ocr_result: Dict[str, Any]) -> AIProcessingResult:
        """Analyze report document"""
        try:
            if not LANGCHAIN_AVAILABLE or not self.langchain_llm:
                return self._create_fallback_result(content, "report")
            
            prompt_template = PromptTemplate(
                input_variables=["content"],
                template="""
                You are an expert report analyst. Analyze the following report content and provide:
                
                1. A concise summary of the report
                2. Key insights (findings, trends, important data)
                3. Extracted entities (report title, date, key metrics, conclusions)
                4. Recommendations (action items, further analysis needed)
                
                Content: {content}
                
                Provide response in JSON format:
                {{
                    "summary": "brief summary",
                    "key_insights": ["insight1", "insight2"],
                    "extracted_entities": {{
                        "report_title": "",
                        "date": "",
                        "key_metrics": [],
                        "conclusions": []
                    }},
                    "recommendations": ["rec1", "rec2"]
                }}
                """
            )
            
            chain = LLMChain(llm=self.langchain_llm, prompt=prompt_template)
            result = await chain.arun(content=content)
            
            try:
                ai_analysis = json.loads(result)
                return AIProcessingResult(
                    document_type="report",
                    summary=ai_analysis.get("summary", ""),
                    key_insights=ai_analysis.get("key_insights", []),
                    extracted_entities=ai_analysis.get("extracted_entities", {}),
                    recommendations=ai_analysis.get("recommendations", []),
                    confidence_score=0.75,
                    processing_steps=["OCR extraction", "Document type detection", "Report analysis"]
                )
            except json.JSONDecodeError:
                return self._create_fallback_result(content, "report")
                
        except Exception as e:
            logger.error(f"Error analyzing report: {e}")
            return self._create_fallback_result(content, "report")
    
    async def _analyze_form(self, content: str, ocr_result: Dict[str, Any]) -> AIProcessingResult:
        """Analyze form document"""
        try:
            if not LANGCHAIN_AVAILABLE or not self.langchain_llm:
                return self._create_fallback_result(content, "form")
            
            prompt_template = PromptTemplate(
                input_variables=["content"],
                template="""
                You are an expert form analyst. Analyze the following form content and provide:
                
                1. A concise summary of the form
                2. Key insights (form type, required fields, completion status)
                3. Extracted entities (form title, fields, dates, signatures)
                4. Recommendations (what to complete, what to verify)
                
                Content: {content}
                
                Provide response in JSON format:
                {{
                    "summary": "brief summary",
                    "key_insights": ["insight1", "insight2"],
                    "extracted_entities": {{
                        "form_title": "",
                        "fields": [],
                        "dates": [],
                        "signatures": []
                    }},
                    "recommendations": ["rec1", "rec2"]
                }}
                """
            )
            
            chain = LLMChain(llm=self.langchain_llm, prompt=prompt_template)
            result = await chain.arun(content=content)
            
            try:
                ai_analysis = json.loads(result)
                return AIProcessingResult(
                    document_type="form",
                    summary=ai_analysis.get("summary", ""),
                    key_insights=ai_analysis.get("key_insights", []),
                    extracted_entities=ai_analysis.get("extracted_entities", {}),
                    recommendations=ai_analysis.get("recommendations", []),
                    confidence_score=0.70,
                    processing_steps=["OCR extraction", "Document type detection", "Form analysis"]
                )
            except json.JSONDecodeError:
                return self._create_fallback_result(content, "form")
                
        except Exception as e:
            logger.error(f"Error analyzing form: {e}")
            return self._create_fallback_result(content, "form")
    
    async def _analyze_table(self, content: str, ocr_result: Dict[str, Any]) -> AIProcessingResult:
        """Analyze table document"""
        try:
            if not LANGCHAIN_AVAILABLE or not self.langchain_llm:
                return self._create_fallback_result(content, "table")
            
            prompt_template = PromptTemplate(
                input_variables=["content"],
                template="""
                You are an expert table analyst. Analyze the following table content and provide:
                
                1. A concise summary of the table
                2. Key insights (patterns, totals, important data points)
                3. Extracted entities (table title, headers, row count, key values)
                4. Recommendations (data quality issues, further analysis)
                
                Content: {content}
                
                Provide response in JSON format:
                {{
                    "summary": "brief summary",
                    "key_insights": ["insight1", "insight2"],
                    "extracted_entities": {{
                        "table_title": "",
                        "headers": [],
                        "row_count": 0,
                        "key_values": []
                    }},
                    "recommendations": ["rec1", "rec2"]
                }}
                """
            )
            
            chain = LLMChain(llm=self.langchain_llm, prompt=prompt_template)
            result = await chain.arun(content=content)
            
            try:
                ai_analysis = json.loads(result)
                return AIProcessingResult(
                    document_type="table",
                    summary=ai_analysis.get("summary", ""),
                    key_insights=ai_analysis.get("key_insights", []),
                    extracted_entities=ai_analysis.get("extracted_entities", {}),
                    recommendations=ai_analysis.get("recommendations", []),
                    confidence_score=0.90,
                    processing_steps=["OCR extraction", "Document type detection", "Table analysis"]
                )
            except json.JSONDecodeError:
                return self._create_fallback_result(content, "table")
                
        except Exception as e:
            logger.error(f"Error analyzing table: {e}")
            return self._create_fallback_result(content, "table")
    
    async def _analyze_general(self, content: str, ocr_result: Dict[str, Any]) -> AIProcessingResult:
        """Analyze general document"""
        try:
            if not LANGCHAIN_AVAILABLE or not self.langchain_llm:
                return self._create_fallback_result(content, "general")
            
            prompt_template = PromptTemplate(
                input_variables=["content"],
                template="""
                You are an expert document analyst. Analyze the following document content and provide:
                
                1. A concise summary of the document
                2. Key insights (important information, patterns, key points)
                3. Extracted entities (names, dates, amounts, locations, organizations)
                4. Recommendations (what to do next, what to verify)
                
                Content: {content}
                
                Provide response in JSON format:
                {{
                    "summary": "brief summary",
                    "key_insights": ["insight1", "insight2"],
                    "extracted_entities": {{
                        "names": [],
                        "dates": [],
                        "amounts": [],
                        "locations": [],
                        "organizations": []
                    }},
                    "recommendations": ["rec1", "rec2"]
                }}
                """
            )
            
            chain = LLMChain(llm=self.langchain_llm, prompt=prompt_template)
            result = await chain.arun(content=content)
            
            try:
                ai_analysis = json.loads(result)
                return AIProcessingResult(
                    document_type="general",
                    summary=ai_analysis.get("summary", ""),
                    key_insights=ai_analysis.get("key_insights", []),
                    extracted_entities=ai_analysis.get("extracted_entities", {}),
                    recommendations=ai_analysis.get("recommendations", []),
                    confidence_score=0.60,
                    processing_steps=["OCR extraction", "Document type detection", "General analysis"]
                )
            except json.JSONDecodeError:
                return self._create_fallback_result(content, "general")
                
        except Exception as e:
            logger.error(f"Error analyzing general document: {e}")
            return self._create_fallback_result(content, "general")
    
    def _create_enhanced_extraction_schema(self, document_type: str) -> dict:
        """Create enhanced JSON schema for structured data extraction (inspired by L8 notebook)"""
        
        if document_type.lower() in ["invoice", "bill", "utility"]:
            return {
                "type": "object",
                "title": "Enhanced Invoice/Utility Bill Extraction Schema",
                "properties": {
                    "account_summary": {
                        "type": "object",
                        "title": "Account Summary",
                        "properties": {
                            "account_number": {
                                "type": "string",
                                "description": "The account number for the service"
                            },
                            "current_charges": {
                                "type": "number",
                                "description": "The charges incurred during the current billing period"
                            },
                            "total_amount_due": {
                                "type": "number",
                                "description": "The total amount currently due"
                            },
                            "billing_period": {
                                "type": "string",
                                "description": "The billing period dates"
                            },
                            "due_date": {
                                "type": "string",
                                "description": "The payment due date"
                            }
                        }
                    },
                    "service_details": {
                        "type": "object",
                        "title": "Service Usage Details",
                        "properties": {
                            "gas_usage": {
                                "type": "object",
                                "properties": {
                                    "total_therms_used": {
                                        "type": "number",
                                        "description": "Total therms of gas used in the billing period"
                                    },
                                    "gas_current_charges": {
                                        "type": "number",
                                        "description": "The gas charges incurred during the current billing period"
                                    },
                                    "gas_usage_chart": {
                                        "type": "boolean",
                                        "description": "Does the document contain a chart of historical gas usage?"
                                    },
                                    "gas_max_month": {
                                        "type": "string",
                                        "description": "Which month has the highest historical gas usage? Return month name only"
                                    }
                                }
                            },
                            "electric_usage": {
                                "type": "object",
                                "properties": {
                                    "total_kwh_used": {
                                        "type": "number",
                                        "description": "Total kilowatt hours of electricity used in the billing period"
                                    },
                                    "electric_current_charges": {
                                        "type": "number",
                                        "description": "The electric charges incurred during the current billing period"
                                    },
                                    "electric_usage_chart": {
                                        "type": "boolean",
                                        "description": "Does the document contain a chart of historical electric usage?"
                                    },
                                    "electric_max_month": {
                                        "type": "string",
                                        "description": "Which month has the highest historical electric usage? Return month name only"
                                    }
                                }
                            }
                        }
                    },
                    "line_items": {
                        "type": "array",
                        "title": "Invoice Line Items",
                        "items": {
                            "type": "object",
                            "properties": {
                                "item_number": {
                                    "type": "string",
                                    "description": "Line item number or identifier"
                                },
                                "description": {
                                    "type": "string",
                                    "description": "Description of the product or service"
                                },
                                "quantity": {
                                    "type": "number",
                                    "description": "Quantity of the item"
                                },
                                "unit_price": {
                                    "type": "number",
                                    "description": "Price per unit"
                                },
                                "total_price": {
                                    "type": "number",
                                    "description": "Total price for this line item"
                                },
                                "cpt_code": {
                                    "type": "string",
                                    "description": "CPT code for medical services"
                                },
                                "diagnosis_code": {
                                    "type": "string",
                                    "description": "Diagnosis code for medical services"
                                },
                                "modifiers": {
                                    "type": "array",
                                    "items": {"type": "string"},
                                    "description": "Any modifiers applied to this line item"
                                }
                            }
                        }
                    }
                }
            }
        
        elif document_type.lower() in ["financial", "statement", "report"]:
            return {
                "type": "object",
                "title": "Financial Document Extraction Schema",
                "properties": {
                    "financial_summary": {
                        "type": "object",
                        "properties": {
                            "total_revenue": {
                                "type": "number",
                                "description": "Total revenue amount"
                            },
                            "total_expenses": {
                                "type": "number",
                                "description": "Total expenses amount"
                            },
                            "net_income": {
                                "type": "number",
                                "description": "Net income or profit"
                            },
                            "period": {
                                "type": "string",
                                "description": "Financial period covered"
                            }
                        }
                    },
                    "key_metrics": {
                        "type": "object",
                        "properties": {
                            "growth_rate": {
                                "type": "number",
                                "description": "Growth rate percentage"
                            },
                            "profit_margin": {
                                "type": "number",
                                "description": "Profit margin percentage"
                            },
                            "market_cap": {
                                "type": "number",
                                "description": "Market capitalization"
                            }
                        }
                    }
                }
            }
        
        else:
            # Default schema for general documents
            return {
                "type": "object",
                "title": "General Document Extraction Schema",
                "properties": {
                    "document_title": {
                        "type": "string",
                        "description": "The main title or subject of the document"
                    },
                    "key_entities": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "entity_name": {
                                    "type": "string",
                                    "description": "Name of the entity"
                                },
                                "entity_type": {
                                    "type": "string",
                                    "description": "Type of entity (person, organization, location, etc.)"
                                },
                                "context": {
                                    "type": "string",
                                    "description": "Context or role of the entity in the document"
                                }
                            }
                        }
                    },
                    "key_dates": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "date": {
                                    "type": "string",
                                    "description": "The date mentioned"
                                },
                                "date_type": {
                                    "type": "string",
                                    "description": "Type of date (created, due, signed, etc.)"
                                },
                                "context": {
                                    "type": "string",
                                    "description": "Context of the date in the document"
                                }
                            }
                        }
                    },
                    "financial_amounts": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "amount": {
                                    "type": "number",
                                    "description": "The monetary amount"
                                },
                                "currency": {
                                    "type": "string",
                                    "description": "Currency code (USD, EUR, etc.)"
                                },
                                "context": {
                                    "type": "string",
                                    "description": "What this amount represents"
                                }
                            }
                        }
                    }
                }
            }
    
    def _create_fallback_result(self, content: str, document_type: str) -> AIProcessingResult:
        """Create a fallback result when AI analysis fails"""
        doc_type = document_type if document_type else "unknown"
        
        return AIProcessingResult(
            document_type=doc_type,
            summary=f"Document processed with {len(content)} characters of text content",
            key_insights=["Document contains text content", "OCR extraction completed"],
            extracted_entities={"content_length": len(content)},
            recommendations=["Review extracted content for accuracy"],
            confidence_score=0.50,
            processing_steps=["OCR extraction", "Basic processing"]
        )

# Global AI agent service instance
ai_agent_service = AIAgentService()
