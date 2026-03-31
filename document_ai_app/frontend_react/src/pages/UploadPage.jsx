import { useState, useRef, useCallback } from 'react'
import './UploadPage.css'

const ENGINES = [
    {
        id: 'landingai',
        name: 'LandingAI ADE',
        icon: '🚀',
        description: 'Best for complex PDFs, tables & forms. Powered by DPT-2.',
        badge: 'Recommended',
        badgeClass: 'badge-gold',
    },
    {
        id: 'trocr',
        name: 'TrOCR (Handwriting)',
        icon: '✍️',
        description: 'Microsoft Transformer OCR fine-tuned for handwritten & scanned text (trocr-large-handwritten).',
        badge: 'Handwriting',
        badgeClass: 'badge-green',
    },
    {
        id: 'tesseract',
        name: 'Tesseract OCR',
        icon: '🔍',
        description: 'Open-source, fast, and reliable for clear printed text.',
        badge: 'Open Source',
        badgeClass: 'badge-blue',
    },
    {
        id: 'docling',
        name: 'Docling',
        icon: '📚',
        description: 'Advanced document understanding with deep table awareness.',
        badge: 'Advanced',
        badgeClass: 'badge-navy',
    },
]

export default function UploadPage({ onResult, processing, setProcessing }) {
    const [file, setFile] = useState(null)
    const [engine, setEngine] = useState('landingai')
    const [aiEnabled, setAiEnabled] = useState(true)
    const [dragOver, setDragOver] = useState(false)
    const [error, setError] = useState(null)
    const [progress, setProgress] = useState(0)
    const inputRef = useRef()

    const onDrop = useCallback((e) => {
        e.preventDefault()
        setDragOver(false)
        const dropped = e.dataTransfer.files[0]
        if (dropped) selectFile(dropped)
    }, [])

    function selectFile(f) {
        const allowed = ['application/pdf', 'image/png', 'image/jpeg', 'image/jpg', 'image/tiff']
        if (!allowed.includes(f.type) && !f.name.match(/\.(pdf|png|jpg|jpeg|tiff|bmp)$/i)) {
            setError('Unsupported file type. Please upload a PDF or image.')
            return
        }
        setError(null)
        setFile(f)
    }

    async function handleProcess() {
        if (!file) return
        setError(null)
        setProcessing(true)
        setProgress(10)

        try {
            const form = new FormData()
            form.append('file', file)
            form.append('ocr_engine', engine)
            form.append('enable_ai_analysis', aiEnabled)
            form.append('extract_tables', true)
            form.append('extract_figures', true)
            form.append('extract_forms', true)

            setProgress(30)

            const res = await fetch('/api/v1/upload', {
                method: 'POST',
                body: form,
            })

            setProgress(80)
            const data = await res.json()

            if (!res.ok || !data.success) {
                throw new Error(data.error || data.detail || 'Processing failed')
            }

            setProgress(100)
            setTimeout(() => {
                onResult(data.data)
                setProcessing(false)
                setProgress(0)
            }, 300)
        } catch (err) {
            setError(err.message)
            setProcessing(false)
            setProgress(0)
        }
    }

    return (
        <div className="upload-page">
            {/* ── Hero ── */}
            <div className="hero">
                <div className="hero-badge badge badge-gold">AI-Powered Document Intelligence</div>
                <h1 className="hero-title">Extract Any Document,<br /><span className="hero-accent">Instantly & Accurately</span></h1>
                <p className="hero-sub">Upload PDFs or images and get structured data, tables, and AI insights in seconds.</p>
            </div>

            <div className="upload-layout">
                {/* ── Upload Card ── */}
                <div className="card upload-card">
                    <div className="card-header">
                        <h3>📤 Upload Document</h3>
                        <span className="text-muted" style={{ fontSize: '.85rem' }}>PDF · PNG · JPG · TIFF</span>
                    </div>

                    <div
                        className={`drop-zone ${dragOver ? 'drag-over' : ''} ${file ? 'has-file' : ''}`}
                        onDragOver={e => { e.preventDefault(); setDragOver(true) }}
                        onDragLeave={() => setDragOver(false)}
                        onDrop={onDrop}
                        onClick={() => !file && inputRef.current.click()}
                    >
                        <input
                            ref={inputRef}
                            type="file"
                            accept=".pdf,.png,.jpg,.jpeg,.tiff,.bmp"
                            style={{ display: 'none' }}
                            onChange={e => e.target.files[0] && selectFile(e.target.files[0])}
                        />

                        {file ? (
                            <div className="file-preview">
                                <div className="file-icon">{file.name.endsWith('.pdf') ? '📄' : '🖼️'}</div>
                                <div className="file-info">
                                    <div className="file-name">{file.name}</div>
                                    <div className="file-meta">{(file.size / 1024).toFixed(1)} KB</div>
                                </div>
                                <button className="btn-remove" onClick={e => { e.stopPropagation(); setFile(null) }}>✕</button>
                            </div>
                        ) : (
                            <div className="drop-placeholder">
                                <div className="drop-icon">☁️</div>
                                <div className="drop-title">Drop your document here</div>
                                <div className="drop-sub">or <span className="link">click to browse</span></div>
                            </div>
                        )}
                    </div>

                    {error && <div className="error-box">⚠️ {error}</div>}

                    {/* AI Toggle */}
                    <div className="ai-toggle-row">
                        <div className="ai-toggle-info">
                            <span className="ai-toggle-label">🤖 Enable AI Analysis</span>
                            <span className="ai-toggle-desc">Extract entities, confidence scores & insights via Groq LLM</span>
                        </div>
                        <button
                            className={`toggle ${aiEnabled ? 'on' : 'off'}`}
                            onClick={() => setAiEnabled(!aiEnabled)}
                            aria-label="Toggle AI analysis"
                        >
                            <span className="toggle-thumb" />
                        </button>
                    </div>

                    {/* Process Button */}
                    {processing ? (
                        <div className="progress-section">
                            <div className="progress-bar">
                                <div className="progress-fill" style={{ width: `${progress}%` }} />
                            </div>
                            <div className="progress-label">Processing document… {progress}%</div>
                        </div>
                    ) : (
                        <button className="btn-process" onClick={handleProcess} disabled={!file}>
                            <span>⚡</span> Process Document
                        </button>
                    )}
                </div>

                {/* ── Engine Selector ── */}
                <div className="engine-panel">
                    <div className="card-header">
                        <h3>🔧 OCR Engine</h3>
                        <span className="text-muted" style={{ fontSize: '.85rem' }}>Choose extraction method</span>
                    </div>

                    <div className="engine-list">
                        {ENGINES.map(eng => (
                            <div
                                key={eng.id}
                                className={`engine-card ${engine === eng.id ? 'selected' : ''}`}
                                onClick={() => setEngine(eng.id)}
                            >
                                <div className="engine-radio">
                                    <div className={`radio-circle ${engine === eng.id ? 'active' : ''}`} />
                                </div>
                                <div className="engine-icon">{eng.icon}</div>
                                <div className="engine-info">
                                    <div className="engine-name">{eng.name}
                                        <span className={`badge ${eng.badgeClass} engine-badge`}>{eng.badge}</span>
                                    </div>
                                    <div className="engine-desc">{eng.description}</div>
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
            </div>

            {/* ── Feature pills ── */}
            <div className="features-row">
                {['📊 Table Extraction', '💊 Medical Billing', '🔢 Per-Field Confidence', '📄 Multi-Page PDFs', '📋 Structured JSON'].map(f => (
                    <div className="feature-pill" key={f}>{f}</div>
                ))}
            </div>
        </div>
    )
}
