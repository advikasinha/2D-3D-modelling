import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { getAnalysisRecommendation, getAnalysisRecommendationWithImage } from '../../utils/geminiApi';
import '../../CAE.css';

interface RecommendationResult {
    recommendations: Array<{
        analysis_type: 'structural' | 'thermal' | 'magnetostatic' | 'modal';
        confidence: number;
        reasoning: string;
    }>;
    parameters_suggestion?: {
        [key: string]: string | number;
    };
}

const analysisInfo = {
    structural: {
        title: 'Static Structural Analysis',
        icon: 'M19.428 15.428a2 2 0 00-1.022-.547l-2.387-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.806.547M8 4h8l-1 1v5.172a2 2 0 00.586 1.414l5 5c1.26 1.26.367 3.414-1.415 3.414H4.828c-1.782 0-2.674-2.154-1.414-3.414l5-5A2 2 0 009 10.172V5L8 4z',
    },
    thermal: {
        title: 'Thermal Analysis',
        icon: 'M17.657 18.657A8 8 0 016.343 7.343S7 9 9 10c0-2 .5-5 2.986-7C14 5 16.09 5.777 17.656 7.343A7.975 7.975 0 0120 13a7.975 7.975 0 01-2.343 5.657z M9.879 16.121A3 3 0 1012.015 11L11 14H9c0 .768.293 1.536.879 2.121z',
    },
    magnetostatic: {
        title: 'Magnetostatic Analysis',
        icon: 'M9 3v2m6-2v2M9 19v2m6-2v2M5 9H3m2 6H3m18-6h-2m2 6h-2M7 19h10a2 2 0 002-2V7a2 2 0 00-2-2H7a2 2 0 00-2 2v10a2 2 0 002 2zM9 9h6v6H9V9z',
    },
    modal: {
        title: 'Modal Analysis',
        icon: 'M9 19V6l12-3v13M9 19c0 1.105-1.343 2-3 2s-3-.895-3-2 1.343-2 3-2 3 .895 3 2zm12-3c0 1.105-1.343 2-3 2s-3-.895-3-2 1.343-2 3-2 3 .895 3 2zM9 10l12-3',
    },
};

function AIRecommendation() {
    const navigate = useNavigate();

    const [file, setFile] = useState<File | null>(null);
    const [description, setDescription] = useState<string>('');
    const [isAnalyzing, setIsAnalyzing] = useState(false);
    const [error, setError] = useState<string>('');
    const [recommendation, setRecommendation] = useState<RecommendationResult | null>(null);

    const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        if (e.target.files && e.target.files[0]) {
            const selectedFile = e.target.files[0];

            // Accept images (png, jpg, jpeg, webp, etc.) or STEP files
            const isImage = selectedFile.type.startsWith('image/');
            const isStepFile = selectedFile.name.toLowerCase().endsWith('.step') ||
                selectedFile.name.toLowerCase().endsWith('.stp');

            if (isImage || isStepFile) {
                setFile(selectedFile);
                setError('');
            } else {
                setError('Please upload an image (PNG, JPG, etc.) or STEP file (.step, .stp)');
                setFile(null);
            }
        }
    };

    const handleAnalyze = async () => {
        if (!description.trim() && !file) {
            setError('Please provide a description or upload a file');
            return;
        }

        setIsAnalyzing(true);
        setError('');
        setRecommendation(null);

        try {
            let result;

            if (file && file.type.startsWith('image/')) {
                // Use image analysis for visual content
                result = await getAnalysisRecommendationWithImage(description, file);
            } else if (file && (file.name.toLowerCase().endsWith('.step') || file.name.toLowerCase().endsWith('.stp'))) {
                // Extract STEP file content as text
                const stepContent = await file.text();
                // Use text analysis with STEP file content
                const enhancedDescription = description
                    ? `${description}\n\nSTEP File Content (first 2000 chars):\n${stepContent.substring(0, 2000)}`
                    : `STEP File Content (first 2000 chars):\n${stepContent.substring(0, 2000)}`;
                result = await getAnalysisRecommendation(enhancedDescription, file.name);
            } else {
                // Use text-only analysis
                result = await getAnalysisRecommendation(description, file?.name);
            }

            setRecommendation(result.data);
        } catch (err: any) {
            console.error('AI Analysis error:', err);
            setError(err.message || 'Failed to get AI recommendation. Please try again.');
        } finally {
            setIsAnalyzing(false);
        }
    };

    const handleProceedToAnalysis = (analysisType: string) => {
        navigate(`/cae/${analysisType}`);
    };

    const getConfidenceColor = (confidence: number) => {
        if (confidence >= 0.8) return '#000000';
        if (confidence >= 0.6) return '#333333';
        return '#666666';
    };

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
                    <h2 className="page-title">AI-Powered Analysis Recommendation</h2>
                    <p className="page-subtitle">
                        Let AI suggest the most suitable analysis type for your project
                    </p>
                </div>
            </section>

            {/* Main Content */}
            <section className="analysis-options-section">
                <div className="section-content">

                    {/* Input Form */}
                    {!recommendation && (
                        <div className="ai-recommendation-container">
                            <div className="ai-input-card">
                                <div className="ai-icon-container">
                                    <svg className="ai-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24" width="60" height="60">
                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
                                    </svg>
                                </div>

                                <h3 className="ai-title">Describe Your Analysis Needs</h3>
                                <p className="ai-description">
                                    Upload an image for visual analysis or a STEP file to extract geometry details.
                                    Describe what you want to analyze and our AI will recommend the best analysis type.
                                </p>

                                {/* File Upload */}
                                <div className="file-upload-area">
                                    <input
                                        type="file"
                                        id="aiFile"
                                        accept=".step,.stp,image/*"
                                        onChange={handleFileChange}
                                        className="file-input"
                                    />
                                    <label htmlFor="aiFile" className="file-label">
                                        {file ? (
                                            <div className="file-selected">
                                                <svg className="check-icon" fill="currentColor" viewBox="0 0 20 20">
                                                    <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                                                </svg>
                                                <span>{file.name}</span>
                                                {file.type.startsWith('image/') && (
                                                    <span className="file-type-badge">Image</span>
                                                )}
                                                {(file.name.toLowerCase().endsWith('.step') || file.name.toLowerCase().endsWith('.stp')) && (
                                                    <span className="file-type-badge">STEP</span>
                                                )}
                                            </div>
                                        ) : (
                                            <div className="file-placeholder">
                                                <svg className="upload-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                                                </svg>
                                                <span>Click to upload file (optional)</span>
                                                <span className="file-hint">Images for visual analysis • STEP files for geometry extraction</span>
                                            </div>
                                        )}
                                    </label>
                                </div>

                                {/* Description Input */}
                                <div className="ai-description-input">
                                    <label htmlFor="description" className="form-label">
                                        Describe your analysis requirements
                                        <span className="label-hint">What are you trying to analyze? What forces/conditions are involved?</span>
                                    </label>
                                    <textarea
                                        id="description"
                                        value={description}
                                        onChange={(e) => setDescription(e.target.value)}
                                        className="description-textarea"
                                        placeholder="Example: I need to analyze a steel bracket under a 500N vertical load to ensure it doesn't fail..."
                                        rows={5}
                                    />
                                </div>

                                {/* Error Display */}
                                {error && (
                                    <div className="error-message">
                                        <svg className="error-icon" fill="currentColor" viewBox="0 0 20 20">
                                            <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                                        </svg>
                                        {error}
                                    </div>
                                )}

                                {/* Analyze Button */}
                                <button
                                    onClick={handleAnalyze}
                                    className="analysis-button submit-button"
                                    disabled={isAnalyzing || (!description.trim() && !file)}
                                >
                                    {isAnalyzing ? (
                                        <>
                                            <div className="spinner"></div>
                                            Analyzing...
                                        </>
                                    ) : (
                                        <>
                                            <svg className="arrow-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                                            </svg>
                                            Get AI Recommendation
                                        </>
                                    )}
                                </button>
                            </div>
                        </div>
                    )}

                    {/* Recommendation Result */}
                    {recommendation && (
                        <div className="ai-result-container">
                            <div className="result-header">
                                <h3 className="result-title">AI Analysis Recommendations</h3>
                                <p className="result-subtitle">Top 3 recommended analyses ranked by relevance</p>
                            </div>

                            {/* Top 3 Recommendations */}
                            {recommendation.recommendations.map((rec, index) => (
                                <div 
                                    key={index} 
                                    className={`recommended-analysis-card ${index === 0 ? 'primary' : index === 1 ? 'secondary' : 'tertiary'}`}
                                >
                                    <div className="rank-badge">
                                        {index === 0 ? '🥇' : index === 1 ? '🥈' : '🥉'}
                                        <span className="rank-text">{index === 0 ? '1st' : index === 1 ? '2nd' : '3rd'} Choice</span>
                                    </div>
                                    
                                    <div className="recommendation-content">
                                        <div className="recommended-icon">
                                            <svg fill="none" stroke="currentColor" viewBox="0 0 24 24" width="60" height="60">
                                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d={analysisInfo[rec.analysis_type].icon} />
                                            </svg>
                                        </div>
                                        
                                        <div className="recommendation-details">
                                            <h4 className="recommended-title">{analysisInfo[rec.analysis_type].title}</h4>
                                            
                                            <div className="confidence-meter">
                                                <div className="confidence-bar">
                                                    <div
                                                        className="confidence-fill"
                                                        style={{ 
                                                            width: `${rec.confidence * 100}%`,
                                                            backgroundColor: getConfidenceColor(rec.confidence)
                                                        }}
                                                    ></div>
                                                </div>
                                                <span className="confidence-text">{(rec.confidence * 100).toFixed(0)}% Match</span>
                                            </div>
                                            
                                            <div className="reasoning-inline">
                                                <p className="reasoning-text">{rec.reasoning}</p>
                                            </div>
                                            
                                            <button 
                                                onClick={() => handleProceedToAnalysis(rec.analysis_type)} 
                                                className="analysis-button proceed-btn"
                                            >
                                                <svg className="arrow-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7l5 5m0 0l-5 5m5-5H6" />
                                                </svg>
                                                Launch Analysis
                                            </button>
                                        </div>
                                    </div>
                                </div>
                            ))}

                            {/* Parameter Suggestions */}
                            {recommendation.parameters_suggestion && Object.keys(recommendation.parameters_suggestion).length > 0 && (
                                <div className="parameters-section">
                                    <h4 className="section-subtitle">
                                        <svg className="section-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                                        </svg>
                                        Suggested Parameters (for top recommendation)
                                    </h4>
                                    <div className="parameters-grid">
                                        {Object.entries(recommendation.parameters_suggestion).map(([key, value]) => (
                                            <div key={key} className="parameter-item">
                                                <span className="parameter-key">{key}:</span>
                                                <span className="parameter-value">{String(value)}</span>
                                            </div>
                                        ))}
                                    </div>
                                </div>
                            )}

                            {/* Action Buttons */}
                            <div className="result-actions">
                                <button onClick={() => setRecommendation(null)} className="analysis-button secondary">
                                    <svg className="arrow-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                                    </svg>
                                    Try Again
                                </button>
                            </div>
                        </div>
                    )}
                </div>
            </section>
        </div>
    );
}

export default AIRecommendation;
