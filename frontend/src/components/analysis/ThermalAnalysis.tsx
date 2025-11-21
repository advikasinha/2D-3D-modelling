import { useNavigate } from 'react-router-dom';
import '../../CAE.css';

function ThermalAnalysis() {
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
                    <h2 className="page-title">Thermal Analysis</h2>
                    <p className="page-subtitle">
                        Steady-state thermal analysis with parametric temperature variation
                    </p>
                </div>
            </section>

            {/* Coming Soon Content */}
            <section className="analysis-options-section">
                <div className="section-content">
                    <div className="coming-soon-container">
                        <div className="coming-soon-icon">
                            <svg fill="none" stroke="currentColor" viewBox="0 0 24 24" width="120" height="120">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17.657 18.657A8 8 0 016.343 7.343S7 9 9 10c0-2 .5-5 2.986-7C14 5 16.09 5.777 17.656 7.343A7.975 7.975 0 0120 13a7.975 7.975 0 01-2.343 5.657z" />
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.879 16.121A3 3 0 1012.015 11L11 14H9c0 .768.293 1.536.879 2.121z" />
                            </svg>
                        </div>
                        <h3 className="coming-soon-title">Coming Soon</h3>
                        <p className="coming-soon-description">
                            The thermal analysis module is currently under development. This feature will allow you to:
                        </p>
                        <ul className="coming-soon-features">
                            <li>
                                <svg className="check-icon" fill="currentColor" viewBox="0 0 20 20">
                                    <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                                </svg>
                                Analyze temperature distribution across your model
                            </li>
                            <li>
                                <svg className="check-icon" fill="currentColor" viewBox="0 0 20 20">
                                    <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                                </svg>
                                Calculate heat flux and thermal gradients
                            </li>
                            <li>
                                <svg className="check-icon" fill="currentColor" viewBox="0 0 20 20">
                                    <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                                </svg>
                                Perform parametric temperature studies
                            </li>
                            <li>
                                <svg className="check-icon" fill="currentColor" viewBox="0 0 20 20">
                                    <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                                </svg>
                                Generate comprehensive thermal analysis reports
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

export default ThermalAnalysis;
