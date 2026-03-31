import { useState } from 'react'
import './ResultsPage.css'

const TABS = [
    { id: 'pipeline', label: '🤖 Agent Pipeline' },
    { id: 'ai', label: '📋 AI Analysis' },
    { id: 'text', label: '📝 Extracted Text' },
    { id: 'tables', label: '📊 Tables' },
    { id: 'json', label: '{ } Raw JSON' },
    { id: 'export', label: '⬇️ Export' },
]

function confBadge(v) {
    const n = parseFloat(v)
    if (isNaN(n)) return { label: '—', cls: '' }
    if (n >= 0.85) return { label: `🟢 ${Math.round(n * 100)}%`, cls: 'high' }
    if (n >= 0.55) return { label: `🟡 ${Math.round(n * 100)}%`, cls: 'med' }
    return { label: `🔴 ${Math.round(n * 100)}%`, cls: 'low' }
}

/* ── PDF Page Viewer ─────────────────────────────────────────────── */
function PdfViewer({ fileName }) {
    const [page, setPage] = useState(0)
    const [count, setCount] = useState(null)
    const [imgSrc, setImgSrc] = useState(null)
    const [loading, setLoading] = useState(false)

    async function loadPage(p) {
        setLoading(true)
        try {
            const res = await fetch(`/api/v1/documents/${encodeURIComponent(fileName)}/pages/${p}`)
            if (res.ok) {
                const blob = await res.blob()
                setImgSrc(URL.createObjectURL(blob))
                setPage(p)
            }
        } finally { setLoading(false) }
    }

    async function init() {
        if (count !== null) return
        try {
            const res = await fetch(`/api/v1/documents/${encodeURIComponent(fileName)}/page_count`)
            const data = await res.json()
            const n = data?.data?.page_count || 1
            setCount(n)
            loadPage(0)
        } catch { setCount(1) }
    }

    if (!imgSrc && count === null) {
        return (
            <div className="pdf-viewer-placeholder" onClick={init}>
                <div className="pdf-placeholder-icon">📄</div>
                <div>Click to load PDF preview</div>
            </div>
        )
    }

    return (
        <div className="pdf-viewer">
            <div className="pdf-nav">
                <button className="pdf-btn" disabled={page <= 0 || loading} onClick={() => loadPage(page - 1)}>‹ Prev</button>
                <span className="pdf-page-label">Page {page + 1}{count ? ` / ${count}` : ''}</span>
                <button className="pdf-btn" disabled={count !== null && page >= count - 1 || loading} onClick={() => loadPage(page + 1)}>Next ›</button>
            </div>
            {loading
                ? <div className="pdf-loading">Loading page…</div>
                : imgSrc && <img src={imgSrc} alt={`Page ${page + 1}`} className="pdf-img" />
            }
        </div>
    )
}

/* ── Agent Pipeline Tab ───────────────────────────────────────────── */
const AGENT_ICONS = {
    'Classifier Agent': '🔍',
    'OCR Quality Agent': '📡',
    'Field Extractor Agent': '📑',
    'Table Extractor Agent': '📊',
    'Validator Agent': '✅',
    'Summary Agent': '💬',
    'Orchestrator Agent': '🎯',
}

function AgentCard({ step, index }) {
    const [open, setOpen] = useState(false)
    const icon = AGENT_ICONS[step.agent_name] || '🤖'
    const cb = confBadge(step.confidence)
    const isErr = step.status === 'error'

    return (
        <div className={`agent-card ${isErr ? 'agent-card-error' : 'agent-card-ok'}`}>
            <div className="agent-card-header" onClick={() => setOpen(!open)}>
                <div className="agent-card-left">
                    <span className="agent-step-num">{index + 1}</span>
                    <span className="agent-icon">{icon}</span>
                    <div>
                        <div className="agent-name">{step.agent_name}</div>
                        <div className="agent-role">{step.role}</div>
                    </div>
                </div>
                <div className="agent-card-right">
                    <span className={`conf-badge conf-${cb.cls}`}>{cb.label}</span>
                    <span className="agent-duration">{step.duration_ms}ms</span>
                    <span className={`agent-status-dot ${isErr ? 'dot-err' : 'dot-ok'}`}>
                        {isErr ? '✗' : '✓'}
                    </span>
                    <span className="chevron">{open ? '▲' : '▼'}</span>
                </div>
            </div>
            <div className="agent-summary">{step.output_summary}</div>
            {isErr && step.error && (
                <div className="agent-error-box">⚠️ {step.error}</div>
            )}
            {open && (
                <pre className="agent-output-json">
                    {JSON.stringify(step.output, null, 2)}
                </pre>
            )}
        </div>
    )
}

function PipelineTab({ ma }) {
    if (!ma) return (
        <div className="empty-state">
            <div style={{ fontSize: '3rem', marginBottom: 12 }}>🤖</div>
            <div style={{ fontWeight: 600, marginBottom: 8 }}>Multi-Agent Pipeline not available</div>
            <div style={{ color: 'var(--slate)', fontSize: '.88rem' }}>
                Ensure GROQ_API_KEY is set and AI analysis is enabled.
            </div>
        </div>
    )

    const trace = ma.agent_trace || []
    const fields = ma.extracted_fields || []
    const tables = ma.tables || []
    const flags = ma.validation_flags || []
    const insights = ma.key_insights || []
    const recs = ma.recommendations || []
    const cb = confBadge(ma.overall_confidence)

    return (
        <div className="pipeline-tab">
            {/* ── Top metrics ── */}
            <div className="ai-metrics">
                <div className="ai-metric">
                    <div className="ai-metric-label">Document Type</div>
                    <div className="ai-metric-value">
                        {ma.document_type?.replace(/_/g, ' ')} <span style={{ color: 'var(--slate)', fontSize: '.8rem' }}>({ma.domain})</span>
                    </div>
                </div>
                <div className="ai-metric">
                    <div className="ai-metric-label">Pipeline Confidence</div>
                    <div className={`ai-metric-value conf-${cb.cls}`}>{cb.label}</div>
                </div>
                <div className="ai-metric">
                    <div className="ai-metric-label">Agents Run</div>
                    <div className="ai-metric-value">{trace.length}</div>
                </div>
                <div className="ai-metric">
                    <div className="ai-metric-label">Fields Extracted</div>
                    <div className="ai-metric-value">{fields.length}</div>
                </div>
                <div className="ai-metric">
                    <div className="ai-metric-label">Tables Found</div>
                    <div className="ai-metric-value">{tables.length}</div>
                </div>
                <div className="ai-metric">
                    <div className="ai-metric-label">Validation Flags</div>
                    <div className={`ai-metric-value ${flags.length > 0 ? 'conf-med' : 'conf-high'}`}>
                        {flags.length > 0 ? `⚠️ ${flags.length}` : '✅ 0'}
                    </div>
                </div>
            </div>

            {/* ── Summary ── */}
            {ma.summary && <div className="summary-box">📝 {ma.summary}</div>}

            <div className="pipeline-two-col">
                {/* ── Left col: agent trace ── */}
                <div className="pipeline-left">
                    <div className="section-title">🔄 Agent Execution Trace</div>
                    <div className="pipeline-trace">
                        {trace.map((step, i) => (
                            <AgentCard key={i} step={step} index={i} />
                        ))}
                    </div>
                </div>

                {/* ── Right col: outputs ── */}
                <div className="pipeline-right">
                    {/* Key insights */}
                    {insights.length > 0 && (
                        <div className="section">
                            <div className="section-title">🔍 Key Insights</div>
                            {insights.map((ins, i) => (
                                <div className="insight-row" key={i}>
                                    <span className="insight-num">{i + 1}</span>{ins}
                                </div>
                            ))}
                        </div>
                    )}

                    {/* Extracted fields */}
                    {fields.length > 0 && (
                        <div className="section">
                            <div className="section-title">🏷️ All Extracted Fields ({fields.length})</div>
                            <div className="table-wrap">
                                <table className="data-table">
                                    <thead>
                                        <tr>
                                            <th>Field</th><th>Value</th><th>Category</th><th>Confidence</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {fields.map((f, i) => {
                                            const fcb = confBadge(f.confidence)
                                            return (
                                                <tr key={i}>
                                                    <td className="td-field">{f.field}</td>
                                                    <td className="td-value">{f.value}</td>
                                                    <td><span className="badge badge-blue" style={{ fontSize: '.7rem', padding: '2px 8px' }}>{f.category}</span></td>
                                                    <td><span className={`conf-badge conf-${fcb.cls}`}>{fcb.label}</span></td>
                                                </tr>
                                            )
                                        })}
                                    </tbody>
                                </table>
                            </div>
                        </div>
                    )}

                    {/* Tables from table agent */}
                    {tables.map((tbl, ti) => (
                        <div className="section" key={ti}>
                            <div className="section-title">📊 {tbl.table_title || `Table ${ti + 1}`}</div>
                            {tbl.headers && tbl.rows ? (
                                <div className="table-wrap">
                                    <table className="data-table">
                                        <thead>
                                            <tr>{tbl.headers.map((h, hi) => <th key={hi}>{h}</th>)}</tr>
                                        </thead>
                                        <tbody>
                                            {tbl.rows.map((row, ri) => (
                                                <tr key={ri}>
                                                    {Array.isArray(row)
                                                        ? row.map((cell, ci) => <td key={ci}>{cell}</td>)
                                                        : tbl.headers.map((h, ci) => <td key={ci}>{row[h] ?? '—'}</td>)
                                                    }
                                                </tr>
                                            ))}
                                        </tbody>
                                    </table>
                                </div>
                            ) : (
                                <pre className="text-content" style={{ fontSize: '.8rem' }}>{JSON.stringify(tbl, null, 2)}</pre>
                            )}
                            {tbl.has_totals && tbl.total_row && (
                                <div className="agent-total-row">
                                    <strong>{tbl.total_row.label || 'Total'}:</strong> {tbl.total_row.value}
                                </div>
                            )}
                        </div>
                    ))}

                    {/* Validation flags */}
                    {flags.length > 0 && (
                        <div className="section">
                            <div className="section-title">⚠️ Validation Flags</div>
                            {flags.map((f, i) => (
                                <div className="agent-flag" key={i}>⚠️ {f}</div>
                            ))}
                        </div>
                    )}

                    {/* Recommendations */}
                    {recs.length > 0 && (
                        <div className="section">
                            <div className="section-title">💡 Recommendations</div>
                            {recs.map((r, i) => (
                                <div className="rec-row" key={i}>✅ {r}</div>
                            ))}
                        </div>
                    )}
                </div>
            </div>
        </div>
    )
}

/* ── AI Tab (legacy) ─────────────────────────────────────────────── */
function AiTab({ ai, isPdf, fileName }) {
    if (!ai) return <div className="empty-state">AI Analysis was not enabled for this document.</div>

    const docType = ai.document_type || 'general'
    const conf = parseFloat(ai.confidence_score || 0)
    const summary = ai.summary || ''
    const insights = ai.key_insights || []
    const entities = ai.extracted_entities || {}
    const recs = ai.recommendations || []
    const allFields = entities.all_fields_in_order || []
    const sections = Object.entries(entities).filter(([k]) => k !== 'all_fields_in_order')

    const typeEmoji = {
        invoice: '🧾', prescription: '💊', medical_form: '🏥', receipt: '🧾',
        contract: '📝', report: '📊', form: '📋', table: '📈', general: '📄', medical_invoice: '🏥',
    }[docType.toLowerCase()] || '📄'

    return (
        <div className="ai-tab">
            <div className="ai-metrics">
                <div className="ai-metric">
                    <div className="ai-metric-label">Document Type</div>
                    <div className="ai-metric-value">{typeEmoji} {docType.replace(/_/g, ' ')}</div>
                </div>
                <div className="ai-metric">
                    <div className="ai-metric-label">AI Confidence</div>
                    <div className={`ai-metric-value conf-${confBadge(conf).cls}`}>{confBadge(conf).label}</div>
                </div>
                <div className="ai-metric">
                    <div className="ai-metric-label">Fields Extracted</div>
                    <div className="ai-metric-value">{allFields.length}</div>
                </div>
                <div className="ai-metric">
                    <div className="ai-metric-label">Sections</div>
                    <div className="ai-metric-value">{sections.length}</div>
                </div>
            </div>

            {summary && <div className="summary-box">📝 {summary}</div>}

            <div className="ai-content-grid">
                {isPdf && fileName && (
                    <div className="ai-pdf-col">
                        <div className="section-title">📄 Document Preview</div>
                        <PdfViewer fileName={fileName} />
                    </div>
                )}

                <div className="ai-data-col">
                    {insights.length > 0 && (
                        <div className="section">
                            <div className="section-title">🔍 Key Insights</div>
                            {insights.map((ins, i) => (
                                <div className="insight-row" key={i}><span className="insight-num">{i + 1}</span>{ins}</div>
                            ))}
                        </div>
                    )}

                    {allFields.length > 0 && (
                        <div className="section">
                            <div className="section-title">🏷️ All Extracted Fields</div>
                            <div className="table-wrap">
                                <table className="data-table">
                                    <thead>
                                        <tr><th>Field</th><th>Value</th><th>Category</th><th>Confidence</th></tr>
                                    </thead>
                                    <tbody>
                                        {allFields.map((f, i) => {
                                            const cb = confBadge(f.confidence)
                                            return (
                                                <tr key={i}>
                                                    <td className="td-field">{f.field}</td>
                                                    <td className="td-value">{f.value}</td>
                                                    <td><span className="badge badge-blue" style={{ fontSize: '.7rem', padding: '2px 8px' }}>{f.category}</span></td>
                                                    <td><span className={`conf-badge conf-${cb.cls}`}>{cb.label}</span></td>
                                                </tr>
                                            )
                                        })}
                                    </tbody>
                                </table>
                            </div>
                        </div>
                    )}

                    {sections.map(([key, data]) => {
                        const title = key.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase())
                        return <SectionBlock key={key} title={`📌 ${title}`} data={data} />
                    })}

                    {recs.length > 0 && (
                        <div className="section">
                            <div className="section-title">💡 Recommendations</div>
                            {recs.map((r, i) => <div className="rec-row" key={i}>✅ {r}</div>)}
                        </div>
                    )}
                </div>
            </div>
        </div>
    )
}

function SectionBlock({ title, data }) {
    const [open, setOpen] = useState(true)

    function renderData() {
        if (Array.isArray(data) && data.length > 0 && typeof data[0] === 'object') {
            const hasCpt = data.some(r => r.cpt_code)
            const priority = hasCpt
                ? ['cpt_code', 'description', 'quantity', 'unit_price', 'total_price', 'date_of_service', 'diagnosis_code', 'modifier']
                : []
            const allKeys = [...new Set([...priority, ...data.flatMap(r => Object.keys(r))])]
                .filter(k => data.some(r => r[k] !== undefined && r[k] !== ''))
            const colLabels = {
                cpt_code: 'CPT Code', description: 'Description', quantity: 'Qty',
                unit_price: 'Unit Price', total_price: 'Total',
                date_of_service: 'Date of Service', diagnosis_code: 'Dx Code', modifier: 'Modifier',
            }
            return (
                <div className="table-wrap">
                    <table className="data-table">
                        <thead><tr>{allKeys.map(k => <th key={k}>{colLabels[k] || k}</th>)}</tr></thead>
                        <tbody>
                            {data.map((row, i) => (
                                <tr key={i}>
                                    {allKeys.map(k => (
                                        <td key={k} className={k === 'cpt_code' ? 'td-cpt' : k === 'description' ? 'td-value' : ''}>
                                            {row[k] ?? '—'}
                                        </td>
                                    ))}
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            )
        }
        if (typeof data === 'object' && !Array.isArray(data)) {
            const rows = Object.entries(data).filter(([, v]) => v !== null && v !== '' && JSON.stringify(v) !== '[]' && JSON.stringify(v) !== '{}')
            return (
                <div className="table-wrap">
                    <table className="data-table">
                        <tbody>
                            {rows.map(([k, v]) => (
                                <tr key={k}>
                                    <td className="td-field">{k.replace(/_/g, ' ')}</td>
                                    <td className="td-value">{typeof v === 'object' ? JSON.stringify(v) : String(v)}</td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            )
        }
        if (Array.isArray(data)) return <ul className="bullet-list">{data.map((d, i) => <li key={i}>{d}</li>)}</ul>
        return <div style={{ color: 'var(--slate)' }}>{String(data)}</div>
    }

    return (
        <div className="section-block">
            <button className="section-toggle" onClick={() => setOpen(!open)}>
                <span>{title}</span>
                <span className="chevron">{open ? '▲' : '▼'}</span>
            </button>
            {open && <div className="section-content">{renderData()}</div>}
        </div>
    )
}

/* ── Text Tab ──────────────────────────────────────────────────────  */
function TextTab({ result }) {
    const text = result?.raw_text || result?.markdown || 'No text extracted.'
    return (
        <div className="text-tab">
            <div className="text-meta">
                <span className="badge badge-blue">{text.length.toLocaleString()} characters</span>
                <span className="badge badge-green">{result?.page_count || 1} pages</span>
            </div>
            <pre className="text-content">{text}</pre>
        </div>
    )
}

/* ── Tables Tab ────────────────────────────────────────────────────  */
function TablesTab({ result }) {
    // Merge tables from chunks AND multi-agent result
    const chunkTables = (result?.chunks || []).filter(c => c.chunk_type === 'table' || c.chunk_type === 'chunkTable')
    const maTables = result?.multi_agent_result?.tables || []

    if (!chunkTables.length && !maTables.length)
        return <div className="empty-state">No tables detected in this document.</div>

    return (
        <div className="tables-tab">
            {maTables.map((t, i) => (
                <div className="card" key={`ma-${i}`} style={{ marginBottom: 16 }}>
                    <div className="card-header"><h4>📊 {t.table_title || `Agent Table ${i + 1}`}</h4></div>
                    {t.headers && t.rows ? (
                        <div className="table-wrap">
                            <table className="data-table">
                                <thead><tr>{t.headers.map((h, hi) => <th key={hi}>{h}</th>)}</tr></thead>
                                <tbody>
                                    {t.rows.map((row, ri) => (
                                        <tr key={ri}>
                                            {Array.isArray(row)
                                                ? row.map((cell, ci) => <td key={ci}>{cell}</td>)
                                                : t.headers.map((h, ci) => <td key={ci}>{row[h] ?? '—'}</td>)
                                            }
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    ) : <pre className="text-content" style={{ fontSize: '.8rem' }}>{JSON.stringify(t, null, 2)}</pre>}
                </div>
            ))}
            {chunkTables.map((t, i) => (
                <div className="card" key={`chunk-${i}`} style={{ marginBottom: 16 }}>
                    <div className="card-header"><h4>Table {i + 1} <span className="text-muted" style={{ fontWeight: 400, fontSize: '.8rem' }}>Page {t.page}</span></h4></div>
                    <pre className="text-content" style={{ fontSize: '.8rem', maxHeight: 300 }}>{t.text}</pre>
                </div>
            ))}
        </div>
    )
}

/* ── JSON Tab ──────────────────────────────────────────────────────  */
function JsonTab({ result }) {
    const [copied, setCopied] = useState(false)
    const json = JSON.stringify(result, null, 2)
    function copy() {
        navigator.clipboard.writeText(json)
        setCopied(true)
        setTimeout(() => setCopied(false), 2000)
    }
    return (
        <div className="json-tab">
            <div className="json-toolbar">
                <span className="badge badge-navy">{(json.length / 1024).toFixed(1)} KB</span>
                <button className="btn-outline" onClick={copy}>{copied ? '✓ Copied!' : '📋 Copy'}</button>
            </div>
            <pre className="json-content">{json}</pre>
        </div>
    )
}

/* ── Export Tab ────────────────────────────────────────────────────  */
function ExportTab({ result }) {
    function downloadJSON() {
        const blob = new Blob([JSON.stringify(result, null, 2)], { type: 'application/json' })
        const a = document.createElement('a'); a.href = URL.createObjectURL(blob)
        a.download = `ai_result_${Date.now()}.json`; a.click()
    }
    function downloadText() {
        const text = result?.raw_text || result?.markdown || ''
        const blob = new Blob([text], { type: 'text/plain' })
        const a = document.createElement('a'); a.href = URL.createObjectURL(blob)
        a.download = `extracted_text_${Date.now()}.txt`; a.click()
    }
    function downloadFields() {
        const fields = result?.multi_agent_result?.extracted_fields || []
        const header = 'Field,Value,Category,Confidence\n'
        const rows = fields.map(f => `"${f.field}","${f.value}","${f.category}","${f.confidence}"`).join('\n')
        const blob = new Blob([header + rows], { type: 'text/csv' })
        const a = document.createElement('a'); a.href = URL.createObjectURL(blob)
        a.download = `extracted_fields_${Date.now()}.csv`; a.click()
    }
    return (
        <div className="export-tab">
            <div className="export-grid">
                <div className="export-card" onClick={downloadJSON}>
                    <div className="export-icon">{ }</div>
                    <div className="export-name">JSON</div>
                    <div className="export-desc">Full result + agent trace</div>
                </div>
                <div className="export-card" onClick={downloadText}>
                    <div className="export-icon">📄</div>
                    <div className="export-name">Plain Text</div>
                    <div className="export-desc">Raw extracted text</div>
                </div>
                <div className="export-card" onClick={downloadFields}>
                    <div className="export-icon">📊</div>
                    <div className="export-name">Fields CSV</div>
                    <div className="export-desc">Multi-agent extracted fields</div>
                </div>
            </div>
        </div>
    )
}

/* ── Main ResultsPage ──────────────────────────────────────────────  */
export default function ResultsPage({ result, onNewUpload }) {
    const [tab, setTab] = useState('pipeline')

    const meta = result?.metadata || {}
    const fileName = meta.file_name || ''
    const isPdf = (result?.document_type || '').toLowerCase() === 'pdf'
    const aiData = result?.ai_analysis || null
    const maData = result?.multi_agent_result || null

    return (
        <div className="results-page">
            {/* ── Results header ── */}
            <div className="results-header">
                <div className="results-header-left">
                    <button className="btn-back" onClick={onNewUpload}>← New Upload</button>
                    <div>
                        <h2 className="results-title">Extraction Results</h2>
                        <div className="results-meta">
                            <span className="badge badge-gold">{result?.ocr_engine || 'OCR'}</span>
                            <span className="badge badge-blue">{result?.document_type?.toUpperCase() || 'DOC'}</span>
                            {result?.page_count > 1 && <span className="badge badge-green">{result.page_count} pages</span>}
                            {maData && <span className="badge badge-purple">🤖 {(maData.agent_trace || []).length} agents</span>}
                            <span className="text-muted" style={{ fontSize: '.82rem' }}>
                                {result?.processing_time ? `${result.processing_time.toFixed(2)}s` : ''}
                            </span>
                        </div>
                    </div>
                </div>
                <div className="results-stats">
                    <div className="stat-chip">
                        <span className="stat-num">{(result?.chunks || []).length}</span>
                        <span className="stat-label">Chunks</span>
                    </div>
                    <div className="stat-chip">
                        <span className="stat-num">{(maData?.extracted_fields || []).length}</span>
                        <span className="stat-label">Fields</span>
                    </div>
                    <div className="stat-chip">
                        <span className="stat-num">{maData ? `${Math.round((maData.overall_confidence || 0) * 100)}%` : '—'}</span>
                        <span className="stat-label">Confidence</span>
                    </div>
                    <div className="stat-chip">
                        <span className="stat-num">{(result?.raw_text || '').length.toLocaleString()}</span>
                        <span className="stat-label">Characters</span>
                    </div>
                </div>
            </div>

            {/* ── Tabs ── */}
            <div className="tab-bar">
                {TABS.map(t => (
                    <button
                        key={t.id}
                        className={`tab-btn ${tab === t.id ? 'active' : ''}`}
                        onClick={() => setTab(t.id)}
                    >
                        {t.label}
                    </button>
                ))}
            </div>

            {/* ── Tab Content ── */}
            <div className="tab-content">
                {tab === 'pipeline' && <PipelineTab ma={maData} />}
                {tab === 'ai' && <AiTab ai={aiData} isPdf={isPdf} fileName={fileName} />}
                {tab === 'text' && <TextTab result={result} />}
                {tab === 'tables' && <TablesTab result={result} />}
                {tab === 'json' && <JsonTab result={result} />}
                {tab === 'export' && <ExportTab result={result} />}
            </div>
        </div>
    )
}
