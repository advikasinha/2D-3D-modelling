import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import '../../CAE.css';

interface AnalysisResults {
    excel_data: string; // base64 encoded Excel file
    comprehensive_plot: string; // base64 encoded PNG
    linearity_plot: string; // base64 encoded PNG
    stress_animation: string; // base64 encoded GIF
    displacement_animation: string; // base64 encoded GIF
    first_stress_components: string[]; // base64 encoded PNGs
    last_stress_components: string[]; // base64 encoded PNGs
    first_displacement_components: string[]; // base64 encoded PNGs
    last_displacement_components: string[]; // base64 encoded PNGs
    first_principal_stresses: string[]; // base64 encoded PNGs
    last_principal_stresses: string[]; // base64 encoded PNGs
    first_deformed_shape: string; // base64 encoded PNG
    last_deformed_shape: string; // base64 encoded PNG
    summary_stats: {
        force_min: number;
        force_max: number;
        force_avg: number;
        stress_min: number;
        stress_max: number;
        stress_avg: number;
        displacement_min: number;
        displacement_max: number;
        displacement_avg: number;
    };
}

function StructuralAnalysis() {
    const navigate = useNavigate();

    // Form state
    const [stepFile, setStepFile] = useState<File | null>(null);
    const [meshSize, setMeshSize] = useState<string>('8.0');
    const [forceMin, setForceMin] = useState<string>('100');
    const [forceMax, setForceMax] = useState<string>('1000');
    const [forceSteps, setForceSteps] = useState<string>('10');
    const [youngsModulus, setYoungsModulus] = useState<string>('200e9');
    const [poissonsRatio, setPoissonsRatio] = useState<string>('0.3');
    const [density, setDensity] = useState<string>('7850');

    // UI state
    const [isAnalyzing, setIsAnalyzing] = useState(false);
    const [progress, setProgress] = useState<string>('');
    const [results, setResults] = useState<AnalysisResults | null>(null);
    const [error, setError] = useState<string>('');
    const [activeTab, setActiveTab] = useState<string>('overview');

    const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        if (e.target.files && e.target.files[0]) {
            const file = e.target.files[0];
            if (file.name.endsWith('.step') || file.name.endsWith('.stp')) {
                setStepFile(file);
                setError('');
            } else {
                setError('Please select a valid STEP file (.step or .stp)');
                setStepFile(null);
            }
        }
    };

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();

        if (!stepFile) {
            setError('Please upload a STEP file');
            return;
        }

        setIsAnalyzing(true);
        setProgress('Uploading file and initializing analysis...');
        setError('');
        setResults(null);

        const formData = new FormData();
        formData.append('step_file', stepFile);
        formData.append('mesh_size', meshSize);
        formData.append('force_min', forceMin);
        formData.append('force_max', forceMax);
        formData.append('force_steps', forceSteps);
        formData.append('youngs_modulus', youngsModulus);
        formData.append('poissons_ratio', poissonsRatio);
        formData.append('density', density);

        try {
            // Replace with your actual Flask backend URL
            const response = await axios.post('http://localhost:5003/api/structural-analysis', formData, {
                headers: {
                    'Content-Type': 'multipart/form-data',
                },
                onUploadProgress: (progressEvent) => {
                    if (progressEvent.total) {
                        const percentCompleted = Math.round((progressEvent.loaded * 100) / progressEvent.total);
                        setProgress(`Uploading: ${percentCompleted}%`);
                    }
                },
                timeout: 600000, // 10 minutes timeout for long analysis
            });

            setProgress('Analysis completed successfully!');
            setResults(response.data);
            setActiveTab('overview');
        } catch (err: any) {
            console.error('Analysis error:', err);
            setError(err.response?.data?.error || 'An error occurred during analysis. Please try again.');
            setProgress('');
        } finally {
            setIsAnalyzing(false);
        }
    };

    const downloadExcel = () => {
        if (results?.excel_data) {
            const link = document.createElement('a');
            link.href = `data:application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;base64,${results.excel_data}`;
            link.download = `structural_analysis_${new Date().getTime()}.xlsx`;
            link.click();
        }
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
                    <h2 className="page-title">Static Structural Analysis</h2>
                    <p className="page-subtitle">
                        Parametric force variation study with comprehensive visualization
                    </p>
                </div>
            </section>

            {/* Main Content */}
            <section className="analysis-options-section">
                <div className="section-content">

                    {/* Analysis Form */}
                    {!results && (
                        <div className="analysis-form-container">
                            <h3 className="section-title">Analysis Configuration</h3>

                            <form onSubmit={handleSubmit} className="analysis-form">
                                {/* File Upload Section */}
                                <div className="form-section">
                                    <h4 className="form-section-title">
                                        <svg className="section-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                                        </svg>
                                        CAD Model Upload
                                    </h4>

                                    <div className="file-upload-area">
                                        <input
                                            type="file"
                                            id="stepFile"
                                            accept=".step,.stp"
                                            onChange={handleFileChange}
                                            className="file-input"
                                        />
                                        <label htmlFor="stepFile" className="file-label">
                                            {stepFile ? (
                                                <div className="file-selected">
                                                    <svg className="check-icon" fill="currentColor" viewBox="0 0 20 20">
                                                        <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                                                    </svg>
                                                    <span>{stepFile.name}</span>
                                                </div>
                                            ) : (
                                                <div className="file-placeholder">
                                                    <svg className="upload-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                                                    </svg>
                                                    <span>Click to upload STEP file</span>
                                                    <span className="file-hint">Supported: .step, .stp</span>
                                                </div>
                                            )}
                                        </label>
                                    </div>
                                </div>

                                {/* Mesh Configuration */}
                                <div className="form-section">
                                    <h4 className="form-section-title">
                                        <svg className="section-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 5a1 1 0 011-1h4a1 1 0 011 1v7a1 1 0 01-1 1H5a1 1 0 01-1-1V5zM14 5a1 1 0 011-1h4a1 1 0 011 1v7a1 1 0 01-1 1h-4a1 1 0 01-1-1V5zM4 16a1 1 0 011-1h4a1 1 0 011 1v3a1 1 0 01-1 1H5a1 1 0 01-1-1v-3zM14 16a1 1 0 011-1h4a1 1 0 011 1v3a1 1 0 01-1 1h-4a1 1 0 01-1-1v-3z" />
                                        </svg>
                                        Mesh Configuration
                                    </h4>

                                    <div className="form-group">
                                        <label htmlFor="meshSize" className="form-label">
                                            Mesh Size (mm)
                                            <span className="label-hint">Smaller = More accurate but slower</span>
                                        </label>
                                        <input
                                            type="number"
                                            id="meshSize"
                                            value={meshSize}
                                            onChange={(e) => setMeshSize(e.target.value)}
                                            step="0.1"
                                            min="0.1"
                                            className="form-input"
                                            required
                                        />
                                    </div>
                                </div>

                                {/* Force Parameters */}
                                <div className="form-section">
                                    <h4 className="form-section-title">
                                        <svg className="section-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                                        </svg>
                                        Force Parametric Study
                                    </h4>

                                    <div className="form-grid">
                                        <div className="form-group">
                                            <label htmlFor="forceMin" className="form-label">Minimum Force (N)</label>
                                            <input
                                                type="number"
                                                id="forceMin"
                                                value={forceMin}
                                                onChange={(e) => setForceMin(e.target.value)}
                                                step="1"
                                                className="form-input"
                                                required
                                            />
                                        </div>

                                        <div className="form-group">
                                            <label htmlFor="forceMax" className="form-label">Maximum Force (N)</label>
                                            <input
                                                type="number"
                                                id="forceMax"
                                                value={forceMax}
                                                onChange={(e) => setForceMax(e.target.value)}
                                                step="1"
                                                className="form-input"
                                                required
                                            />
                                        </div>

                                        <div className="form-group">
                                            <label htmlFor="forceSteps" className="form-label">Number of Steps</label>
                                            <input
                                                type="number"
                                                id="forceSteps"
                                                value={forceSteps}
                                                onChange={(e) => setForceSteps(e.target.value)}
                                                step="1"
                                                min="2"
                                                className="form-input"
                                                required
                                            />
                                        </div>
                                    </div>
                                </div>

                                {/* Material Properties */}
                                <div className="form-section">
                                    <h4 className="form-section-title">
                                        <svg className="section-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19.428 15.428a2 2 0 00-1.022-.547l-2.387-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.806.547M8 4h8l-1 1v5.172a2 2 0 00.586 1.414l5 5c1.26 1.26.367 3.414-1.415 3.414H4.828c-1.782 0-2.674-2.154-1.414-3.414l5-5A2 2 0 009 10.172V5L8 4z" />
                                        </svg>
                                        Material Properties
                                    </h4>

                                    <div className="form-grid">
                                        <div className="form-group">
                                            <label htmlFor="youngsModulus" className="form-label">
                                                Young's Modulus (Pa)
                                                <span className="label-hint">Default: Steel (200 GPa)</span>
                                            </label>
                                            <input
                                                type="text"
                                                id="youngsModulus"
                                                value={youngsModulus}
                                                onChange={(e) => setYoungsModulus(e.target.value)}
                                                className="form-input"
                                                placeholder="200e9"
                                                required
                                            />
                                        </div>

                                        <div className="form-group">
                                            <label htmlFor="poissonsRatio" className="form-label">
                                                Poisson's Ratio
                                                <span className="label-hint">Typical: 0.25-0.35</span>
                                            </label>
                                            <input
                                                type="number"
                                                id="poissonsRatio"
                                                value={poissonsRatio}
                                                onChange={(e) => setPoissonsRatio(e.target.value)}
                                                step="0.01"
                                                min="0"
                                                max="0.5"
                                                className="form-input"
                                                required
                                            />
                                        </div>

                                        <div className="form-group">
                                            <label htmlFor="density" className="form-label">
                                                Density (kg/m³)
                                                <span className="label-hint">Default: Steel (7850)</span>
                                            </label>
                                            <input
                                                type="number"
                                                id="density"
                                                value={density}
                                                onChange={(e) => setDensity(e.target.value)}
                                                step="1"
                                                className="form-input"
                                                required
                                            />
                                        </div>
                                    </div>
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

                                {/* Progress Display */}
                                {isAnalyzing && (
                                    <div className="progress-container">
                                        <div className="progress-bar">
                                            <div className="progress-fill"></div>
                                        </div>
                                        <p className="progress-text">{progress}</p>
                                    </div>
                                )}

                                {/* Submit Button */}
                                <button
                                    type="submit"
                                    className="analysis-button submit-button"
                                    disabled={isAnalyzing || !stepFile}
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
                                            Run Analysis
                                        </>
                                    )}
                                </button>
                            </form>
                        </div>
                    )}

                    {/* Results Display */}
                    {results && (
                        <div className="results-container">
                            <div className="results-header">
                                <h3 className="section-title">Analysis Results</h3>
                                <div className="results-actions">
                                    <button onClick={downloadExcel} className="action-button">
                                        <svg className="button-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                                        </svg>
                                        Download Excel
                                    </button>
                                    <button onClick={() => setResults(null)} className="action-button secondary">
                                        <svg className="button-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                                        </svg>
                                        New Analysis
                                    </button>
                                </div>
                            </div>

                            {/* Results Tabs */}
                            <div className="results-tabs">
                                <button
                                    className={`tab-button ${activeTab === 'overview' ? 'active' : ''}`}
                                    onClick={() => setActiveTab('overview')}
                                >
                                    Overview
                                </button>
                                <button
                                    className={`tab-button ${activeTab === 'animations' ? 'active' : ''}`}
                                    onClick={() => setActiveTab('animations')}
                                >
                                    Animations
                                </button>
                                <button
                                    className={`tab-button ${activeTab === 'components' ? 'active' : ''}`}
                                    onClick={() => setActiveTab('components')}
                                >
                                    Component Analysis
                                </button>
                                <button
                                    className={`tab-button ${activeTab === 'statistics' ? 'active' : ''}`}
                                    onClick={() => setActiveTab('statistics')}
                                >
                                    Statistics
                                </button>
                            </div>

                            {/* Tab Content */}
                            <div className="tab-content">
                                {/* Overview Tab */}
                                {activeTab === 'overview' && (
                                    <div className="tab-panel">
                                        <div className="image-grid">
                                            <div className="image-card">
                                                <h4 className="image-title">Comprehensive Parametric Analysis</h4>
                                                <img
                                                    src={`data:image/png;base64,${results.comprehensive_plot}`}
                                                    alt="Comprehensive Analysis"
                                                    className="result-image"
                                                />
                                            </div>
                                            <div className="image-card">
                                                <h4 className="image-title">Linearity Check</h4>
                                                <img
                                                    src={`data:image/png;base64,${results.linearity_plot}`}
                                                    alt="Linearity Check"
                                                    className="result-image"
                                                />
                                            </div>
                                        </div>
                                    </div>
                                )}

                                {/* Animations Tab */}
                                {activeTab === 'animations' && (
                                    <div className="tab-panel">
                                        <div className="image-grid">
                                            <div className="image-card">
                                                <h4 className="image-title">Stress Evolution</h4>
                                                <img
                                                    src={`data:image/gif;base64,${results.stress_animation}`}
                                                    alt="Stress Animation"
                                                    className="result-image"
                                                />
                                            </div>
                                            <div className="image-card">
                                                <h4 className="image-title">Displacement Evolution</h4>
                                                <img
                                                    src={`data:image/gif;base64,${results.displacement_animation}`}
                                                    alt="Displacement Animation"
                                                    className="result-image"
                                                />
                                            </div>
                                        </div>

                                        <div className="image-grid">
                                            <div className="image-card">
                                                <h4 className="image-title">Initial Deformed Shape</h4>
                                                <img
                                                    src={`data:image/png;base64,${results.first_deformed_shape}`}
                                                    alt="First Deformed Shape"
                                                    className="result-image"
                                                />
                                            </div>
                                            <div className="image-card">
                                                <h4 className="image-title">Final Deformed Shape</h4>
                                                <img
                                                    src={`data:image/png;base64,${results.last_deformed_shape}`}
                                                    alt="Last Deformed Shape"
                                                    className="result-image"
                                                />
                                            </div>
                                        </div>
                                    </div>
                                )}

                                {/* Components Tab */}
                                {activeTab === 'components' && (
                                    <div className="tab-panel">
                                        <h4 className="subsection-title">Initial Load Step - Stress Components</h4>
                                        <div className="component-grid">
                                            {results.first_stress_components.map((img, idx) => (
                                                <div key={`first-stress-${idx}`} className="component-card">
                                                    <img
                                                        src={`data:image/png;base64,${img}`}
                                                        alt={`First Stress Component ${idx + 1}`}
                                                        className="result-image"
                                                    />
                                                </div>
                                            ))}
                                        </div>

                                        <h4 className="subsection-title">Final Load Step - Stress Components</h4>
                                        <div className="component-grid">
                                            {results.last_stress_components.map((img, idx) => (
                                                <div key={`last-stress-${idx}`} className="component-card">
                                                    <img
                                                        src={`data:image/png;base64,${img}`}
                                                        alt={`Last Stress Component ${idx + 1}`}
                                                        className="result-image"
                                                    />
                                                </div>
                                            ))}
                                        </div>

                                        <h4 className="subsection-title">Principal Stresses - Initial</h4>
                                        <div className="component-grid">
                                            {results.first_principal_stresses.map((img, idx) => (
                                                <div key={`first-principal-${idx}`} className="component-card">
                                                    <img
                                                        src={`data:image/png;base64,${img}`}
                                                        alt={`First Principal Stress ${idx + 1}`}
                                                        className="result-image"
                                                    />
                                                </div>
                                            ))}
                                        </div>

                                        <h4 className="subsection-title">Principal Stresses - Final</h4>
                                        <div className="component-grid">
                                            {results.last_principal_stresses.map((img, idx) => (
                                                <div key={`last-principal-${idx}`} className="component-card">
                                                    <img
                                                        src={`data:image/png;base64,${img}`}
                                                        alt={`Last Principal Stress ${idx + 1}`}
                                                        className="result-image"
                                                    />
                                                </div>
                                            ))}
                                        </div>

                                        <h4 className="subsection-title">Displacement Components - Initial</h4>
                                        <div className="component-grid">
                                            {results.first_displacement_components.map((img, idx) => (
                                                <div key={`first-disp-${idx}`} className="component-card">
                                                    <img
                                                        src={`data:image/png;base64,${img}`}
                                                        alt={`First Displacement Component ${idx + 1}`}
                                                        className="result-image"
                                                    />
                                                </div>
                                            ))}
                                        </div>

                                        <h4 className="subsection-title">Displacement Components - Final</h4>
                                        <div className="component-grid">
                                            {results.last_displacement_components.map((img, idx) => (
                                                <div key={`last-disp-${idx}`} className="component-card">
                                                    <img
                                                        src={`data:image/png;base64,${img}`}
                                                        alt={`Last Displacement Component ${idx + 1}`}
                                                        className="result-image"
                                                    />
                                                </div>
                                            ))}
                                        </div>
                                    </div>
                                )}

                                {/* Statistics Tab */}
                                {activeTab === 'statistics' && (
                                    <div className="tab-panel">
                                        <div className="stats-grid">
                                            <div className="stat-card">
                                                <h4 className="stat-title">Force Range</h4>
                                                <div className="stat-row">
                                                    <span className="stat-label">Minimum:</span>
                                                    <span className="stat-value">{results.summary_stats.force_min.toFixed(2)} N</span>
                                                </div>
                                                <div className="stat-row">
                                                    <span className="stat-label">Maximum:</span>
                                                    <span className="stat-value">{results.summary_stats.force_max.toFixed(2)} N</span>
                                                </div>
                                                <div className="stat-row">
                                                    <span className="stat-label">Average:</span>
                                                    <span className="stat-value">{results.summary_stats.force_avg.toFixed(2)} N</span>
                                                </div>
                                            </div>

                                            <div className="stat-card">
                                                <h4 className="stat-title">Maximum Stress</h4>
                                                <div className="stat-row">
                                                    <span className="stat-label">Minimum:</span>
                                                    <span className="stat-value">{results.summary_stats.stress_min.toFixed(2)} MPa</span>
                                                </div>
                                                <div className="stat-row">
                                                    <span className="stat-label">Maximum:</span>
                                                    <span className="stat-value">{results.summary_stats.stress_max.toFixed(2)} MPa</span>
                                                </div>
                                                <div className="stat-row">
                                                    <span className="stat-label">Average:</span>
                                                    <span className="stat-value">{results.summary_stats.stress_avg.toFixed(2)} MPa</span>
                                                </div>
                                            </div>

                                            <div className="stat-card">
                                                <h4 className="stat-title">Maximum Displacement</h4>
                                                <div className="stat-row">
                                                    <span className="stat-label">Minimum:</span>
                                                    <span className="stat-value">{results.summary_stats.displacement_min.toFixed(4)} mm</span>
                                                </div>
                                                <div className="stat-row">
                                                    <span className="stat-label">Maximum:</span>
                                                    <span className="stat-value">{results.summary_stats.displacement_max.toFixed(4)} mm</span>
                                                </div>
                                                <div className="stat-row">
                                                    <span className="stat-label">Average:</span>
                                                    <span className="stat-value">{results.summary_stats.displacement_avg.toFixed(4)} mm</span>
                                                </div>
                                            </div>
                                        </div>
                                    </div>
                                )}
                            </div>
                        </div>
                    )}
                </div>
            </section>
        </div>
    );
}

export default StructuralAnalysis;
