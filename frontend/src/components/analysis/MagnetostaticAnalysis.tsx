import { useNavigate } from 'react-router-dom';
import '../../CAE.css';

function MagnetostaticAnalysis() {
    const navigate = useNavigate();

    return (
        <div className="cae-container">
            {/* Header */}
            <header className="cae-header">
                <div className="header-content">
                    <div className="logo-section">
                        <div className="logo-icon">T</div>
                        <h1 className="logo-text">TEB Project</h1>
                    </div>
                    <button onClick={() => navigate('/cae')} className="back-button">
                        <svg className="back-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
                        </svg>
                        Back to CAE
                    </button>
                </div>
            </header>

            {/* Page Title */}
            <section className="page-title-section">
                <div className="page-title-content">
                    <h2 className="page-title">Magnetostatic Analysis</h2>
                    <p className="page-subtitle">
                        Electromagnetic field analysis for static magnetic systems
                    </p>
                </div>
            </section>

            {/* Coming Soon Content */}
            <section className="analysis-options-section">
                <div className="section-content">
                    <div className="coming-soon-container">
                        <div className="coming-soon-icon">
                            <svg fill="none" stroke="currentColor" viewBox="0 0 24 24" width="120" height="120">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 3v2m6-2v2M9 19v2m6-2v2M5 9H3m2 6H3m18-6h-2m2 6h-2M7 19h10a2 2 0 002-2V7a2 2 0 00-2-2H7a2 2 0 00-2 2v10a2 2 0 002 2zM9 9h6v6H9V9z" />
                            </svg>
                        </div>
                        <h3 className="coming-soon-title">Coming Soon</h3>
                        <p className="coming-soon-description">
                            The magnetostatic analysis module is currently under development. This feature will allow you to:
                        </p>
                        <ul className="coming-soon-features">
                            <li>
                                <svg className="check-icon" fill="currentColor" viewBox="0 0 20 20">
                                    <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                                </svg>
                                Analyze magnetic field distribution and flux density
                            </li>
                            <li>
                                <svg className="check-icon" fill="currentColor" viewBox="0 0 20 20">
                                    <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                                </svg>
                                Calculate magnetic forces and torques
                            </li>
                            <li>
                                <svg className="check-icon" fill="currentColor" viewBox="0 0 20 20">
                                    <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                                </svg>
                                Perform parametric current/field studies
                            </li>
                            <li>
                                <svg className="check-icon" fill="currentColor" viewBox="0 0 20 20">
                                    <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                                </svg>
                                Visualize electromagnetic field patterns
                            </li>
                        </ul>
                        <button onClick={() => navigate('/cae')} className="analysis-button">
                            <svg className="arrow-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
                            </svg>
                            Back to Analysis Selection
                        </button>
                    </div>
                </div>
            </section>
        </div>
    );
}

export default MagnetostaticAnalysis;
