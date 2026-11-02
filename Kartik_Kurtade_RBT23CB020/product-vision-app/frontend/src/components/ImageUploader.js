import React, { useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import './ImageUploader.css';

const ACCEPTED_TYPES = {
  'image/jpeg': ['.jpg', '.jpeg'],
  'image/png': ['.png'],
  'image/webp': ['.webp'],
  'image/gif': ['.gif'],
};

const MAX_SIZE = 10 * 1024 * 1024; // 10 MB

export default function ImageUploader({
  onImageSelect, imagePreview, imageFile,
  onAnalyze, onReset, isLoading, error,
}) {
  const onDrop = useCallback((accepted, rejected) => {
    if (rejected.length > 0) {
      // Error is handled via dropzone's fileRejections
      return;
    }
    if (accepted.length > 0) {
      onImageSelect(accepted[0]);
    }
  }, [onImageSelect]);

  const { getRootProps, getInputProps, isDragActive, fileRejections } = useDropzone({
    onDrop,
    accept: ACCEPTED_TYPES,
    maxSize: MAX_SIZE,
    multiple: false,
    disabled: isLoading,
  });

  const rejectionError = fileRejections[0]?.errors[0];
  const dropError = rejectionError
    ? rejectionError.code === 'file-too-large'
      ? 'File is too large. Maximum size is 10MB.'
      : rejectionError.code === 'file-invalid-type'
      ? 'Invalid file type. Please upload JPG, PNG, WebP, or GIF.'
      : rejectionError.message
    : null;

  const displayError = error || dropError;

  return (
    <div className="uploader-page">
      {/* Hero */}
      <div className="hero">
        <div className="hero-pill">
          <span>✨</span>
          <span>AI-Powered Product Intelligence</span>
        </div>
        <h2 className="hero-title">
          Turn any product image into a
          <br />
          <span className="gradient-text">structured description</span>
        </h2>
        <p className="hero-subtitle">
          Upload a product photo and let Gemini Vision AI identify features,
          extract specifications, and generate SEO-ready product content — instantly.
        </p>
      </div>

      {/* Drop zone / Preview */}
      <div className="upload-area">
        {!imagePreview ? (
          <div
            {...getRootProps()}
            className={`dropzone ${isDragActive ? 'dropzone-active' : ''} ${isLoading ? 'dropzone-disabled' : ''}`}
          >
            <input {...getInputProps()} />
            <div className="dropzone-icon">
              <svg viewBox="0 0 48 48" fill="none" xmlns="http://www.w3.org/2000/svg">
                <rect x="6" y="10" width="36" height="28" rx="4" stroke="currentColor" strokeWidth="2" fill="none" />
                <circle cx="18" cy="20" r="4" stroke="currentColor" strokeWidth="2" fill="none" />
                <path d="M6 34l9-8 6 6 7-9 14 11" stroke="currentColor" strokeWidth="2" strokeLinejoin="round" />
                <path d="M32 6v12M26 9l6-3 6 3" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
              </svg>
            </div>
            <div className="dropzone-text">
              {isDragActive ? (
                <p className="dropzone-label active">Drop it here!</p>
              ) : (
                <>
                  <p className="dropzone-label">Drag & drop a product image</p>
                  <p className="dropzone-sublabel">or <span>click to browse</span></p>
                </>
              )}
              <p className="dropzone-hint">JPG, PNG, WebP, GIF — up to 10 MB</p>
            </div>
          </div>
        ) : (
          <div className="preview-container">
            <div className="preview-image-wrap">
              <img src={imagePreview} alt="Selected product" className="preview-image" />
              <div className="preview-overlay">
                <button className="preview-change-btn" onClick={onReset} disabled={isLoading}>
                  Change Image
                </button>
              </div>
            </div>
            <div className="preview-meta">
              <div className="preview-meta-row">
                <span className="meta-icon">📁</span>
                <span className="meta-text">{imageFile?.name}</span>
              </div>
              <div className="preview-meta-row">
                <span className="meta-icon">📐</span>
                <span className="meta-text">{(imageFile?.size / 1024).toFixed(1)} KB</span>
              </div>
              <div className="preview-meta-row">
                <span className="meta-icon">🖼️</span>
                <span className="meta-text">{imageFile?.type}</span>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Error */}
      {displayError && (
        <div className="error-banner" role="alert">
          <span className="error-icon">⚠️</span>
          <span>{displayError}</span>
        </div>
      )}

      {/* Analyze button */}
      {imagePreview && (
        <div className="action-row">
          <button
            className="analyze-btn"
            onClick={onAnalyze}
            disabled={isLoading || !imageFile}
          >
            {isLoading ? (
              <>
                <span className="btn-spinner" aria-hidden="true" />
                Analyzing with Gemini Vision...
              </>
            ) : (
              <>
                <span className="btn-icon">🔍</span>
                Analyze Product
              </>
            )}
          </button>
        </div>
      )}

      {/* Feature cards */}
      <div className="feature-grid">
        {[
          { icon: '🎯', title: 'Feature Detection', desc: 'Identifies colors, materials, design style, and all visible product attributes' },
          { icon: '📝', title: 'Rich Descriptions', desc: 'Generates short and long-form product descriptions ready for e-commerce listings' },
          { icon: '🏷️', title: 'SEO Keywords', desc: 'Extracts relevant search keywords to boost product discoverability' },
          { icon: '📊', title: 'Specifications', desc: 'Extracts visible specs, components, labels, and use-case information' },
        ].map((f) => (
          <div key={f.title} className="feature-card">
            <span className="feature-card-icon">{f.icon}</span>
            <h3 className="feature-card-title">{f.title}</h3>
            <p className="feature-card-desc">{f.desc}</p>
          </div>
        ))}
      </div>
    </div>
  );
}
