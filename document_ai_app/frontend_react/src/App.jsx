import { useState } from 'react'
import Navbar from './components/Navbar'
import UploadPage from './pages/UploadPage'
import ResultsPage from './pages/ResultsPage'
import './App.css'

export default function App() {
    const [page, setPage] = useState('upload')         // 'upload' | 'results'
    const [result, setResult] = useState(null)
    const [processing, setProcessing] = useState(false)

    function handleResult(data) {
        setResult(data)
        setPage('results')
    }

    function handleNewUpload() {
        setResult(null)
        setPage('upload')
    }

    return (
        <div className="app-shell">
            <Navbar onNewUpload={handleNewUpload} currentPage={page} />
            <main className="app-main">
                {page === 'upload' ? (
                    <UploadPage
                        onResult={handleResult}
                        processing={processing}
                        setProcessing={setProcessing}
                    />
                ) : (
                    <ResultsPage result={result} onNewUpload={handleNewUpload} />
                )}
            </main>
            <footer className="app-footer">
                <span>© 2025 Document AI Portal</span>
                <span className="footer-sep">·</span>
                <span>Powered by LandingAI · Groq · FastAPI</span>
            </footer>
        </div>
    )
}
