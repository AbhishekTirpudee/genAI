import React from 'react';
import './Header.css';

export default function Header() {
  return (
    <header className="header">
      <div className="header-inner">
        <div className="header-brand">
          <div className="brand-icon" aria-hidden="true">
            <svg viewBox="0 0 32 32" fill="none" xmlns="http://www.w3.org/2000/svg">
              <rect width="32" height="32" rx="8" fill="url(#grad)" />
              <path d="M8 16a8 8 0 1 1 16 0A8 8 0 0 1 8 16Z" stroke="white" strokeWidth="1.5" fill="none" />
              <circle cx="16" cy="16" r="3.5" fill="white" />
              <path d="M16 10V8M16 24v-2M10 16H8M24 16h-2" stroke="white" strokeWidth="1.5" strokeLinecap="round" />
              <defs>
                <linearGradient id="grad" x1="0" y1="0" x2="32" y2="32" gradientUnits="userSpaceOnUse">
                  <stop stopColor="#6366f1" />
                  <stop offset="1" stopColor="#8b5cf6" />
                </linearGradient>
              </defs>
            </svg>
          </div>
          <div className="brand-text">
            <h1 className="brand-name">ProductVision <span>AI</span></h1>
            <p className="brand-tagline">Powered by Gemini Vision</p>
          </div>
        </div>

        <nav className="header-badges">
          <span className="badge badge-model">
            <span className="badge-dot" />
            gemini-3.5-flash
          </span>
          <span className="badge badge-feature">Vision Analysis</span>
          <span className="badge badge-feature">Structured Output</span>
        </nav>
      </div>
    </header>
  );
}
