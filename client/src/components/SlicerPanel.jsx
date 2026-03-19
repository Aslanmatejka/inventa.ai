import React, { useState, useEffect } from 'react';
import { estimatePrint, getSlicerPresets } from '../api';
import './SlicerPanel.css';

/**
 * F38: 3D Printer Slicer Panel
 * Configure print settings and get time/material/cost estimates.
 */
function SlicerPanel({ buildId }) {
  const [expanded, setExpanded] = useState(false);
  const [loading, setLoading] = useState(false);
  const [estimate, setEstimate] = useState(null);
  const [presets, setPresets] = useState({});
  const [filaments, setFilaments] = useState({});

  // Settings
  const [preset, setPreset] = useState('normal');
  const [filament, setFilament] = useState('pla');
  const [supports, setSupports] = useState(false);

  // Load presets on mount
  useEffect(() => {
    if (expanded && Object.keys(presets).length === 0) {
      getSlicerPresets()
        .then(res => {
          if (res.success) {
            setPresets(res.presets || {});
            setFilaments(res.filaments || {});
          }
        })
        .catch(() => {});
    }
  }, [expanded, presets]);

  const handleEstimate = async () => {
    if (!buildId) return;
    setLoading(true);
    try {
      const res = await estimatePrint(buildId, { preset, filament, supports });
      if (res.success) {
        setEstimate(res);
      }
    } catch (err) {
      console.error('Slicer estimate failed:', err);
    } finally {
      setLoading(false);
    }
  };

  // Auto-estimate when settings change (with debounce)
  useEffect(() => {
    if (!expanded || !buildId) return;
    const timer = setTimeout(() => {
      handleEstimate();
    }, 300);
    return () => clearTimeout(timer);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [preset, filament, supports, buildId, expanded]);

  if (!buildId) return null;

  return (
    <div className="slicer-panel">
      <button
        className="slicer-panel__toggle"
        onClick={() => setExpanded(!expanded)}
      >
        <span>🖨️ Print Estimator</span>
        <span className={`slicer-panel__arrow ${expanded ? 'open' : ''}`}>▸</span>
      </button>

      {expanded && (
        <div className="slicer-panel__body">
          {/* Settings Row */}
          <div className="slicer-panel__settings">
            <div className="slicer-setting">
              <label>Quality</label>
              <select value={preset} onChange={(e) => setPreset(e.target.value)}>
                {Object.entries(presets).length > 0
                  ? Object.entries(presets).map(([id, p]) => (
                      <option key={id} value={id}>{p.quality || id}</option>
                    ))
                  : ['draft', 'normal', 'fine', 'ultra', 'strong', 'vase'].map(p => (
                      <option key={p} value={p}>{p.charAt(0).toUpperCase() + p.slice(1)}</option>
                    ))
                }
              </select>
            </div>

            <div className="slicer-setting">
              <label>Filament</label>
              <select value={filament} onChange={(e) => setFilament(e.target.value)}>
                {Object.entries(filaments).length > 0
                  ? Object.entries(filaments).map(([id, f]) => (
                      <option key={id} value={id}>{f.name || id}</option>
                    ))
                  : ['pla', 'abs', 'petg', 'tpu', 'nylon'].map(f => (
                      <option key={f} value={f}>{f.toUpperCase()}</option>
                    ))
                }
              </select>
            </div>

            <div className="slicer-setting slicer-setting--toggle">
              <label>
                <input
                  type="checkbox"
                  checked={supports}
                  onChange={(e) => setSupports(e.target.checked)}
                />
                Supports
              </label>
            </div>
          </div>

          {/* Estimate Results */}
          {loading && (
            <div className="slicer-panel__loading">Calculating estimate...</div>
          )}

          {estimate && !loading && (
            <div className="slicer-panel__results">
              {/* Primary Stats */}
              <div className="slicer-stats-grid">
                <div className="slicer-stat">
                  <span className="slicer-stat__icon">⏱️</span>
                  <span className="slicer-stat__value">{estimate.estimate.printTimeFormatted}</span>
                  <span className="slicer-stat__label">Print Time</span>
                </div>
                <div className="slicer-stat">
                  <span className="slicer-stat__icon">⚖️</span>
                  <span className="slicer-stat__value">{estimate.estimate.weightGrams}g</span>
                  <span className="slicer-stat__label">Weight</span>
                </div>
                <div className="slicer-stat">
                  <span className="slicer-stat__icon">📏</span>
                  <span className="slicer-stat__value">{estimate.estimate.filamentLengthM}m</span>
                  <span className="slicer-stat__label">Filament</span>
                </div>
                <div className="slicer-stat">
                  <span className="slicer-stat__icon">💰</span>
                  <span className="slicer-stat__value">${estimate.estimate.costEstimate}</span>
                  <span className="slicer-stat__label">Est. Cost</span>
                </div>
              </div>

              {/* Details */}
              <div className="slicer-details">
                <div className="slicer-detail-row">
                  <span>Layers</span>
                  <span>{estimate.estimate.totalLayers}</span>
                </div>
                <div className="slicer-detail-row">
                  <span>Layer Height</span>
                  <span>{estimate.settings.layerHeight}mm</span>
                </div>
                <div className="slicer-detail-row">
                  <span>Infill</span>
                  <span>{estimate.settings.infill}%</span>
                </div>
                <div className="slicer-detail-row">
                  <span>Shells</span>
                  <span>{estimate.settings.shells}</span>
                </div>
                <div className="slicer-detail-row">
                  <span>Speed</span>
                  <span>{estimate.settings.speed} mm/s</span>
                </div>
                {estimate.settings.nozzleTemp > 0 && (
                  <div className="slicer-detail-row">
                    <span>Nozzle / Bed</span>
                    <span>{estimate.settings.nozzleTemp}°C / {estimate.settings.bedTemp}°C</span>
                  </div>
                )}
              </div>

              {/* Bed Fit Warning */}
              {estimate.model && !estimate.model.fitsBed && (
                <div className="slicer-warning">
                  ⚠️ Model exceeds standard bed size ({estimate.model.boundingBox.x} × {estimate.model.boundingBox.y} × {estimate.model.boundingBox.z} mm)
                </div>
              )}
              {estimate.model && estimate.model.needsSupports && !supports && (
                <div className="slicer-warning slicer-warning--info">
                  💡 This model likely needs supports. Consider enabling them.
                </div>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export default SlicerPanel;
