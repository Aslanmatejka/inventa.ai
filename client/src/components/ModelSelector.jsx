import React, { useState, useEffect, useRef } from 'react';
import { API_BASE } from '../config';
import { authFetch } from '../api';
import './ModelSelector.css';

const TIER_ICONS = {
  flagship: (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2" />
    </svg>
  ),
  standard: (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <circle cx="12" cy="12" r="10" />
      <polyline points="12 6 12 12 16 14" />
    </svg>
  ),
  fast: (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2" />
    </svg>
  ),
};

const TIER_COLORS = {
  flagship: '#f59e0b',
  standard: '#3b82f6',
  fast: '#10b981',
};

const PROVIDER_COLORS = {
  Anthropic: '#d4a27a',
  OpenAI: '#10a37f',
};

export default function ModelSelector({ selectedModel, onModelChange }) {
  const [models, setModels] = useState([]);
  const [defaultModel, setDefaultModel] = useState('');
  const [open, setOpen] = useState(false);
  const [dropdownPos, setDropdownPos] = useState(null);
  const ref = useRef(null);
  const triggerRef = useRef(null);

  // Fetch available models on mount
  useEffect(() => {
    authFetch(`${API_BASE}/models`)
      .then((r) => r.json())
      .then((data) => {
        setModels(data.models || []);
        setDefaultModel(data.default || '');
        if (!selectedModel) {
          onModelChange(data.default || data.models?.[0]?.id || '');
        }
      })
      .catch(() => {
        // Fallback if endpoint not available yet
        const fallback = [
          { id: 'claude-opus-4-6', name: 'Claude Opus 4.6', provider: 'Anthropic', tier: 'flagship', description: 'Latest & most powerful' },
          { id: 'claude-opus-4-20250514', name: 'Claude Opus 4', provider: 'Anthropic', tier: 'flagship', description: 'Proven flagship' },
          { id: 'claude-sonnet-4-6', name: 'Claude Sonnet 4.6', provider: 'Anthropic', tier: 'standard', description: 'Fast & highly capable' },
          { id: 'claude-sonnet-4-20250514', name: 'Claude Sonnet 4', provider: 'Anthropic', tier: 'standard', description: 'Balanced speed & quality' },
          { id: 'gpt-4.1-2025-04-14', name: 'GPT-4.1', provider: 'OpenAI', tier: 'flagship', description: 'Flagship GPT' },
          { id: 'gpt-4.1-mini-2025-04-14', name: 'GPT-4.1 Mini', provider: 'OpenAI', tier: 'standard', description: 'Fast & affordable' },
          { id: 'gpt-4.1-nano-2025-04-14', name: 'GPT-4.1 Nano', provider: 'OpenAI', tier: 'fast', description: 'Ultra-fast' },
        ];
        setModels(fallback);
        setDefaultModel('claude-opus-4-6');
        if (!selectedModel) onModelChange('claude-opus-4-6');
      });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Close on outside click
  useEffect(() => {
    const handler = (e) => {
      if (ref.current && !ref.current.contains(e.target)) setOpen(false);
    };
    document.addEventListener('mousedown', handler);
    return () => document.removeEventListener('mousedown', handler);
  }, []);

  const current = models.find((m) => m.id === selectedModel) || models[0];
  if (!current) return null;

  // Group models by provider
  const providers = [];
  const seen = new Set();
  for (const m of models) {
    const p = m.provider || 'Anthropic';
    if (!seen.has(p)) { seen.add(p); providers.push(p); }
  }

  return (
    <div className="model-selector" ref={ref}>
      <button
        ref={triggerRef}
        className="model-selector-trigger"
        onClick={() => {
          if (!open && triggerRef.current) {
            const rect = triggerRef.current.getBoundingClientRect();
            setDropdownPos({ left: rect.left, bottom: window.innerHeight - rect.top + 6 });
          }
          setOpen(!open);
        }}
        title="Switch AI model"
      >
        <span className="model-selector-icon" style={{ color: TIER_COLORS[current.tier] || '#8b949e' }}>
          {TIER_ICONS[current.tier] || TIER_ICONS.standard}
        </span>
        <span className="model-selector-name">{current.name}</span>
        {current.provider && (
          <span className="model-provider-pill" style={{ background: `${PROVIDER_COLORS[current.provider] || '#636e7b'}20`, color: PROVIDER_COLORS[current.provider] || '#636e7b' }}>
            {current.provider}
          </span>
        )}
        <svg className={`model-selector-chevron ${open ? 'open' : ''}`} width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
          <polyline points="6 9 12 15 18 9" />
        </svg>
      </button>

      {open && dropdownPos && (
        <div className="model-selector-dropdown" style={{ position: 'fixed', left: dropdownPos.left, bottom: dropdownPos.bottom }}>
          <div className="model-dropdown-header">Select AI Model</div>
          {providers.map((provider) => (
            <React.Fragment key={provider}>
              <div className="model-provider-section" style={{ color: PROVIDER_COLORS[provider] || '#636e7b' }}>
                {provider}
              </div>
              {models.filter((m) => (m.provider || 'Anthropic') === provider).map((m) => (
                <button
                  key={m.id}
                  className={`model-option ${m.id === selectedModel ? 'active' : ''}`}
                  onClick={() => {
                    onModelChange(m.id);
                    setOpen(false);
                  }}
                >
                  <span className="model-option-icon" style={{ color: TIER_COLORS[m.tier] || '#8b949e' }}>
                    {TIER_ICONS[m.tier] || TIER_ICONS.standard}
                  </span>
                  <div className="model-option-info">
                    <span className="model-option-name">
                      {m.name}
                      {m.id === defaultModel && <span className="model-default-badge">default</span>}
                    </span>
                    <span className="model-option-desc">{m.description}</span>
                  </div>
                  {m.id === selectedModel && (
                    <svg className="model-option-check" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                      <polyline points="20 6 9 17 4 12" />
                    </svg>
                  )}
                </button>
              ))}
            </React.Fragment>
          ))}
        </div>
      )}
    </div>
  );
}
