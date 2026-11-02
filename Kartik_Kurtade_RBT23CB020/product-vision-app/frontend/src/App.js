import React, { useState, useCallback } from 'react';
import axios from 'axios';
import Header from './components/Header';
import ImageUploader from './components/ImageUploader';
import AnalysisResults from './components/AnalysisResults';
import LoadingOverlay from './components/LoadingOverlay';
import './App.css';

const API_BASE = process.env.REACT_APP_API_URL || 'http://localhost:5000';

function App() {
  const [imageFile, setImageFile] = useState(null);
  const [imagePreview, setImagePreview] = useState(null);
  const [analysis, setAnalysis] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [imageSizeKb, setImageSizeKb] = useState(null);

  const handleImageSelect = useCallback((file) => {
    setImageFile(file);
    setAnalysis(null);
    setError(null);
    setImageSizeKb(null);

    const reader = new FileReader();
    reader.onload = (e) => setImagePreview(e.target.result);
    reader.readAsDataURL(file);
  }, []);

  const handleAnalyze = async () => {
    if (!imageFile) return;

    setIsLoading(true);
    setError(null);
    setAnalysis(null);

    try {
      const formData = new FormData();
      formData.append('image', imageFile);

      const response = await axios.post(`${API_BASE}/analyze`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
        timeout: 60000,
      });

      if (response.data.success) {
        setAnalysis(response.data.analysis);
        setImageSizeKb(response.data.image_size_kb);
      } else {
        setError(response.data.error || 'Analysis failed. Please try again.');
      }
    } catch (err) {
      if (err.response?.data?.error) {
        setError(err.response.data.error);
      } else if (err.code === 'ECONNABORTED') {
        setError('Request timed out. The image may be too complex. Please try again.');
      } else if (err.code === 'ERR_NETWORK') {
        setError('Cannot connect to the server. Make sure the backend is running on port 5000.');
      } else {
        setError('An unexpected error occurred. Please try again.');
      }
    } finally {
      setIsLoading(false);
    }
  };

  const handleReset = () => {
    setImageFile(null);
    setImagePreview(null);
    setAnalysis(null);
    setError(null);
    setImageSizeKb(null);
  };

  return (
    <div className="app">
      {/* Animated background */}
      <div className="bg-orbs" aria-hidden="true">
        <div className="orb orb-1" />
        <div className="orb orb-2" />
        <div className="orb orb-3" />
      </div>

      <Header />

      <main className="main-content">
        <div className="container">
          {!analysis ? (
            <ImageUploader
              onImageSelect={handleImageSelect}
              imagePreview={imagePreview}
              imageFile={imageFile}
              onAnalyze={handleAnalyze}
              onReset={handleReset}
              isLoading={isLoading}
              error={error}
            />
          ) : (
            <AnalysisResults
              analysis={analysis}
              imagePreview={imagePreview}
              imageSizeKb={imageSizeKb}
              onReset={handleReset}
            />
          )}
        </div>
      </main>

      {isLoading && <LoadingOverlay />}
    </div>
  );
}

export default App;
