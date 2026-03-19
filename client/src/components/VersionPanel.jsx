import React, { useState, useEffect } from 'react';
import { saveVersion, listVersions, restoreVersion } from '../api';
import './VersionPanel.css';

/**
 * F36: Version History Panel
 * Save, list, and restore design version snapshots.
 */
function VersionPanel({ buildId, currentDesign, onRestore }) {
  const [versions, setVersions] = useState([]);
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [restoring, setRestoring] = useState(null);
  const [label, setLabel] = useState('');
  const [expanded, setExpanded] = useState(false);

  // Load versions when buildId changes
  useEffect(() => {
    if (buildId && expanded) {
      loadVersions();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [buildId, expanded]);

  const loadVersions = async () => {
    if (!buildId) return;
    setLoading(true);
    try {
      const res = await listVersions(buildId);
      if (res.success) {
        setVersions(res.versions || []);
      }
    } catch (err) {
      console.error('Failed to load versions:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async () => {
    if (!buildId) return;
    setSaving(true);
    try {
      const res = await saveVersion(
        buildId,
        label || undefined,
        currentDesign,
        currentDesign?.parameters || null
      );
      if (res.success) {
        setLabel('');
        await loadVersions();
      }
    } catch (err) {
      console.error('Failed to save version:', err);
    } finally {
      setSaving(false);
    }
  };

  const handleRestore = async (versionId) => {
    setRestoring(versionId);
    try {
      const res = await restoreVersion(buildId, versionId);
      if (res.success && onRestore) {
        onRestore(res);
      }
    } catch (err) {
      console.error('Failed to restore version:', err);
      alert('Restore failed: ' + err.message);
    } finally {
      setRestoring(null);
    }
  };

  const formatTimestamp = (ts) => {
    try {
      const d = new Date(ts);
      return d.toLocaleString(undefined, {
        month: 'short', day: 'numeric',
        hour: '2-digit', minute: '2-digit',
      });
    } catch {
      return ts;
    }
  };

  if (!buildId) return null;

  return (
    <div className="version-panel">
      <button
        className="version-panel__toggle"
        onClick={() => setExpanded(!expanded)}
      >
        <span>🕒 Version History</span>
        <span className="version-panel__count">{versions.length}</span>
        <span className={`version-panel__arrow ${expanded ? 'open' : ''}`}>▸</span>
      </button>

      {expanded && (
        <div className="version-panel__body">
          {/* Save new version */}
          <div className="version-panel__save-row">
            <input
              type="text"
              className="version-panel__label-input"
              placeholder="Version label (optional)"
              value={label}
              onChange={(e) => setLabel(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleSave()}
            />
            <button
              className="version-panel__save-btn"
              onClick={handleSave}
              disabled={saving}
            >
              {saving ? '⏳' : '💾'} Save
            </button>
          </div>

          {/* Version list */}
          <div className="version-panel__list">
            {loading ? (
              <div className="version-panel__loading">Loading versions...</div>
            ) : versions.length === 0 ? (
              <div className="version-panel__empty">No versions saved yet</div>
            ) : (
              versions.slice().reverse().map((v) => (
                <div key={v.versionId} className="version-panel__item">
                  <div className="version-panel__item-info">
                    <span className="version-panel__item-label">{v.label}</span>
                    <span className="version-panel__item-time">{formatTimestamp(v.timestamp)}</span>
                  </div>
                  <div className="version-panel__item-meta">
                    {v.hasCode && <span className="version-badge">Code</span>}
                    {v.hasParameters && <span className="version-badge">Params</span>}
                  </div>
                  <button
                    className="version-panel__restore-btn"
                    onClick={() => handleRestore(v.versionId)}
                    disabled={!!restoring}
                    title="Restore this version"
                  >
                    {restoring === v.versionId ? '⏳' : '↩️'} Restore
                  </button>
                </div>
              ))
            )}
          </div>
        </div>
      )}
    </div>
  );
}

export default VersionPanel;
