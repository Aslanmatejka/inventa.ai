import React, { useState, useRef, useEffect } from 'react';
import './CodeView.css';

/* Minimal CadQuery/Python syntax highlighter — no external deps */
function highlightPython(code) {
  if (!code) return '';
  // Escape HTML first
  let html = code
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;');

  // Comments
  html = html.replace(/(#.*$)/gm, '<span class="cv-comment">$1</span>');
  // Strings (double and single, multiline handled minimally)
  html = html.replace(/("""[\s\S]*?"""|'''[\s\S]*?'''|"(?:[^"\\]|\\.)*"|'(?:[^'\\]|\\.)*')/g, '<span class="cv-string">$1</span>');
  // Keywords
  html = html.replace(/\b(import|from|as|def|class|return|if|elif|else|for|while|in|not|and|or|is|None|True|False|try|except|pass|with|lambda|raise|break|continue|yield)\b/g, '<span class="cv-keyword">$1</span>');
  // Numbers
  html = html.replace(/\b(\d+\.?\d*)\b/g, '<span class="cv-number">$1</span>');
  // Built-in functions / CadQuery methods
  html = html.replace(/\.(box|cylinder|sphere|extrude|cut|union|fillet|chamfer|shell|translate|rotate|workplane|center|rect|circle|slot2D|pushPoints|rarray|faces|edges|vertices|val|close|revolve|loft|sweep|transformed|moveTo|lineTo|threePointArc|sagittaArc|spline|cutBlind|cutThruAll)\b/g, '.<span class="cv-method">$1</span>');
  // CadQuery namespace
  html = html.replace(/\b(cq|cadquery|math|result|body|np|numpy)\b/g, '<span class="cv-builtin">$1</span>');
  // Decorators / special
  html = html.replace(/\b(Workplane|Solid|Compound|Shape|Assembly)\b/g, '<span class="cv-class">$1</span>');

  return html;
}

function CodeView({ code, isBuilding, buildPhase, onClose }) {
  const [copied, setCopied] = useState(false);
  const [wordWrap, setWordWrap] = useState(false);
  const codeRef = useRef(null);

  // Auto-scroll to bottom when code changes during build
  useEffect(() => {
    if (isBuilding && codeRef.current) {
      codeRef.current.scrollTop = codeRef.current.scrollHeight;
    }
  }, [code, isBuilding]);

  const handleCopy = () => {
    if (!code) return;
    navigator.clipboard.writeText(code).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    });
  };

  const lines = code ? code.split('\n') : [];
  const lineCount = lines.length;

  // Determine file status indicator
  let fileStatus = null;
  if (isBuilding && buildPhase) {
    if (buildPhase <= 2) fileStatus = { icon: 'M', label: 'Generating...', color: '#f59e0b' };
    else if (buildPhase <= 3) fileStatus = { icon: 'M', label: 'Validating...', color: '#3b82f6' };
    else if (buildPhase <= 4) fileStatus = { icon: 'M', label: 'Executing...', color: '#8b5cf6' };
    else fileStatus = { icon: 'M', label: 'Exporting...', color: '#34d399' };
  } else if (code) {
    fileStatus = { icon: '', label: '', color: '#34d399' };
  }

  return (
    <div className="code-view">
      {/* Tab bar — VS Code style */}
      <div className="cv-tab-bar">
        <div className="cv-tab active">
          <svg className="cv-tab-icon" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#3b82f6" strokeWidth="2">
            <path d="M13 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V9z"/>
            <polyline points="13 2 13 9 20 9"/>
          </svg>
          <span className="cv-tab-name">design.py</span>
          {fileStatus && fileStatus.icon && (
            <span className="cv-tab-status" style={{ color: fileStatus.color }}>
              {fileStatus.icon}
            </span>
          )}
          {isBuilding && <span className="cv-tab-building-dot" />}
        </div>
        <div className="cv-tab-spacer" />

        <div className="cv-toolbar">
          <button
            className={`cv-toolbar-btn ${wordWrap ? 'active' : ''}`}
            onClick={() => setWordWrap(!wordWrap)}
            title="Toggle word wrap"
          >
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M3 6h18M3 12h15a3 3 0 1 1 0 6h-4M3 18h7"/>
              <polyline points="13 15 10 18 13 21"/>
            </svg>
          </button>
          <button
            className="cv-toolbar-btn"
            onClick={handleCopy}
            title={copied ? 'Copied!' : 'Copy code'}
          >
            {copied ? (
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#34d399" strokeWidth="2">
                <polyline points="20 6 9 17 4 12"/>
              </svg>
            ) : (
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <rect x="9" y="9" width="13" height="13" rx="2" ry="2"/>
                <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/>
              </svg>
            )}
          </button>
          <button className="cv-toolbar-btn cv-close-btn" onClick={onClose} title="Close code view">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>
            </svg>
          </button>
        </div>
      </div>

      {/* Breadcrumb bar */}
      {code && (
        <div className="cv-breadcrumb">
          <span className="cv-breadcrumb-item">exports</span>
          <span className="cv-breadcrumb-sep">/</span>
          <span className="cv-breadcrumb-item">cad</span>
          <span className="cv-breadcrumb-sep">/</span>
          <span className="cv-breadcrumb-item active">design.py</span>
          <span className="cv-breadcrumb-info">{lineCount} lines</span>
          {isBuilding && fileStatus && (
            <span className="cv-breadcrumb-status" style={{ color: fileStatus.color }}>
              {fileStatus.label}
            </span>
          )}
        </div>
      )}

      {/* Code editor area */}
      <div className={`cv-editor ${wordWrap ? 'word-wrap' : ''}`} ref={codeRef}>
        {!code ? (
          <div className="cv-empty">
            <svg width="36" height="36" viewBox="0 0 24 24" fill="none" stroke="#4b5563" strokeWidth="1.5">
              <polyline points="16 18 22 12 16 6"/>
              <polyline points="8 6 2 12 8 18"/>
            </svg>
            <span>No code generated yet</span>
            <span className="cv-empty-hint">Build something to see the CadQuery code here</span>
          </div>
        ) : (
          <table className="cv-code-table">
            <tbody>
              {lines.map((line, i) => (
                <tr key={i} className="cv-line">
                  <td className="cv-line-num">{i + 1}</td>
                  <td
                    className="cv-line-code"
                    dangerouslySetInnerHTML={{ __html: highlightPython(line) || '&nbsp;' }}
                  />
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {/* Status bar — VS Code style */}
      <div className="cv-status-bar">
        <span className="cv-status-item">Python</span>
        <span className="cv-status-item">CadQuery</span>
        <span className="cv-status-item">{lineCount} lines</span>
        {isBuilding && (
          <span className="cv-status-item cv-status-building">
            <span className="cv-status-dot" />
            AI is writing...
          </span>
        )}
      </div>
    </div>
  );
}

export default CodeView;
