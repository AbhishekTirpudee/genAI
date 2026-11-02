import React, { useState } from 'react';
import './AnalysisResults.css';

/* ─── Small reusable pieces ─── */

function Section({ icon, title, children, accent }) {
  return (
    <section className={`result-section ${accent ? 'result-section--accent' : ''}`}>
      <h3 className="section-title">
        <span className="section-icon">{icon}</span>
        {title}
      </h3>
      {children}
    </section>
  );
}

function Tag({ label, variant = 'default' }) {
  return <span className={`tag tag-${variant}`}>{label}</span>;
}

function KeyValueRow({ label, value }) {
  if (!value) return null;
  return (
    <div className="kv-row">
      <span className="kv-label">{label}</span>
      <span className="kv-value">{value}</span>
    </div>
  );
}

function ScoreBar({ score }) {
  const pct = Math.round((score || 0) * 100);
  const color = pct >= 85 ? '#10b981' : pct >= 65 ? '#f59e0b' : '#ef4444';
  return (
    <div className="score-bar-wrap">
      <div className="score-bar-track">
        <div
          className="score-bar-fill"
          style={{ width: `${pct}%`, background: color }}
        />
      </div>
      <span className="score-label" style={{ color }}>{pct}%</span>
    </div>
  );
}

/* ─── Copy to clipboard ─── */
function CopyButton({ text }) {
  const [copied, setCopied] = useState(false);
  const copy = async () => {
    try {
      await navigator.clipboard.writeText(text);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      // fallback ignored
    }
  };
  return (
    <button className="copy-btn" onClick={copy} title="Copy to clipboard">
      {copied ? '✅ Copied!' : '📋 Copy'}
    </button>
  );
}

/* ─── Main component ─── */

export default function AnalysisResults({ analysis, imagePreview, imageSizeKb, onReset }) {
  const a = analysis;
  if (!a) return null;

  const longDesc = a.long_description || a.short_description || '';

  return (
    <div className="results-page">

      {/* Top bar */}
      <div className="results-topbar">
        <button className="back-btn" onClick={onReset}>
          ← Analyze Another Product
        </button>
        <div className="topbar-right">
          {imageSizeKb && (
            <span className="meta-chip">📁 {imageSizeKb} KB processed</span>
          )}
          <span className="meta-chip">✅ Analysis complete</span>
        </div>
      </div>

      {/* Two-column layout */}
      <div className="results-grid">

        {/* Left: image + quick summary */}
        <aside className="results-sidebar">

          {/* Product image */}
          <div className="sidebar-image-card">
            <img src={imagePreview} alt="Analyzed product" className="sidebar-image" />
            {a.condition_assessment && (
              <div className="condition-badge">{a.condition_assessment}</div>
            )}
          </div>

          {/* Quick stats */}
          <div className="sidebar-card">
            <h3 className="sidebar-card-title">Analysis Confidence</h3>
            <ScoreBar score={a.confidence_score} />
          </div>

          {a.category && (
            <div className="sidebar-card">
              <h3 className="sidebar-card-title">Classification</h3>
              <KeyValueRow label="Category" value={a.category} />
              <KeyValueRow label="Subcategory" value={a.subcategory} />
              <KeyValueRow label="Brand" value={a.brand} />
            </div>
          )}

          {a.suggested_price_range && (
            <div className="sidebar-card price-card">
              <h3 className="sidebar-card-title">💰 Estimated Price</h3>
              <p className="price-value">{a.suggested_price_range}</p>
            </div>
          )}

          {a.target_audience && (
            <div className="sidebar-card">
              <h3 className="sidebar-card-title">🎯 Target Audience</h3>
              <p className="sidebar-card-body">{a.target_audience}</p>
            </div>
          )}

        </aside>

        {/* Right: detailed analysis */}
        <main className="results-main">

          {/* Product name & tagline */}
          <div className="product-header-card">
            <div className="product-header-top">
              <h1 className="product-name">{a.product_name || 'Product Analysis'}</h1>
              {a.brand && a.brand !== 'Unknown' && (
                <span className="brand-chip">{a.brand}</span>
              )}
            </div>
            {a.tagline && <p className="product-tagline">"{a.tagline}"</p>}
          </div>

          {/* Short description */}
          {a.short_description && (
            <Section icon="📋" title="Product Overview">
              <p className="description-text">{a.short_description}</p>
            </Section>
          )}

          {/* Long description with copy */}
          {a.long_description && (
            <Section icon="📝" title="Full Product Description">
              <p className="description-text">{a.long_description}</p>
              <CopyButton text={longDesc} />
            </Section>
          )}

          {/* Visual Features */}
          {a.visual_features && (
            <Section icon="🎨" title="Visual Features">
              <div className="kv-grid">
                <KeyValueRow label="Primary Color" value={a.visual_features.primary_color} />
                <KeyValueRow label="Material" value={a.visual_features.material} />
                <KeyValueRow label="Finish" value={a.visual_features.finish} />
                <KeyValueRow label="Shape" value={a.visual_features.shape} />
                <KeyValueRow label="Design Style" value={a.visual_features.design_style} />
                <KeyValueRow label="Size Estimate" value={a.visual_features.size_estimate} />
              </div>
              {Array.isArray(a.visual_features.secondary_colors) && a.visual_features.secondary_colors.length > 0 && (
                <div className="tags-row" style={{ marginTop: '0.75rem' }}>
                  <span className="kv-label">Secondary Colors:</span>
                  {a.visual_features.secondary_colors.map((c) => (
                    <Tag key={c} label={c} variant="color" />
                  ))}
                </div>
              )}
            </Section>
          )}

          {/* Key features */}
          {Array.isArray(a.key_features) && a.key_features.length > 0 && (
            <Section icon="⭐" title="Key Features">
              <ul className="feature-list">
                {a.key_features.map((f, i) => (
                  <li key={i} className="feature-list-item">
                    <span className="feature-bullet">{i + 1}</span>
                    <span>{f}</span>
                  </li>
                ))}
              </ul>
            </Section>
          )}

          {/* Specifications */}
          {a.specifications && (
            <Section icon="🔧" title="Specifications">
              <div className="kv-grid">
                <KeyValueRow label="Dimensions" value={a.specifications.visible_dimensions} />
                <KeyValueRow label="Labels/Text" value={a.specifications.visible_labels_text} />
                <KeyValueRow label="Connectivity" value={a.specifications.connectivity} />
                <KeyValueRow label="Packaging" value={a.specifications.packaging} />
              </div>
              {Array.isArray(a.specifications.visible_components) && a.specifications.visible_components.length > 0 && (
                <div className="tags-row" style={{ marginTop: '0.75rem' }}>
                  <span className="kv-label">Components:</span>
                  {a.specifications.visible_components.map((c) => (
                    <Tag key={c} label={c} variant="spec" />
                  ))}
                </div>
              )}
            </Section>
          )}

          {/* Use cases */}
          {Array.isArray(a.use_cases) && a.use_cases.length > 0 && (
            <Section icon="💡" title="Use Cases">
              <div className="use-cases-grid">
                {a.use_cases.map((u, i) => (
                  <div key={i} className="use-case-card">
                    <span className="use-case-num">{i + 1}</span>
                    <span>{u}</span>
                  </div>
                ))}
              </div>
            </Section>
          )}

          {/* USPs */}
          {Array.isArray(a.unique_selling_points) && a.unique_selling_points.length > 0 && (
            <Section icon="🏆" title="Unique Selling Points">
              <div className="usp-list">
                {a.unique_selling_points.map((u, i) => (
                  <div key={i} className="usp-item">
                    <span className="usp-check">✓</span>
                    <span>{u}</span>
                  </div>
                ))}
              </div>
            </Section>
          )}

          {/* SEO Keywords */}
          {Array.isArray(a.seo_keywords) && a.seo_keywords.length > 0 && (
            <Section icon="🔍" title="SEO Keywords">
              <div className="tags-row">
                {a.seo_keywords.map((k) => (
                  <Tag key={k} label={k} variant="seo" />
                ))}
              </div>
              <CopyButton text={a.seo_keywords.join(', ')} />
            </Section>
          )}

          {/* Quality */}
          {a.quality_indicators && (
            <Section icon="🔬" title="Quality Assessment">
              <p className="description-text">{a.quality_indicators}</p>
            </Section>
          )}

        </main>
      </div>
    </div>
  );
}
