import { useState, ChangeEvent, FormEvent } from 'react';
import axios, { AxiosError } from 'axios';
import './App.css';

type FileState = {
    top_view: File | null;
    front_view: File | null;
    side_view: File | null;
};

type PreviewState = {
    top_view: string | null;
    front_view: string | null;
    side_view: string | null;
};

interface DimensionResult {
    root: {
        type: string;
        operations: Array<{
            type: string;
            dimensions: {
                width: number;
                height: number;
                depth: number;
            };
            position: {
                x: number;
                y: number;
                z: number;
            };
        }>;
    };
}

function DimensionExtractor() {
    const [files, setFiles] = useState<FileState>({
        top_view: null,
        front_view: null,
        side_view: null
    });
    const [isLoading, setIsLoading] = useState<boolean>(false);
    const [result, setResult] = useState<DimensionResult | null>(null);
    const [error, setError] = useState<string | null>(null);
    const [previews, setPreviews] = useState<PreviewState>({
        top_view: null,
        front_view: null,
        side_view: null
    });
    const [vbaScript, setVbaScript] = useState<string | null>(null);
    const [vbaError, setVbaError] = useState<string | null>(null);
    const [isGeneratingVba, setIsGeneratingVba] = useState<boolean>(false);

    const handleFileChange = (e: ChangeEvent<HTMLInputElement>) => {
        const { name, files: selectedFiles } = e.target;
        if (selectedFiles && selectedFiles[0]) {
            const file = selectedFiles[0];
            setFiles(prev => ({ ...prev, [name]: file }));

            const reader = new FileReader();
            reader.onload = (event) => {
                if (event.target?.result) {
                    setPreviews(prev => ({ ...prev, [name]: event.target?.result as string }));
                }
            };
            reader.readAsDataURL(file);
        }
    };

    const handleSubmit = async (e: FormEvent) => {
        e.preventDefault();
        setIsLoading(true);
        setError(null);
        setResult(null);
        setVbaScript(null);
        setVbaError(null);

        try {
            const formData = new FormData();
            for (const [key, value] of Object.entries(files)) {
                if (value) {
                    formData.append(key, value);
                }
            }

            const response = await axios.post<DimensionResult>(
                'http://localhost:5001/extract-dimensions',
                formData,
                {
                    headers: {
                        'Content-Type': 'multipart/form-data'
                    }
                }
            );

            setResult(response.data);
        } catch (err) {
            const error = err as AxiosError<{ error: string }>;
            setError(
                error.response?.data?.error ||
                error.message ||
                'An error occurred while processing the images'
            );
        } finally {
            setIsLoading(false);
        }
    };

    const handleGenerateVba = async () => {
        if (!result) return;

        setIsGeneratingVba(true);
        setVbaError(null);
        setVbaScript(null);

        try {
            const response = await axios.post(
                'http://localhost:5002/convert-clean',
                result,
                {
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    responseType: 'text'
                }
            );

            setVbaScript(response.data);
        } catch (err) {
            const error = err as AxiosError;
            setVbaError(
                error.message ||
                'An error occurred while generating VBA script'
            );
        } finally {
            setIsGeneratingVba(false);
        }
    };

    const handleDownloadVba = () => {
        if (!vbaScript) return;

        const blob = new Blob([vbaScript], { type: 'text/plain' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = 'solidworks_macro.vba';
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    };

    const allFilesSelected = Object.values(files).every(file => file !== null);

    return (
        <div className="app-container">
            <div className="app-content">
                <header className="app-header">
                    <h1>Engineering Drawing Dimension Extractor</h1>
                    <p className="app-description">
                        Upload your engineering drawing views to extract dimensions and generate SolidWorks VBA scripts
                    </p>
                </header>

                <div className="main-content">
                    <form onSubmit={handleSubmit} className="upload-form">
                        <div className="file-upload-section">
                            <h2>Upload Engineering Drawing Views</h2>

                            <div className="file-inputs">
                                <div className="file-input-group">
                                    <label htmlFor="top_view">Top View</label>
                                    <div className="file-upload-wrapper">
                                        <input
                                            type="file"
                                            id="top_view"
                                            name="top_view"
                                            accept="image/*"
                                            onChange={handleFileChange}
                                            required
                                        />
                                        <div className="file-upload-label">
                                            {files.top_view ? files.top_view.name : 'Choose file...'}
                                        </div>
                                    </div>
                                    {previews.top_view && (
                                        <div className="image-preview">
                                            <img src={previews.top_view} alt="Top view preview" />
                                        </div>
                                    )}
                                </div>

                                <div className="file-input-group">
                                    <label htmlFor="front_view">Front View</label>
                                    <div className="file-upload-wrapper">
                                        <input
                                            type="file"
                                            id="front_view"
                                            name="front_view"
                                            accept="image/*"
                                            onChange={handleFileChange}
                                            required
                                        />
                                        <div className="file-upload-label">
                                            {files.front_view ? files.front_view.name : 'Choose file...'}
                                        </div>
                                    </div>
                                    {previews.front_view && (
                                        <div className="image-preview">
                                            <img src={previews.front_view} alt="Front view preview" />
                                        </div>
                                    )}
                                </div>

                                <div className="file-input-group">
                                    <label htmlFor="side_view">Side View</label>
                                    <div className="file-upload-wrapper">
                                        <input
                                            type="file"
                                            id="side_view"
                                            name="side_view"
                                            accept="image/*"
                                            onChange={handleFileChange}
                                            required
                                        />
                                        <div className="file-upload-label">
                                            {files.side_view ? files.side_view.name : 'Choose file...'}
                                        </div>
                                    </div>
                                    {previews.side_view && (
                                        <div className="image-preview">
                                            <img src={previews.side_view} alt="Side view preview" />
                                        </div>
                                    )}
                                </div>
                            </div>

                            <button
                                type="submit"
                                disabled={!allFilesSelected || isLoading}
                                className={`submit-button ${(!allFilesSelected || isLoading) ? 'disabled' : ''}`}
                            >
                                {isLoading ? (
                                    <>
                                        <span className="spinner"></span>
                                        Processing...
                                    </>
                                ) : 'Extract Dimensions'}
                            </button>
                        </div>
                    </form>

                    {error && (
                        <div className="error-message">
                            <h3>Error</h3>
                            <p>{error}</p>
                        </div>
                    )}

                    {result && (
                        <div className="result-section">
                            <div className="result-header">
                                <h2>Extracted Dimensions</h2>
                                <button
                                    onClick={handleGenerateVba}
                                    disabled={isGeneratingVba}
                                    className={`generate-vba-button ${isGeneratingVba ? 'disabled' : ''}`}
                                >
                                    {isGeneratingVba ? (
                                        <>
                                            <span className="spinner"></span>
                                            Generating VBA...
                                        </>
                                    ) : 'Generate SolidWorks VBA Script'}
                                </button>
                            </div>

                            <div className="result-content">
                                <div className="result-display">
                                    <pre>{JSON.stringify(result, null, 2)}</pre>
                                </div>

                                {vbaError && (
                                    <div className="error-message">
                                        <h3>VBA Generation Error</h3>
                                        <p>{vbaError}</p>
                                    </div>
                                )}

                                {vbaScript && (
                                    <div className="vba-result">
                                        <div className="vba-header">
                                            <h3>Generated VBA Script</h3>
                                            <button
                                                onClick={handleDownloadVba}
                                                className="download-vba-button"
                                            >
                                                Download VBA File
                                            </button>
                                        </div>
                                        <div className="vba-code-container">
                                            <pre className="vba-code">{vbaScript}</pre>
                                        </div>
                                    </div>
                                )}
                            </div>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}

export default DimensionExtractor;
