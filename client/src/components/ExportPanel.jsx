import React, { useState, useEffect } from 'react';
import { API_HOST } from '../config';
import {
  exportAssembly,
  listMaterials,
  getMaterial,
  setMaterial,
  generateBOM,
  export2DDrawing,
} from '../api';
import VersionPanel from './VersionPanel';
import SlicerPanel from './SlicerPanel';
import CollabPanel from './CollabPanel';
import './ExportPanel.css';

/**
 * Phase 4+: Export Options Panel
 * Provides download buttons for STEP, STL, Python script,
 * plus F34 Assembly export, F37 Material metadata, F39 BOM, F40 2D Drawing
 */
function ExportPanel({ buildId, stlUrl, stepUrl, parametricScript, onShare, sceneProducts, currentDesign, onVersionRestore, sceneId, onSceneSync }) {
  const [sharing, setSharing] = useState(false);
  const [shareUrl, setShareUrl] = useState(null);
  const [copySuccess, setCopySuccess] = useState(false);

  // F37: Material metadata
  const [showMaterial, setShowMaterial] = useState(false);
  const [materials, setMaterials] = useState({});
  const [selectedMaterial, setSelectedMaterial] = useState('');
  const [currentMaterial, setCurrentMaterial] = useState(null);
  const [settingMaterial, setSettingMaterial] = useState(false);

  // F34: Assembly export
  const [exportingAssembly, setExportingAssembly] = useState(false);

  // F39: BOM
  const [generatingBom, setGeneratingBom] = useState(false);
  const [bomResult, setBomResult] = useState(null);

  // F40: 2D drawing
  const [exporting2D, setExporting2D] = useState(false);

  // Load material library on mount
  useEffect(() => {
    let cancelled = false;
    listMaterials()
      .then(res => { if (!cancelled && res.success) setMaterials(res.materials); })
      .catch(() => {});
    return () => { cancelled = true; };
  }, []);

  // Load current material when buildId changes
  useEffect(() => {
    let cancelled = false;
    if (buildId) {
      getMaterial(buildId)
        .then(res => {
          if (!cancelled && res.success && res.material) {
            setCurrentMaterial(res.material);
            setSelectedMaterial(res.material.materialId || '');
          }
        })
        .catch(() => {});
    }
    return () => { cancelled = true; };
  }, [buildId]);

  const handleDownload = (url, filename) => {
    const link = document.createElement('a');
    link.href = `${API_HOST}${url}`;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const handleShare = async () => {
    if (!buildId) return;
    
    setSharing(true);
    try {
      if (onShare) {
        const result = await onShare(buildId);
        setShareUrl(result.shareUrl);
      }
    } catch (error) {
      console.error('Share failed:', error);
      alert('Failed to generate share link: ' + error.message);
    } finally {
      setSharing(false);
    }
  };

  // Clear copy success timeout on unmount
  const copyTimerRef = React.useRef(null);
  useEffect(() => {
    return () => { if (copyTimerRef.current) clearTimeout(copyTimerRef.current); };
  }, []);

  const handleCopyLink = () => {
    if (shareUrl) {
      navigator.clipboard.writeText(shareUrl);
      setCopySuccess(true);
      if (copyTimerRef.current) clearTimeout(copyTimerRef.current);
      copyTimerRef.current = setTimeout(() => setCopySuccess(false), 2000);
    }
  };

  // F37: Material assignment
  const handleSetMaterial = async () => {
    if (!buildId || !selectedMaterial) return;
    setSettingMaterial(true);
    try {
      const res = await setMaterial(buildId, { materialId: selectedMaterial });
      if (res.success) setCurrentMaterial(res.material);
    } catch (err) {
      console.error('Failed to set material:', err);
    } finally {
      setSettingMaterial(false);
    }
  };

  // F34: Assembly STEP export
  const handleAssemblyExport = async () => {
    const products = sceneProducts || [];
    const buildIds = products
      .map(p => p.buildId)
      .filter(Boolean);
    if (buildIds.length === 0 && buildId) {
      buildIds.push(buildId);
    }
    if (buildIds.length === 0) return;

    setExportingAssembly(true);
    try {
      const res = await exportAssembly(buildIds, 'Assembly');
      if (res.success && res.assemblyFile) {
        const link = document.createElement('a');
        link.href = `${API_HOST}${res.assemblyFile}`;
        link.download = `assembly_${res.assemblyId}.step`;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
      }
    } catch (err) {
      alert('Assembly export failed: ' + err.message);
    } finally {
      setExportingAssembly(false);
    }
  };

  // F39: BOM generation
  const handleGenerateBom = async () => {
    const products = sceneProducts || [];
    const items = products.length > 0
      ? products.map((p, i) => ({
          buildId: p.buildId || '',
          name: p.name || p.prompt || `Part ${i + 1}`,
          quantity: 1,
        }))
      : [{ buildId: buildId || '', name: 'Current Design', quantity: 1 }];

    setGeneratingBom(true);
    setBomResult(null);
    try {
      const res = await generateBOM(items);
      if (res.success) {
        setBomResult(res);
        // Also auto-download CSV
        if (res.csvFile) {
          const link = document.createElement('a');
          link.href = `${API_HOST}${res.csvFile}`;
          link.download = 'bill_of_materials.csv';
          document.body.appendChild(link);
          link.click();
          document.body.removeChild(link);
        }
      }
    } catch (err) {
      alert('BOM generation failed: ' + err.message);
    } finally {
      setGeneratingBom(false);
    }
  };

  // F40: 2D Drawing export
  const handle2DExport = async () => {
    if (!buildId) return;
    setExporting2D(true);
    try {
      const res = await export2DDrawing(buildId, ['front', 'top', 'right', 'iso']);
      if (res.success && res.svgFile) {
        const link = document.createElement('a');
        link.href = `${API_HOST}${res.svgFile}`;
        link.download = `drawing_${buildId.slice(0, 8)}.svg`;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
      }
    } catch (err) {
      alert('2D drawing export failed: ' + err.message);
    } finally {
      setExporting2D(false);
    }
  };

  if (!buildId) {
    return null;
  }

  return (
    <div className="export-panel">
      <div className="export-header">
        <h3>📦 Export Options</h3>
        <span className="build-id">Build: {buildId.slice(0, 8)}</span>
      </div>

      <div className="export-buttons">
        {stlUrl && (
          <button 
            className="export-button stl"
            onClick={() => handleDownload(stlUrl, `${buildId}.stl`)}
          >
            <span className="icon">🖨️</span>
            <div className="button-text">
              <span className="title">Download STL</span>
              <span className="subtitle">For 3D Printing</span>
            </div>
          </button>
        )}

        {stepUrl && (
          <button 
            className="export-button step"
            onClick={() => handleDownload(stepUrl, `${buildId}.step`)}
          >
            <span className="icon">⚙️</span>
            <div className="button-text">
              <span className="title">Download STEP</span>
              <span className="subtitle">Editable CAD Format</span>
            </div>
          </button>
        )}

        {parametricScript && (
          <button 
            className="export-button script"
            onClick={() => handleDownload(parametricScript, `${buildId}_parametric.py`)}
          >
            <span className="icon">📝</span>
            <div className="button-text">
              <span className="title">Download Python Script</span>
              <span className="subtitle">Edit & Re-run Locally</span>
            </div>
          </button>
        )}
      </div>

      <div className="share-section">
        <button 
          className="share-button"
          onClick={handleShare}
          disabled={sharing || !buildId}
        >
          {sharing ? (
            <>
              <span className="spinner"></span>
              Generating Share Link...
            </>
          ) : shareUrl ? (
            '✓ Share Link Generated'
          ) : (
            '🔗 Generate Share Link'
          )}
        </button>

        {shareUrl && (
          <div className="share-link-container">
            <input 
              type="text" 
              className="share-link-input" 
              value={shareUrl} 
              readOnly 
            />
            <button 
              className="copy-button"
              onClick={handleCopyLink}
            >
              {copySuccess ? '✓ Copied!' : '📋 Copy'}
            </button>
          </div>
        )}
      </div>

      <div className="export-info">
        <p>💡 <strong>STEP files</strong> can be opened in professional CAD software (SolidWorks, Fusion 360, FreeCAD)</p>
        <p>💡 <strong>STL files</strong> are ready for slicing and 3D printing</p>
        <p>💡 <strong>Python scripts</strong> let you modify parameters and regenerate locally</p>
      </div>

      {/* ── Advanced Export (F34, F40) ── */}
      <div className="export-advanced">
        <h4>📐 Advanced Export</h4>
        <div className="export-buttons">
          <button
            className="export-button assembly"
            onClick={handleAssemblyExport}
            disabled={exportingAssembly}
          >
            <span className="icon">🔩</span>
            <div className="button-text">
              <span className="title">{exportingAssembly ? 'Exporting...' : 'Assembly STEP'}</span>
              <span className="subtitle">Merge all parts into one file</span>
            </div>
          </button>

          <button
            className="export-button drawing"
            onClick={handle2DExport}
            disabled={exporting2D || !buildId}
          >
            <span className="icon">📏</span>
            <div className="button-text">
              <span className="title">{exporting2D ? 'Generating...' : '2D Drawing (SVG)'}</span>
              <span className="subtitle">Engineering views</span>
            </div>
          </button>

          <button
            className="export-button bom"
            onClick={handleGenerateBom}
            disabled={generatingBom}
          >
            <span className="icon">📋</span>
            <div className="button-text">
              <span className="title">{generatingBom ? 'Generating...' : 'Bill of Materials'}</span>
              <span className="subtitle">CSV parts list with dimensions</span>
            </div>
          </button>
        </div>
      </div>

      {/* ── BOM Result (F39) ── */}
      {bomResult && (
        <div className="bom-result">
          <h4>📋 Bill of Materials</h4>
          <table className="bom-table">
            <thead>
              <tr>
                <th>#</th>
                <th>Name</th>
                <th>Material</th>
                <th>Dimensions</th>
                <th>Weight</th>
              </tr>
            </thead>
            <tbody>
              {bomResult.bom.map(row => (
                <tr key={row.item}>
                  <td>{row.item}</td>
                  <td>{row.name}</td>
                  <td>{row.material}</td>
                  <td>{row.dimensions ? `${row.dimensions.length_mm}×${row.dimensions.width_mm}×${row.dimensions.height_mm}` : '—'}</td>
                  <td>{row.weight_g ? `${row.weight_g}g` : '—'}</td>
                </tr>
              ))}
            </tbody>
          </table>
          {bomResult.summary.totalWeight_g && (
            <p className="bom-total">Total weight: {bomResult.summary.totalWeight_g}g ({bomResult.summary.totalQuantity} parts)</p>
          )}
        </div>
      )}

      {/* ── Material Metadata (F37) ── */}
      <div className="material-section">
        <button
          className="material-toggle"
          onClick={() => setShowMaterial(!showMaterial)}
        >
          🎨 {showMaterial ? 'Hide' : 'Show'} Material Properties
        </button>

        {showMaterial && (
          <div className="material-panel">
            <div className="material-select-row">
              <select
                value={selectedMaterial}
                onChange={(e) => setSelectedMaterial(e.target.value)}
                className="material-select"
              >
                <option value="">Select material...</option>
                {Object.entries(materials).map(([id, mat]) => (
                  <option key={id} value={id}>
                    {mat.name} ({mat.category}) — {mat.density} g/cm³
                  </option>
                ))}
              </select>
              <button
                className="material-apply-btn"
                onClick={handleSetMaterial}
                disabled={!selectedMaterial || settingMaterial}
              >
                {settingMaterial ? '...' : 'Apply'}
              </button>
            </div>

            {currentMaterial && (
              <div className="material-info">
                <div className="material-swatch" style={{ backgroundColor: currentMaterial.color || '#ccc' }} />
                <div className="material-details">
                  <strong>{currentMaterial.name}</strong>
                  <span>Finish: {currentMaterial.finish}</span>
                  <span>Density: {currentMaterial.density} g/cm³</span>
                  {currentMaterial.volume_cm3 && <span>Volume: {currentMaterial.volume_cm3} cm³</span>}
                  {currentMaterial.weight_g && <span>Est. Weight: {currentMaterial.weight_g}g</span>}
                </div>
              </div>
            )}
          </div>
        )}
      </div>

      {/* ── Version History (F36) ── */}
      <VersionPanel
        buildId={buildId}
        currentDesign={currentDesign}
        onRestore={onVersionRestore}
      />

      {/* ── 3D Printer Slicer (F38) ── */}
      <SlicerPanel buildId={buildId} />

      {/* ── Collaboration (F35) ── */}
      <CollabPanel sceneId={sceneId} onSceneSync={onSceneSync} />
    </div>
  );
}

export default ExportPanel;
