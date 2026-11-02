import React from 'react';
import './LoadingOverlay.css';

const STEPS = [
  { icon: '📷', label: 'Reading image pixels...' },
  { icon: '🧠', label: 'Sending to Gemini Vision...' },
  { icon: '🔍', label: 'Identifying product features...' },
  { icon: '✍️', label: 'Generating descriptions...' },
  { icon: '📊', label: 'Structuring output...' },
];

export default function LoadingOverlay() {
  const [step, setStep] = React.useState(0);

  React.useEffect(() => {
    const interval = setInterval(() => {
      setStep((s) => (s + 1) % STEPS.length);
    }, 1800);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="loading-overlay" role="status" aria-live="polite">
      <div className="loading-card">
        {/* Spinner */}
        <div className="loading-spinner-wrap">
          <div className="loading-ring loading-ring-1" />
          <div className="loading-ring loading-ring-2" />
          <div className="loading-ring loading-ring-3" />
          <span className="loading-center-icon">🔮</span>
        </div>

        <h2 className="loading-title">Analyzing Product</h2>
        <p className="loading-subtitle">Gemini Vision is examining your image</p>

        {/* Step indicator */}
        <div className="loading-step">
          <span className="loading-step-icon">{STEPS[step].icon}</span>
          <span className="loading-step-label">{STEPS[step].label}</span>
        </div>

        {/* Progress dots */}
        <div className="loading-dots">
          {STEPS.map((_, i) => (
            <span key={i} className={`loading-dot ${i === step ? 'active' : i < step ? 'done' : ''}`} />
          ))}
        </div>
      </div>
    </div>
  );
}
