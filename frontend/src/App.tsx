import React, { useState, ChangeEvent, FormEvent } from 'react';
import axios, { AxiosError } from 'axios';
import './App.css';

// Define types for our state
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

// Define the expected response type from the backend
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

function App() {
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

  const handleFileChange = (e: ChangeEvent<HTMLInputElement>) => {
    const { name, files: selectedFiles } = e.target;
    if (selectedFiles && selectedFiles[0]) {
      const file = selectedFiles[0];
      setFiles(prev => ({ ...prev, [name]: file }));

      // Create preview
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

    try {
      const formData = new FormData();
      for (const [key, value] of Object.entries(files)) {
        if (value) {
          formData.append(key, value);
        }
      }

      // Send to your Flask backend
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

  const allFilesSelected = Object.values(files).every(file => file !== null);

  return (
    <div className="app-container">
      <h1>Engineering Drawing Dimension Extractor</h1>
      
      <form onSubmit={handleSubmit} className="upload-form">
        <div className="file-upload-section">
          <h2>Upload Engineering Drawing Views</h2>
          
          <div className="file-inputs">
            <div className="file-input-group">
              <label htmlFor="top_view">Top View:</label>
              <input
                type="file"
                id="top_view"
                name="top_view"
                accept="image/*"
                onChange={handleFileChange}
                required
              />
              {previews.top_view && (
                <div className="image-preview">
                  <img src={previews.top_view} alt="Top view preview" />
                </div>
              )}
            </div>

            <div className="file-input-group">
              <label htmlFor="front_view">Front View:</label>
              <input
                type="file"
                id="front_view"
                name="front_view"
                accept="image/*"
                onChange={handleFileChange}
                required
              />
              {previews.front_view && (
                <div className="image-preview">
                  <img src={previews.front_view} alt="Front view preview" />
                </div>
              )}
            </div>

            <div className="file-input-group">
              <label htmlFor="side_view">Side View:</label>
              <input
                type="file"
                id="side_view"
                name="side_view"
                accept="image/*"
                onChange={handleFileChange}
                required
              />
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
            className="submit-button"
          >
            {isLoading ? 'Processing...' : 'Extract Dimensions'}
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
          <h2>Extracted Dimensions</h2>
          <div className="result-display">
            <pre>{JSON.stringify(result, null, 2)}</pre>
          </div>
        </div>
      )}
    </div>
  );
}

export default App;