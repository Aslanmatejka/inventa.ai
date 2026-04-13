import React, { useState } from 'react';
import { API_HOST } from '../config';
import { searchPCBComponents, getPCBCategories, generatePCBEnclosure } from '../api';
import './PCBPanel.css';

/**
 * PCBPanel — Displays PCB design results alongside the 3D model.
 * Shows board dimensions, component list, download links, enclosure specs,
 * component browser, and enclosure generation.
 */
const PCBPanel = ({ pcbResult, onClose, buildId }) => {
  const [showBrowser, setShowBrowser] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState([]);
  const [categories, setCategories] = useState([]);
  const [selectedCategory, setSelectedCategory] = useState('');
  const [searching, setSearching] = useState(false);
  const [generatingEnclosure, setGeneratingEnclosure] = useState(false);
  const [enclosureResult, setEnclosureResult] = useState(null);

  if (!pcbResult) return null;

  const {
    boardDimensions = {},
    componentList = [],
    enclosureSpec = {},
    kicadFile,
    stlFile,
    stepFile,
  } = pcbResult;

  const cutouts = enclosureSpec.connectorCutouts || [];

  // ── Component Search ──
  const handleSearch = async () => {
    setSearching(true);
    try {
      const results = await searchPCBComponents(searchQuery, selectedCategory);
      setSearchResults(results.components || []);
    } catch (err) {
      console.error('Component search failed:', err);
    } finally {
      setSearching(false);
    }
  };

  const handleLoadCategories = async () => {
    try {
      const data = await getPCBCategories();
      setCategories(data.categories || []);
    } catch (err) {
      console.error('Failed to load categories:', err);
    }
  };

  const handleToggleBrowser = () => {
    const next = !showBrowser;
    setShowBrowser(next);
    if (next && categories.length === 0) {
      handleLoadCategories();
    }
  };

  // ── Enclosure Generation ──
  const handleGenerateEnclosure = async () => {
    if (!pcbResult) return;
    setGeneratingEnclosure(true);
    try {
      const result = await generatePCBEnclosure({
        boardDimensions: pcbResult.boardDimensions,
        componentList: pcbResult.componentList,
        enclosureSpec: pcbResult.enclosureSpec,
        buildId: buildId,
      });
      setEnclosureResult(result);
    } catch (err) {
      console.error('Enclosure generation failed:', err);
    } finally {
      setGeneratingEnclosure(false);
    }
  };

  return (
    <div className="pcb-panel">
      {/* Header */}
      <div className="pcb-panel__header">
        <span className="pcb-panel__icon">🔌</span>
        <span className="pcb-panel__title">PCB Design</span>
        <span className="pcb-panel__badge">
          {componentList.length} components
        </span>
        {onClose && (
          <button className="pcb-panel__close" onClick={onClose} title="Close PCB panel">✕</button>
        )}
      </div>

      {/* Board Dimensions */}
      <div className="pcb-panel__board">
        <div className="pcb-panel__board-title">Board</div>
        <div className="pcb-panel__board-dims">
          <div className="pcb-panel__dim">
            <span className="pcb-panel__dim-value">
              {boardDimensions.width || '?'}
            </span>
            <span className="pcb-panel__dim-label">Width (mm)</span>
          </div>
          <div className="pcb-panel__dim">
            <span className="pcb-panel__dim-value">
              {boardDimensions.height || '?'}
            </span>
            <span className="pcb-panel__dim-label">Height (mm)</span>
          </div>
          <div className="pcb-panel__dim">
            <span className="pcb-panel__dim-value">
              {boardDimensions.thickness || 1.6}
            </span>
            <span className="pcb-panel__dim-label">Thickness</span>
          </div>
          <div className="pcb-panel__dim">
            <span className="pcb-panel__dim-value">
              {boardDimensions.cornerRadius || 0}
            </span>
            <span className="pcb-panel__dim-label">Corner R</span>
          </div>
        </div>
      </div>

      {/* Component List */}
      {componentList.length > 0 && (
        <div className="pcb-panel__components">
          <div className="pcb-panel__comp-title">Components</div>
          <ul className="pcb-panel__comp-list">
            {componentList.map((comp, i) => (
              <li key={i} className="pcb-panel__comp-item">
                <span className="pcb-panel__comp-ref">{comp.ref}</span>
                <span className="pcb-panel__comp-name">{comp.name}</span>
                <span
                  className={`pcb-panel__comp-side pcb-panel__comp-side--${comp.side || 'front'}`}
                >
                  {comp.side || 'front'}
                </span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Enclosure Cutout Tags */}
      {cutouts.length > 0 && (
        <div className="pcb-panel__enclosure">
          <div className="pcb-panel__enclosure-title">
            Enclosure Cutouts
          </div>
          <div className="pcb-panel__cutout-list">
            {cutouts.map((c, i) => (
              <span key={i} className="pcb-panel__cutout-tag">
                {c.ref}: {c.name} ({c.wall})
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Generate Enclosure Button */}
      <div className="pcb-panel__actions">
        <button
          className="pcb-panel__action-btn pcb-panel__action-btn--enclosure"
          onClick={handleGenerateEnclosure}
          disabled={generatingEnclosure}
        >
          {generatingEnclosure ? '⏳ Generating...' : '📦 Generate Enclosure'}
        </button>
        <button
          className="pcb-panel__action-btn pcb-panel__action-btn--browse"
          onClick={handleToggleBrowser}
        >
          {showBrowser ? '✕ Close Browser' : '🔍 Browse Components'}
        </button>
      </div>

      {/* Enclosure Result */}
      {enclosureResult && enclosureResult.success && (
        <div className="pcb-panel__enclosure-result">
          <div className="pcb-panel__enclosure-title">Enclosure Generated</div>
          <div className="pcb-panel__downloads">
            {enclosureResult.stlFile && (
              <a href={`${API_HOST}${enclosureResult.stlFile}`} className="pcb-panel__download-btn" download>
                🖨️ Enclosure STL
              </a>
            )}
            {enclosureResult.stepFile && (
              <a href={`${API_HOST}${enclosureResult.stepFile}`} className="pcb-panel__download-btn" download>
                📦 Enclosure STEP
              </a>
            )}
          </div>
        </div>
      )}

      {/* Component Browser */}
      {showBrowser && (
        <div className="pcb-panel__browser">
          <div className="pcb-panel__browser-title">Component Library</div>
          <div className="pcb-panel__browser-search">
            <select
              value={selectedCategory}
              onChange={(e) => setSelectedCategory(e.target.value)}
              className="pcb-panel__browser-select"
            >
              <option value="">All Categories</option>
              {categories.map((cat, i) => (
                <option key={i} value={cat}>{cat}</option>
              ))}
            </select>
            <input
              type="text"
              placeholder="Search components..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
              className="pcb-panel__browser-input"
            />
            <button onClick={handleSearch} disabled={searching} className="pcb-panel__browser-btn">
              {searching ? '...' : '🔍'}
            </button>
          </div>
          {searchResults.length > 0 && (
            <ul className="pcb-panel__browser-results">
              {searchResults.map((comp, i) => (
                <li key={i} className="pcb-panel__browser-item">
                  <span className="pcb-panel__browser-name">{comp.name || comp.id}</span>
                  <span className="pcb-panel__browser-cat">{comp.category}</span>
                  {comp.body && (
                    <span className="pcb-panel__browser-dims">
                      {comp.body.x}×{comp.body.y}×{comp.body.z}mm
                    </span>
                  )}
                </li>
              ))}
            </ul>
          )}
          {searchResults.length === 0 && !searching && (
            <div className="pcb-panel__browser-empty">
              Search or select a category to browse components
            </div>
          )}
        </div>
      )}

      {/* Download Buttons */}
      <div className="pcb-panel__downloads">
        {kicadFile && (
          <a
            href={`${API_HOST}${kicadFile}`}
            className="pcb-panel__download-btn pcb-panel__download-btn--kicad"
            download
          >
            📋 KiCad PCB
          </a>
        )}
        {stepFile && (
          <a
            href={`${API_HOST}${stepFile}`}
            className="pcb-panel__download-btn"
            download
          >
            📦 STEP
          </a>
        )}
        {stlFile && (
          <a
            href={`${API_HOST}${stlFile}`}
            className="pcb-panel__download-btn"
            download
          >
            🖨️ STL
          </a>
        )}
      </div>
    </div>
  );
};

export default PCBPanel;
