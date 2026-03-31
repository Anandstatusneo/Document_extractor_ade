"""
Multi-Agent Document Extraction Service
========================================
Five specialist agents + one Orchestrator. Each agent has a focused role
and records a structured AgentStep trace for full pipeline visibility.

Pipeline
--------
OCR text
  └─► Orchestrator
        ├─► ClassifierAgent      (doc type + domain)
        ├─► OCRQualityAgent      (quality score, low-conf zones)
        │
        └─► [after classifier] ──────────────────────────────────┐
              ├─► FieldExtractorAgent  (key-value pairs)         │
              └─► TableExtractorAgent (tables, CPT codes)        │
                                                                  │
                    └─► ValidatorAgent (cross-check all)  ◄──────┘
                          └─► Aggregator (merge → final JSON)
"""

import logging
import json
import asyncio
import time
import re
from dataclasses import dataclass, field, asdict
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)

try:
    from langchain_groq import ChatGroq
    GROQ_AVAILABLE = True
except ImportError:
    GROQ_AVAILABLE = False

from core.config import settings

# ─────────────────────────────────────────────────────────────────────────────
# Data models
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class AgentStep:
    """Trace record for one agent in the pipeline."""
    agent_name:     str
    role:           str
    status:         str          # "success" | "error" | "skipped"
    confidence:     float        # 0.0 – 1.0
    duration_ms:    int
    output_summary: str
    output:         Dict[str, Any] = field(default_factory=dict)
    error:          Optional[str]  = None


@dataclass
class MultiAgentResult:
    """Final aggregated output from the multi-agent pipeline."""
    document_type:     str
    domain:            str           # medical | legal | financial | general
    summary:           str
    key_insights:      List[str]
    extracted_fields:  List[Dict]    # [{field, value, category, confidence}]
    tables:            List[Dict]    # [{title, headers, rows}]
    validation_flags:  List[str]     # anomalies / warnings
    recommendations:   List[str]
    overall_confidence: float
    agent_trace:       List[AgentStep]
    processing_steps:  List[str]


# ─────────────────────────────────────────────────────────────────────────────
# Helper
# ─────────────────────────────────────────────────────────────────────────────

def _parse_json(text: str) -> Dict:
    """Strip markdown fences then parse JSON."""
    text = text.strip()
    # Remove ```json ... ``` or ``` ... ```
    text = re.sub(r'^```(?:json)?\s*', '', text, flags=re.MULTILINE)
    text = re.sub(r'\s*```$', '', text, flags=re.MULTILINE)
    text = text.strip()
    return json.loads(text)


async def _call_llm_with_fallback(orchestrator, prompt: str, agent_name: str) -> tuple[str, str]:
    """Invoke LLM with fallback from 70b to 8b on 429 Rate Limit."""
    try:
        # Try primary 70b first
        resp = await orchestrator.llm.ainvoke(prompt)
        return resp.content if hasattr(resp, "content") else str(resp), "llama-3.3-70b"
    except Exception as e:
        if "rate_limit_exceeded" in str(e).lower() or "429" in str(e):
            logger.warning(f"Rate limit for 70b on {agent_name}. Falling back to 8b.")
            if orchestrator.llm_fallback:
                try:
                    resp = await orchestrator.llm_fallback.ainvoke(prompt)
                    return resp.content if hasattr(resp, "content") else str(resp), "llama-3.1-8b"
                except Exception as fe:
                    logger.error(f"Fallback 8b also failed: {fe}")
                    raise fe
        raise e


def _sample_content(content: str, max_chars: int = 8_000) -> str:
    """Sample multi-page content keeping ≤1500 chars per page to stay under limits."""
    CHARS_PP = 1_500
    blocks = re.split(r'\n=== PAGE \d+ ===\n', content)
    if len(blocks) > 1:
        blocks = [b for b in blocks if b.strip()]
        # Proportional clipping
        per_page = max(500, max_chars // len(blocks))
        return "\n\n---\n\n".join(b[:min(per_page, CHARS_PP)] for b in blocks)[:max_chars]
    return content[:max_chars]


# ─────────────────────────────────────────────────────────────────────────────
# Agents
# ─────────────────────────────────────────────────────────────────────────────

class ClassifierAgent:
    NAME = "Classifier Agent"
    ROLE = "Detects document type and domain from text"
    def get_prompt(self, content: str) -> str:
        return f"Classify doc: {content[:2000]}. JSON ONLY: {{\"document_type\":\"invoice|prescription|...\",\"domain\":\"medical|...\",\"confidence\":0.9}}"

class OCRQualityAgent:
    NAME = "OCR Quality Agent"
    ROLE = "Scores OCR quality and flags low-confidence zones"
    def get_prompt(self, content: str) -> str:
        return f"Rate OCR quality (0-1): {content[:1500]}. JSON ONLY: {{\"quality_score\":0.9,\"error_zones\":[]}}"

class FieldExtractorAgent:
    NAME = "Field Extractor Agent"
    ROLE = "Extracts all key-value fields grouped by section"
    def get_prompt(self, content: str, doc_type: str, domain: str) -> str:
        sampled = _sample_content(content, 6000)
        return f"Extract fields from {doc_type} ({domain}): {sampled}. JSON ONLY: {{\"sections\":[],\"all_fields_flat\":[{{\"field\":\"\",\"value\":\"\",\"confidence\":0.9}}]}}"

class TableExtractorAgent:
    NAME = "Table Extractor Agent"
    ROLE = "Parses tables and line-items"
    def get_prompt(self, content: str, doc_type: str) -> str:
        sampled = _sample_content(content, 6000)
        return f"Extract tables from {doc_type}: {sampled}. JSON ONLY: {{\"tables\":[{{\"title\":\"\",\"headers\":[],\"rows\":[]}}],\"table_count\":1}}"

class ValidatorAgent:
    NAME = "Validator Agent"
    ROLE = "Cross-validates extracted fields"
    def get_prompt(self, fields_output: Dict, tables_output: Dict, doc_type: str) -> str:
        compact = {"f": (fields_output.get("all_fields_flat") or [])[:20], "t": (tables_output.get("tables") or [])[:3]}
        return f"Validate {doc_type} data: {json.dumps(compact)}. JSON ONLY: {{\"is_valid\":true,\"confidence\":0.9,\"validation_flags\":[]}}"


# ─────────────────────────────────────────────────────────────────────────────
# Orchestrator
# ─────────────────────────────────────────────────────────────────────────────

class OrchestratorAgent:
    """Coordinates all agents and aggregates their output into a final result."""

    NAME = "Orchestrator Agent"

    def __init__(self):
        self.llm: Optional[ChatGroq] = None
        self.llm_fallback: Optional[ChatGroq] = None
        self._init_llm()

    def _init_llm(self):
        if GROQ_AVAILABLE and settings.GROQ_API_KEY:
            try:
                # Primary 70b - High quality
                self.llm = ChatGroq(
                    api_key=settings.GROQ_API_KEY,
                    model_name="llama-3.3-70b-versatile",
                    temperature=0.05,
                    max_tokens=2048,
                )
                # Fallback 8b - Instant / High Volume Free Tier
                self.llm_fallback = ChatGroq(
                    api_key=settings.GROQ_API_KEY,
                    model_name="llama-3.1-8b-instant",
                    temperature=0.0,
                    max_tokens=1024,
                )
                logger.info("Multi-agent orchestrator: Groq 70b & 8b ready")
            except Exception as e:
                logger.warning(f"Orchestrator LLM init failed: {e}")
                self.llm = None
        else:
            logger.warning("Orchestrator: GROQ_API_KEY not set")

    async def run_agent(self, agent, *args) -> AgentStep:
        """Helper to run an agent with model info captured."""
        t0 = time.time()
        try:
            # We pass 'self' instead of just 'llm' to allow fallback inside the agent call helper
            # But the agents expect 'llm' as first arg in their run method. 
            # Let's adjust agents to use a helper that handles orchestrator self.
            pass # See below for individual agent adjustments
        except: pass

    async def run(self, content: str) -> MultiAgentResult:
        """Run full multi-agent pipeline and return structured result."""
        if not self.llm:
            return self._fallback_result(content)

        trace: List[AgentStep] = []
        t_start = time.time()

        # ── Stage 1: Classify + OCR quality (concurrent) ──────────────────
        cls_agent = ClassifierAgent()
        qa_agent  = OCRQualityAgent()
        
        # We'll use a local helper to run agents with the fallback logic
        async def run_cls():
            t0 = time.time()
            prompt = cls_agent.get_prompt(content)
            try:
                raw, model = await _call_llm_with_fallback(self, prompt, cls_agent.NAME)
                data = _parse_json(raw)
                return AgentStep(
                    agent_name=cls_agent.NAME, role=cls_agent.ROLE, status="success",
                    confidence=float(data.get("confidence", 0.85)),
                    duration_ms=int((time.time()-t0)*1000),
                    output_summary=f"[{model}] Type: {data.get('document_type')} ({data.get('domain')})",
                    output=data
                )
            except Exception as e:
                return AgentStep(agent_name=cls_agent.NAME, role=cls_agent.ROLE, status="error", confidence=0, duration_ms=int((time.time()-t0)*1000), output_summary="Failed", output={}, error=str(e))

        async def run_qa():
            t0 = time.time()
            prompt = qa_agent.get_prompt(content)
            try:
                raw, model = await _call_llm_with_fallback(self, prompt, qa_agent.NAME)
                data = _parse_json(raw)
                score = float(data.get("quality_score", 0.8))
                return AgentStep(
                    agent_name=qa_agent.NAME, role=qa_agent.ROLE, status="success",
                    confidence=score, duration_ms=int((time.time()-t0)*1000),
                    output_summary=f"[{model}] Quality: {score:.0%}",
                    output=data
                )
            except Exception as e:
                return AgentStep(agent_name=qa_agent.NAME, role=qa_agent.ROLE, status="error", confidence=0, duration_ms=int((time.time()-t0)*1000), output_summary="Failed", output={}, error=str(e))

        cls_step, qa_step = await asyncio.gather(run_cls(), run_qa())
        trace.extend([cls_step, qa_step])

        doc_type = cls_step.output.get("document_type", "general")
        domain   = cls_step.output.get("domain", "general")

        # ── Stage 2: Field + Table extraction ─────────────────────────────
        f_agent = FieldExtractorAgent()
        t_agent = TableExtractorAgent()

        async def run_fields():
            t0 = time.time()
            prompt = f_agent.get_prompt(content, doc_type, domain)
            try:
                raw, model = await _call_llm_with_fallback(self, prompt, f_agent.NAME)
                data = _parse_json(raw)
                flat = data.get("all_fields_flat", [])
                avg_conf = sum(f.get("confidence", 0.8) for f in flat) / len(flat) if flat else 0.8
                return AgentStep(
                    agent_name=f_agent.NAME, role=f_agent.ROLE, status="success",
                    confidence=round(avg_conf, 2), duration_ms=int((time.time()-t0)*1000),
                    output_summary=f"[{model}] Fields: {len(flat)}",
                    output=data
                )
            except Exception as e:
                return AgentStep(agent_name=f_agent.NAME, role=f_agent.ROLE, status="error", confidence=0, duration_ms=int((time.time()-t0)*1000), output_summary="Failed", output={}, error=str(e))

        async def run_tables():
            t0 = time.time()
            prompt = t_agent.get_prompt(content, doc_type)
            try:
                raw, model = await _call_llm_with_fallback(self, prompt, t_agent.NAME)
                data = _parse_json(raw)
                n = data.get("table_count", len(data.get("tables", [])))
                return AgentStep(
                    agent_name=t_agent.NAME, role=t_agent.ROLE, status="success",
                    confidence=0.9 if n > 0 else 0.5, duration_ms=int((time.time()-t0)*1000),
                    output_summary=f"[{model}] Tables: {n}",
                    output=data
                )
            except Exception as e:
                return AgentStep(agent_name=t_agent.NAME, role=t_agent.ROLE, status="error", confidence=0, duration_ms=int((time.time()-t0)*1000), output_summary="Failed", output={}, error=str(e))

        field_step, table_step = await asyncio.gather(run_fields(), run_tables())
        trace.extend([field_step, table_step])

        # ── Stage 3: Validation ───────────────────────────────────────────
        v_agent = ValidatorAgent()
        async def run_val():
            t0 = time.time()
            prompt = v_agent.get_prompt(field_step.output, table_step.output, doc_type)
            try:
                raw, model = await _call_llm_with_fallback(self, prompt, v_agent.NAME)
                data = _parse_json(raw)
                return AgentStep(
                    agent_name=v_agent.NAME, role=v_agent.ROLE, status="success",
                    confidence=float(data.get("confidence", 0.9)),
                    duration_ms=int((time.time()-t0)*1000),
                    output_summary=f"[{model}] Flags: {len(data.get('validation_flags', []))}",
                    output=data
                )
            except Exception as e:
                return AgentStep(agent_name=v_agent.NAME, role=v_agent.ROLE, status="error", confidence=0, duration_ms=int((time.time()-t0)*1000), output_summary="Failed", output={}, error=str(e))

        val_step = await run_val()
        trace.append(val_step)

        # ── Stage 4: Summary ──────────────────────────────────────────────
        async def run_sum():
            t0 = time.time()
            fields_sample = json.dumps((field_step.output.get("all_fields_flat") or [])[:15], indent=None)
            prompt = f"Summarize {doc_type} ({domain}). Info: {fields_sample[:1000]}. JSON ONLY: {{\"summary\":\"...\",\"key_insights\":[],\"recommendations\":[]}}"
            try:
                raw, model = await _call_llm_with_fallback(self, prompt, "Summary Agent")
                data = _parse_json(raw)
                return AgentStep(
                    agent_name="Summary Agent", role="Insights", status="success",
                    confidence=0.9, duration_ms=int((time.time()-t0)*1000),
                    output_summary=f"[{model}] Summary generated",
                    output=data
                )
            except Exception as e:
                return AgentStep(agent_name="Summary Agent", role="Insights", status="error", confidence=0, duration_ms=int((time.time()-t0)*1000), output_summary="Failed", output={}, error=str(e))

        summary_step = await run_sum()
        trace.append(summary_step)

        # Final Aggregation (Same as before but using ma_result logic)
        return self._build_final_result(trace, cls_step, field_step, table_step, val_step, summary_step, t_start)

    def _build_final_result(self, trace, cls_step, field_step, table_step, val_step, summary_step, t_start) -> MultiAgentResult:
        all_fields    = field_step.output.get("all_fields_flat", [])
        tables        = table_step.output.get("tables", [])
        val_flags     = val_step.output.get("validation_flags", []) + val_step.output.get("critical_issues", [])
        insights      = summary_step.output.get("key_insights", [])
        recommendations = summary_step.output.get("recommendations", [])
        summary_text  = summary_step.output.get("summary", "")

        conf_values = [s.confidence for s in trace if s.status == "success" and s.confidence > 0]
        overall_conf = round(sum(conf_values) / len(conf_values), 3) if conf_values else 0.75

        return MultiAgentResult(
            document_type=cls_step.output.get("document_type", "general"),
            domain=cls_step.output.get("domain", "general"),
            summary=summary_text,
            key_insights=insights,
            extracted_fields=all_fields,
            tables=tables,
            validation_flags=val_flags,
            recommendations=recommendations,
            overall_confidence=overall_conf,
            agent_trace=trace,
            processing_steps=[s.agent_name for s in trace],
        )

    def _fallback_result(self, content: str) -> MultiAgentResult:
        return MultiAgentResult(
            document_type="general", domain="general",
            summary="Multi-agent pipeline unavailable.",
            key_insights=[], extracted_fields=[], tables=[], validation_flags=["LLM error"],
            recommendations=[], overall_confidence=0.0, agent_trace=[], processing_steps=[],
        )


# ─────────────────────────────────────────────────────────────────────────────
# Module-level singleton
# ─────────────────────────────────────────────────────────────────────────────

multi_agent_service = OrchestratorAgent()
