import './Navbar.css'

export default function Navbar({ onNewUpload, currentPage }) {
    return (
        <header className="navbar">
            <div className="navbar-inner">
                <div className="navbar-brand" onClick={onNewUpload}>
                    <div className="navbar-logo">
                        <span className="logo-icon">⚡</span>
                    </div>
                    <div className="navbar-title">
                        <span className="brand-name">Document AI</span>
                        <span className="brand-tagline">Intelligent Extraction Portal</span>
                    </div>
                </div>

                <nav className="navbar-links">
                    <a className={`nav-link ${currentPage === 'upload' ? 'active' : ''}`} onClick={onNewUpload}>
                        <span className="nav-icon">📤</span> Upload
                    </a>
                    {currentPage === 'results' && (
                        <a className="nav-link active">
                            <span className="nav-icon">📊</span> Results
                        </a>
                    )}
                </nav>

                <div className="navbar-actions">
                    <div className="status-indicator">
                        <span className="status-dot"></span>
                        <span className="status-text">API Connected</span>
                    </div>
                </div>
            </div>
        </header>
    )
}
