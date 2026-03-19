import React, { useState, useRef, useEffect } from 'react';
import ModelSelector from './ModelSelector';
import './PromptInput.css';

/* ── Mode definitions (Agent / Ask / Plan) ── */
const MODES = [
  {
    id: 'agent',
    label: 'Agent',
    icon: (
      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <path d="M12 8V4H8"/>
        <rect x="2" y="2" width="20" height="20" rx="5"/>
        <path d="M2 12h20"/>
        <path d="M12 2v20"/>
      </svg>
    ),
    description: 'Build & modify CAD designs autonomously',
    placeholder: 'Ask Agent to build something...',
  },
  {
    id: 'ask',
    label: 'Ask',
    icon: (
      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <circle cx="12" cy="12" r="10"/>
        <path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3"/>
        <line x1="12" y1="17" x2="12.01" y2="17"/>
      </svg>
    ),
    description: 'Ask questions about your design or CAD',
    placeholder: 'Ask a question about your design...',
  },
  {
    id: 'plan',
    label: 'Plan',
    icon: (
      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
        <polyline points="14 2 14 8 20 8"/>
        <line x1="16" y1="13" x2="8" y2="13"/>
        <line x1="16" y1="17" x2="8" y2="17"/>
        <polyline points="10 9 9 9 8 9"/>
      </svg>
    ),
    description: 'Plan a complex design step by step',
    placeholder: 'Describe a design to plan...',
  },
];

const MODE_COLORS = {
  agent: '#3b82f6',
  ask: '#a78bfa',
  plan: '#f59e0b',
};

function PromptInput({ onBuild, isBuilding, hasExistingDesign, uploadedFile, selectedModel, onModelChange, interactionMode, onModeChange }) {
  const [prompt, setPrompt] = useState('');
  const [modeMenuOpen, setModeMenuOpen] = useState(false);
  const [modeMenuPos, setModeMenuPos] = useState(null);
  const textareaRef = useRef(null);
  const modeRef = useRef(null);
  const modeTriggerRef = useRef(null);

  // Auto-resize textarea
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = Math.min(textareaRef.current.scrollHeight, 200) + 'px';
    }
  }, [prompt]);

  // Close mode menu on outside click
  useEffect(() => {
    const handler = (e) => {
      if (modeRef.current && !modeRef.current.contains(e.target)) setModeMenuOpen(false);
    };
    document.addEventListener('mousedown', handler);
    return () => document.removeEventListener('mousedown', handler);
  }, []);

  const handleSubmit = (e) => {
    if (e) e.preventDefault();
    if (prompt.trim() && !isBuilding) {
      onBuild(prompt);
      setPrompt('');
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  const currentMode = MODES.find((m) => m.id === interactionMode) || MODES[0];
  const modeColor = MODE_COLORS[currentMode.id] || '#3b82f6';

  const placeholder = uploadedFile
    ? `Edit ${uploadedFile.filename} — describe changes...`
    : hasExistingDesign
      ? "Describe what to change..."
      : currentMode.placeholder;

  return (
    <div className="prompt-input">
      {uploadedFile && (
        <div className="prompt-upload-badge">
          <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
            <polyline points="14 2 14 8 20 8"/>
          </svg>
          <span>{uploadedFile.filename}</span>
          {uploadedFile.editable && <span className="badge-editable">NLP editable</span>}
        </div>
      )}
      <form onSubmit={handleSubmit}>
        <div className="input-box" style={{ '--mode-color': modeColor }}>
          {/* ── Top: Textarea + Send ── */}
          <div className="input-area">
            <textarea
              ref={textareaRef}
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder={placeholder}
              rows={1}
              disabled={isBuilding}
            />
          </div>

          {/* ── Bottom toolbar ── */}
          <div className="input-bottom-bar">
            <div className="input-bottom-left">
              {/* Mode selector */}
              <div className="mode-selector" ref={modeRef}>
                <button
                  ref={modeTriggerRef}
                  type="button"
                  className="mode-trigger"
                  onClick={() => {
                    if (!modeMenuOpen && modeTriggerRef.current) {
                      const rect = modeTriggerRef.current.getBoundingClientRect();
                      setModeMenuPos({ left: rect.left, bottom: window.innerHeight - rect.top + 6 });
                    }
                    setModeMenuOpen(!modeMenuOpen);
                  }}
                  style={{ color: modeColor }}
                >
                  {currentMode.icon}
                  <span className="mode-label">{currentMode.label}</span>
                  <svg className={`mode-chevron ${modeMenuOpen ? 'open' : ''}`} width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                    <polyline points="6 9 12 15 18 9" />
                  </svg>
                </button>

                {modeMenuOpen && modeMenuPos && (
                  <div className="mode-dropdown" style={{ position: 'fixed', left: modeMenuPos.left, bottom: modeMenuPos.bottom }}>
                    {MODES.map((mode) => (
                      <button
                        key={mode.id}
                        type="button"
                        className={`mode-option ${mode.id === currentMode.id ? 'active' : ''}`}
                        onClick={() => {
                          onModeChange(mode.id);
                          setModeMenuOpen(false);
                        }}
                      >
                        <span className="mode-option-icon" style={{ color: MODE_COLORS[mode.id] }}>
                          {mode.icon}
                        </span>
                        <div className="mode-option-info">
                          <span className="mode-option-name">{mode.label}</span>
                          <span className="mode-option-desc">{mode.description}</span>
                        </div>
                        {mode.id === currentMode.id && (
                          <svg className="mode-option-check" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                            <polyline points="20 6 9 17 4 12" />
                          </svg>
                        )}
                      </button>
                    ))}
                  </div>
                )}
              </div>

              <span className="toolbar-divider" />

              {/* Model selector */}
              <ModelSelector
                selectedModel={selectedModel}
                onModelChange={onModelChange}
              />
            </div>

            <div className="input-bottom-right">
              <span className="input-hint-text"><kbd>Enter</kbd> send · <kbd>Shift+Enter</kbd> newline</span>
              <button
                type="submit"
                disabled={!prompt.trim() || isBuilding}
                className="send-button"
                title={isBuilding ? 'Building...' : 'Send (Enter)'}
              >
                {isBuilding ? (
                  <span className="send-spinner"></span>
                ) : (
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <line x1="22" y1="2" x2="11" y2="13"></line>
                    <polygon points="22 2 15 22 11 13 2 9 22 2"></polygon>
                  </svg>
                )}
              </button>
            </div>
          </div>
        </div>
      </form>
    </div>
  );
}

export default PromptInput;
