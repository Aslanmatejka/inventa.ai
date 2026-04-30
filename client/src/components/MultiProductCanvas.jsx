import React, { useState, useEffect, useRef, useCallback, useMemo } from 'react';
import { Canvas, useThree } from '@react-three/fiber';
import { OrbitControls, Grid, PerspectiveCamera, TransformControls, Html } from '@react-three/drei';
import { STLLoader } from 'three/examples/jsm/loaders/STLLoader';
import * as THREE from 'three';
import { API_HOST } from '../config';
import { authFetch } from '../api';
import './MultiProductCanvas.css';

// ── Color palette for visual distinction ──
const PRODUCT_COLORS = [
  '#8b9dc3', '#a3c4f3', '#90caf9', '#80deea', '#a5d6a7',
  '#c5e1a5', '#fff59d', '#ffe082', '#ffcc80', '#ef9a9a',
  '#f48fb1', '#ce93d8', '#b39ddb', '#9fa8da', '#81d4fa',
];

function snapValue(val, gridSize) {
  if (!gridSize || gridSize <= 0) return val;
  return Math.round(val / gridSize) * gridSize;
}

function toFixed(val, decimals) {
  return Number(Number(val).toFixed(decimals));
}

function radToDeg(rad) { return Number((rad * 180 / Math.PI).toFixed(2)); }
function degToRad(deg) { return deg * Math.PI / 180; }

// ── Precision Input Row ──
function PrecisionInput({ label, value, onChange, step, min, max, decimals, locked, onToggleLock, color }) {
  const [localValue, setLocalValue] = useState(String(toFixed(value, decimals)));
  const inputRef = useRef();

  useEffect(() => {
    if (document.activeElement !== inputRef.current) {
      setLocalValue(String(toFixed(value, decimals)));
    }
  }, [value, decimals]);

  const commit = (v) => {
    let parsed = parseFloat(v);
    if (isNaN(parsed)) parsed = 0;
    if (min !== undefined) parsed = Math.max(min, parsed);
    if (max !== undefined) parsed = Math.min(max, parsed);
    parsed = toFixed(parsed, decimals);
    setLocalValue(String(parsed));
    onChange(parsed);
  };

  return (
    <div className={`precision-input-row ${locked ? 'locked' : ''}`}>
      <span className="precision-label" style={{ color: color || '#b0b3bc' }}>{label}</span>
      <input
        ref={inputRef}
        type="number"
        className="precision-field"
        value={localValue}
        step={step || 1}
        onChange={(e) => setLocalValue(e.target.value)}
        onBlur={(e) => commit(e.target.value)}
        onKeyDown={(e) => {
          if (e.key === 'Enter') { commit(e.target.value); e.target.blur(); }
        }}
        disabled={locked}
      />
      {onToggleLock && (
        <button
          className={`axis-lock-btn ${locked ? 'active' : ''}`}
          onClick={onToggleLock}
          title={locked ? `Unlock ${label} axis` : `Lock ${label} axis`}
        >
          {locked ? '🔒' : '🔓'}
        </button>
      )}
    </div>
  );
}

// ── Precision Panel (right sidebar) ──
function PrecisionPanel({ selectedProduct, onTransformChange, decimals, setDecimals, lockedAxes, setLockedAxes, nudgeAmount, setNudgeAmount, boundingBox }) {
  if (!selectedProduct) return null;

  const pos = selectedProduct.position || { x: 0, y: 0, z: 0 };
  const rot = selectedProduct.rotation || { x: 0, y: 0, z: 0 };
  const scl = selectedProduct.scale || { x: 1, y: 1, z: 1 };

  const updatePos = (axis, val) => {
    if (lockedAxes[axis]) return;
    const newPos = { ...pos, [axis]: val };
    onTransformChange(selectedProduct.instanceId, { position: newPos, rotation: rot, scale: scl });
  };

  const updateRot = (axis, degVal) => {
    const newRot = { ...rot, [axis]: degToRad(degVal) };
    onTransformChange(selectedProduct.instanceId, { position: pos, rotation: newRot, scale: scl });
  };

  // Uniform scale handler
  const updateScaleUniform = (axis, val) => {
    const ratio = scl[axis] !== 0 ? val / scl[axis] : 1;
    const newScl = { x: scl.x * ratio, y: scl.y * ratio, z: scl.z * ratio };
    onTransformChange(selectedProduct.instanceId, { position: pos, rotation: rot, scale: newScl });
  };

  const updateScaleAxis = (axis, val) => {
    const newScl = { ...scl, [axis]: val };
    onTransformChange(selectedProduct.instanceId, { position: pos, rotation: rot, scale: newScl });
  };

  const toggleLock = (axis) => {
    setLockedAxes(prev => ({ ...prev, [axis]: !prev[axis] }));
  };

  return (
    <div className="precision-panel">
      <div className="precision-header">
        <h4>📐 Precision Controls</h4>
        <div className="precision-settings">
          <label title="Decimal places">
            <span>Decimals:</span>
            <select value={decimals} onChange={(e) => setDecimals(Number(e.target.value))}>
              <option value={0}>0</option>
              <option value={1}>1</option>
              <option value={2}>2</option>
              <option value={3}>3</option>
            </select>
          </label>
          <label title="Arrow key nudge amount in mm">
            <span>Nudge:</span>
            <select value={nudgeAmount} onChange={(e) => setNudgeAmount(Number(e.target.value))}>
              <option value={0.1}>0.1mm</option>
              <option value={0.5}>0.5mm</option>
              <option value={1}>1mm</option>
              <option value={5}>5mm</option>
              <option value={10}>10mm</option>
              <option value={25}>25mm</option>
            </select>
          </label>
        </div>
      </div>

      <div className="precision-section">
        <div className="precision-section-title">Position (mm)</div>
        <PrecisionInput label="X" value={pos.x} onChange={(v) => updatePos('x', v)} step={1} decimals={decimals} locked={lockedAxes.x} onToggleLock={() => toggleLock('x')} color="#ff6b6b" />
        <PrecisionInput label="Y" value={pos.y} onChange={(v) => updatePos('y', v)} step={1} decimals={decimals} locked={lockedAxes.y} onToggleLock={() => toggleLock('y')} color="#6bff6b" />
        <PrecisionInput label="Z" value={pos.z} onChange={(v) => updatePos('z', v)} step={1} decimals={decimals} locked={lockedAxes.z} onToggleLock={() => toggleLock('z')} color="#6b9fff" />
      </div>

      <div className="precision-section">
        <div className="precision-section-title">Rotation (°)</div>
        <PrecisionInput label="X" value={radToDeg(rot.x)} onChange={(v) => updateRot('x', v)} step={5} min={-360} max={360} decimals={Math.min(decimals, 1)} color="#ff6b6b" />
        <PrecisionInput label="Y" value={radToDeg(rot.y)} onChange={(v) => updateRot('y', v)} step={5} min={-360} max={360} decimals={Math.min(decimals, 1)} color="#6bff6b" />
        <PrecisionInput label="Z" value={radToDeg(rot.z)} onChange={(v) => updateRot('z', v)} step={5} min={-360} max={360} decimals={Math.min(decimals, 1)} color="#6b9fff" />
      </div>

      <div className="precision-section">
        <div className="precision-section-title">Scale</div>
        <PrecisionInput label="X" value={scl.x} onChange={(v) => updateScaleAxis('x', v)} step={0.1} min={0.01} decimals={Math.max(decimals, 2)} color="#ff6b6b" />
        <PrecisionInput label="Y" value={scl.y} onChange={(v) => updateScaleAxis('y', v)} step={0.1} min={0.01} decimals={Math.max(decimals, 2)} color="#6bff6b" />
        <PrecisionInput label="Z" value={scl.z} onChange={(v) => updateScaleAxis('z', v)} step={0.1} min={0.01} decimals={Math.max(decimals, 2)} color="#6b9fff" />
        <button className="uniform-scale-btn" onClick={() => updateScaleUniform('x', 1)} title="Reset scale to 1">↺ Reset Scale</button>
      </div>

      {boundingBox && (
        <div className="precision-section">
          <div className="precision-section-title">Dimensions (mm)</div>
          <div className="dimension-readout">
            <span className="dim-axis" style={{ color: '#ff6b6b' }}>W:</span>
            <span className="dim-value">{toFixed(boundingBox.x * (scl.x || 1), decimals)}</span>
          </div>
          <div className="dimension-readout">
            <span className="dim-axis" style={{ color: '#6bff6b' }}>H:</span>
            <span className="dim-value">{toFixed(boundingBox.y * (scl.y || 1), decimals)}</span>
          </div>
          <div className="dimension-readout">
            <span className="dim-axis" style={{ color: '#6b9fff' }}>D:</span>
            <span className="dim-value">{toFixed(boundingBox.z * (scl.z || 1), decimals)}</span>
          </div>
        </div>
      )}

      <div className="precision-footer">
        <span>↑↓←→ nudge by {nudgeAmount}mm</span>
        <span>Shift+Arrow = 10× nudge</span>
      </div>
    </div>
  );
}

// ── Auto-fit camera to scene bounds ──
function CameraFitter({ products, trigger }) {
  const { camera, scene } = useThree();

  useEffect(() => {
    if (products.length === 0) return;
    const timer = setTimeout(() => {
      const box = new THREE.Box3();
      scene.traverse((obj) => {
        if (obj.isMesh) box.union(new THREE.Box3().setFromObject(obj));
      });
      if (box.isEmpty()) return;
      const center = box.getCenter(new THREE.Vector3());
      const size = box.getSize(new THREE.Vector3());
      const maxDim = Math.max(size.x, size.y, size.z);
      const dist = maxDim * 2.5;
      camera.position.set(center.x + dist * 0.6, center.y + dist * 0.5, center.z + dist * 0.6);
      camera.lookAt(center);
      camera.updateProjectionMatrix();
    }, 300);
    return () => clearTimeout(timer);
  }, [trigger]); // eslint-disable-line react-hooks/exhaustive-deps

  return null;
}

// ── Draggable 3D Model Component ──
function DraggableModel({
  instanceId, url, position, rotation, scale, color,
  wireframe, isSelected, isMultiSelected, onSelect,
  onTransformChange, transformMode, snapGrid, orbitRef, assemblyId,
  onBoundingBox
}) {
  const meshRef = useRef();
  const transformRef = useRef();
  const [geometry, setGeometry] = useState(null);
  const [loadError, setLoadError] = useState(null);

  useEffect(() => {
    if (!url) return;
    let cancelled = false;
    setLoadError(null);
    setGeometry(null);
    const loader = new STLLoader();
    loader.load(
      url,
      (loadedGeometry) => {
        if (cancelled) { loadedGeometry.dispose(); return; }
        loadedGeometry.computeBoundingBox();
        const bbox = loadedGeometry.boundingBox;
        const center = bbox.getCenter(new THREE.Vector3());
        const size = bbox.getSize(new THREE.Vector3());
        loadedGeometry.translate(-center.x, -center.y, -center.z);
        setGeometry(loadedGeometry);
        setLoadError(null);
        if (onBoundingBox) onBoundingBox(instanceId, { x: size.x, y: size.y, z: size.z });
      },
      undefined,
      (error) => {
        if (!cancelled) {
          console.error('STL loading error for', url, ':', error);
          setLoadError(error?.message || 'Failed to load STL');
          // Create fallback box geometry so user sees something
          const fallback = new THREE.BoxGeometry(20, 20, 20);
          setGeometry(fallback);
        }
      }
    );
    return () => { cancelled = true; };
  }, [url]); // eslint-disable-line react-hooks/exhaustive-deps

  // Disable orbit controls while dragging transform gizmo
  useEffect(() => {
    const ctrl = transformRef.current;
    if (!ctrl || !orbitRef?.current) return;
    const handler = (e) => {
      if (orbitRef.current) orbitRef.current.enabled = !e.value;
    };
    ctrl.addEventListener('dragging-changed', handler);
    return () => ctrl.removeEventListener('dragging-changed', handler);
  }, [orbitRef, geometry]);

  if (!geometry) return null;

  const highlight = isSelected || isMultiSelected;
  const outlineColor = assemblyId ? '#00ff88' : (isMultiSelected ? '#ff6600' : '#ffcc00');
  const emissiveColor = assemblyId ? '#004422' : (isMultiSelected ? '#442200' : '#443300');

  return (
    <group>
      {loadError && (
        <Html position={[position.x, position.y + 30, position.z]} center>
          <div style={{ background: 'rgba(220,50,50,0.85)', color: '#fff', padding: '4px 10px', borderRadius: 6, fontSize: 11, whiteSpace: 'nowrap', pointerEvents: 'none' }}>
            ⚠ STL load failed
          </div>
        </Html>
      )}
      <mesh
        ref={meshRef}
        geometry={geometry}
        position={[position.x, position.y, position.z]}
        rotation={[rotation.x, rotation.y, rotation.z]}
        scale={[scale.x, scale.y, scale.z]}
        onClick={(e) => {
          e.stopPropagation();
          onSelect(instanceId, e.nativeEvent.ctrlKey || e.nativeEvent.metaKey);
        }}
      >
        <meshStandardMaterial
          color={highlight ? outlineColor : color}
          metalness={0.3}
          roughness={0.4}
          wireframe={wireframe}
          side={THREE.DoubleSide}
          emissive={highlight ? emissiveColor : '#000000'}
          emissiveIntensity={highlight ? 0.4 : 0}
        />
      </mesh>

      {isSelected && meshRef.current && (
        <TransformControls
          ref={transformRef}
          object={meshRef.current}
          mode={transformMode}
          translationSnap={snapGrid > 0 ? snapGrid : null}
          rotationSnap={snapGrid > 0 ? THREE.MathUtils.degToRad(15) : null}
          scaleSnap={snapGrid > 0 ? 0.1 : null}
          onObjectChange={() => {
            if (!meshRef.current) return;
            const p = meshRef.current.position;
            const r = meshRef.current.rotation;
            const s = meshRef.current.scale;
            onTransformChange(instanceId, {
              position: {
                x: snapGrid > 0 ? snapValue(p.x, snapGrid) : p.x,
                y: snapGrid > 0 ? snapValue(p.y, snapGrid) : p.y,
                z: snapGrid > 0 ? snapValue(p.z, snapGrid) : p.z
              },
              rotation: { x: r.x, y: r.y, z: r.z },
              scale: { x: s.x, y: s.y, z: s.z }
            });
          }}
        />
      )}
    </group>
  );
}

// ── Dimension Overlay (F43) ──
// Renders dimension lines + labels on the selected product's bounding box
function DimensionLine({ start, end, label, color, offset }) {
  const dir = new THREE.Vector3().subVectors(end, start);
  const length = dir.length();

  const mid = new THREE.Vector3().addVectors(start, end).multiplyScalar(0.5);
  const offDir = offset ? new THREE.Vector3(...offset).normalize().multiplyScalar(2) : new THREE.Vector3(0, 0, 0);
  const labelPos = mid.clone().add(offDir);

  // Create line geometry
  const points = useMemo(() => [start, end], [start, end]);
  const geom = useMemo(() => new THREE.BufferGeometry().setFromPoints(points), [points]);

  // Extension lines (short perpendicular ticks at start/end)
  const tickLen = Math.max(length * 0.04, 1);
  const tickDir2 = useMemo(() => offset ? new THREE.Vector3(...offset).normalize().multiplyScalar(tickLen) : new THREE.Vector3(0, tickLen, 0), [offset, tickLen]);

  const tick1Points = useMemo(() => [
    start.clone().sub(tickDir2),
    start.clone().add(tickDir2),
  ], [start, tickDir2]);
  const tick2Points = useMemo(() => [
    end.clone().sub(tickDir2),
    end.clone().add(tickDir2),
  ], [end, tickDir2]);

  const tick1Geom = useMemo(() => new THREE.BufferGeometry().setFromPoints(tick1Points), [tick1Points]);
  const tick2Geom = useMemo(() => new THREE.BufferGeometry().setFromPoints(tick2Points), [tick2Points]);

  if (length < 0.1) return null;

  return (
    <group>
      <line geometry={geom}>
        <lineBasicMaterial color={color} linewidth={1.5} transparent opacity={0.8} />
      </line>
      <line geometry={tick1Geom}>
        <lineBasicMaterial color={color} linewidth={1.5} />
      </line>
      <line geometry={tick2Geom}>
        <lineBasicMaterial color={color} linewidth={1.5} />
      </line>
      <Html position={[labelPos.x, labelPos.y, labelPos.z]} center style={{ pointerEvents: 'none' }}>
        <div style={{
          background: 'rgba(20,20,30,0.85)',
          color: color,
          padding: '2px 6px',
          borderRadius: '3px',
          fontSize: '11px',
          fontFamily: 'monospace',
          whiteSpace: 'nowrap',
          border: `1px solid ${color}`,
          fontWeight: 600,
        }}>
          {label}
        </div>
      </Html>
    </group>
  );
}

function DimensionsOverlay({ products, selectedId, boundingBoxes, showDimensions }) {
  if (!showDimensions || !selectedId) return null;

  const product = products.find(p => p.instanceId === selectedId);
  const bbox = boundingBoxes[selectedId];
  if (!product || !bbox) return null;

  const pos = product.position || { x: 0, y: 0, z: 0 };
  const scl = product.scale || { x: 1, y: 1, z: 1 };

  const w = bbox.x * scl.x;
  const h = bbox.y * scl.y;
  const d = bbox.z * scl.z;

  // Half dimensions (model is centered after STL load)
  const hw = w / 2, hh = h / 2, hd = d / 2;

  // Dimension line positions (along bounding box edges, offset slightly)
  const margin = Math.max(w, h, d) * 0.15;

  // Width (X) — bottom front edge
  const wStart = new THREE.Vector3(pos.x - hw, pos.y - hh - margin, pos.z + hd);
  const wEnd = new THREE.Vector3(pos.x + hw, pos.y - hh - margin, pos.z + hd);

  // Height (Y) — right front edge
  const hStart = new THREE.Vector3(pos.x + hw + margin, pos.y - hh, pos.z + hd);
  const hEnd = new THREE.Vector3(pos.x + hw + margin, pos.y + hh, pos.z + hd);

  // Depth (Z) — bottom right edge
  const dStart = new THREE.Vector3(pos.x + hw + margin, pos.y - hh - margin, pos.z - hd);
  const dEnd = new THREE.Vector3(pos.x + hw + margin, pos.y - hh - margin, pos.z + hd);

  return (
    <group>
      <DimensionLine
        start={wStart} end={wEnd}
        label={`${w.toFixed(1)} mm`}
        color="#ff6b6b"
        offset={[0, -1, 0]}
      />
      <DimensionLine
        start={hStart} end={hEnd}
        label={`${h.toFixed(1)} mm`}
        color="#6bff6b"
        offset={[1, 0, 0]}
      />
      <DimensionLine
        start={dStart} end={dEnd}
        label={`${d.toFixed(1)} mm`}
        color="#6b9fff"
        offset={[0, -1, 0]}
      />
    </group>
  );
}

// ── Scene Component ──
function Scene({
  products, selectedId, multiSelectedIds, onSelect,
  onTransformChange, transformMode, wireframe, snapGrid,
  orbitRef, assemblies, cameraTrigger, onBoundingBox,
  showDimensions, boundingBoxes
}) {
  return (
    <>
      <ambientLight intensity={0.6} />
      <directionalLight position={[10, 10, 5]} intensity={0.8} castShadow />
      <directionalLight position={[-10, -10, -5]} intensity={0.3} />
      <hemisphereLight intensity={0.4} groundColor="#1a1d24" />

      <Grid
        args={[100, 100]}
        cellSize={10}
        cellThickness={0.5}
        cellColor="#6e6e6e"
        sectionSize={50}
        sectionThickness={1}
        sectionColor="#9d9d9d"
        fadeDistance={400}
        fadeStrength={1}
        followCamera={false}
        infiniteGrid={true}
      />

      {products.map((product, idx) => {
        const assembly = assemblies.find(a =>
          a.parentInstanceId === product.instanceId ||
          a.childInstanceIds?.includes(product.instanceId)
        );
        return (
          <DraggableModel
            key={product.instanceId}
            instanceId={product.instanceId}
            url={product.stlUrl}
            position={product.position || { x: idx * 100, y: 0, z: 0 }}
            rotation={product.rotation || { x: 0, y: 0, z: 0 }}
            scale={product.scale || { x: 1, y: 1, z: 1 }}
            color={product.color || PRODUCT_COLORS[idx % PRODUCT_COLORS.length]}
            wireframe={wireframe}
            isSelected={product.instanceId === selectedId}
            isMultiSelected={multiSelectedIds.includes(product.instanceId)}
            onSelect={onSelect}
            onTransformChange={onTransformChange}
            transformMode={transformMode}
            snapGrid={snapGrid}
            orbitRef={orbitRef}
            assemblyId={assembly?.assemblyId}
            onBoundingBox={onBoundingBox}
          />
        );
      })}

      <CameraFitter products={products} trigger={cameraTrigger} />

      <DimensionsOverlay
        products={products}
        selectedId={selectedId}
        boundingBoxes={boundingBoxes}
        showDimensions={showDimensions}
      />
    </>
  );
}

// ── Main Multi-Product Canvas Component ──
function MultiProductCanvas({ sceneId, initialProducts = [] }) {
  const [products, setProducts] = useState(initialProducts);
  const [selectedId, setSelectedId] = useState(null);
  const [multiSelectedIds, setMultiSelectedIds] = useState([]);
  const [transformMode, setTransformMode] = useState('translate');
  const [wireframe, setWireframe] = useState(false);
  const [assemblies, setAssemblies] = useState([]);
  const [snapGrid, setSnapGrid] = useState(0);
  const [cameraTrigger, setCameraTrigger] = useState(0);
  const [showPrecision, setShowPrecision] = useState(true);
  const [decimals, setDecimals] = useState(1);
  const [lockedAxes, setLockedAxes] = useState({ x: false, y: false, z: false });
  const [nudgeAmount, setNudgeAmount] = useState(5);
  const [boundingBoxes, setBoundingBoxes] = useState({});
  const [showDimensions, setShowDimensions] = useState(true);
  const orbitRef = useRef();

  const handleBoundingBox = useCallback((instanceId, size) => {
    setBoundingBoxes(prev => ({ ...prev, [instanceId]: size }));
  }, []);

  // Sync with parent & auto-fit camera
  useEffect(() => {
    setProducts(initialProducts);
    if (initialProducts.length > 0) setCameraTrigger(c => c + 1);
  }, [initialProducts]);

  // ── Keyboard Shortcuts + Arrow-key nudge ──
  useEffect(() => {
    const onKeyDown = (e) => {
      if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA' || e.target.isContentEditable) return;

      // Arrow-key precision nudging
      if (['arrowup', 'arrowdown', 'arrowleft', 'arrowright'].includes(e.key.toLowerCase()) && selectedId) {
        e.preventDefault();
        const product = products.find(p => p.instanceId === selectedId);
        if (!product) return;
        const amount = (e.shiftKey ? 10 : 1) * nudgeAmount;
        const pos = { ...(product.position || { x: 0, y: 0, z: 0 }) };

        switch (e.key) {
          case 'ArrowRight': if (!lockedAxes.x) pos.x += amount; break;
          case 'ArrowLeft':  if (!lockedAxes.x) pos.x -= amount; break;
          case 'ArrowUp':    if (!lockedAxes.z) pos.z -= amount; break;
          case 'ArrowDown':  if (!lockedAxes.z) pos.z += amount; break;
          default: break;
        }
        handleTransformChange(selectedId, { position: pos, rotation: product.rotation, scale: product.scale });
        return;
      }

      switch (e.key.toLowerCase()) {
        case 'g': setTransformMode('translate'); break;
        case 'r': setTransformMode('rotate'); break;
        case 's':
          if (!e.ctrlKey && !e.metaKey) setTransformMode('scale');
          break;
        case 'delete':
        case 'backspace':
          if (selectedId || multiSelectedIds.length > 0) handleDeleteSelected();
          break;
        case 'd':
          if (e.ctrlKey || e.metaKey) { e.preventDefault(); handleDuplicate(); }
          break;
        case 'a':
          if (e.ctrlKey || e.metaKey) {
            e.preventDefault();
            setMultiSelectedIds(products.map(p => p.instanceId));
            if (products.length > 0) setSelectedId(products[0].instanceId);
          }
          break;
        case 'escape':
          setSelectedId(null);
          setMultiSelectedIds([]);
          break;
        case 'f':
          setCameraTrigger(c => c + 1);
          break;
        case 'p':
          setShowPrecision(prev => !prev);
          break;
        default: break;
      }
    };
    window.addEventListener('keydown', onKeyDown);
    return () => window.removeEventListener('keydown', onKeyDown);
  }, [selectedId, multiSelectedIds, products, nudgeAmount, lockedAxes]); // eslint-disable-line react-hooks/exhaustive-deps

  // ── Transform ──
  const transformTimers = useRef({});
  const handleTransformChange = useCallback((instanceId, transform) => {
    setProducts(prev => prev.map(p => p.instanceId === instanceId ? { ...p, ...transform } : p));
    if (sceneId) {
      // Debounce server sync to avoid flooding with requests during drag
      clearTimeout(transformTimers.current[instanceId]);
      transformTimers.current[instanceId] = setTimeout(() => {
        authFetch(`${API_HOST}/api/scene/product/${instanceId}/transform`, {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(transform)
        }).catch(err => console.error('Transform update failed:', err));
      }, 300);
    }
  }, [sceneId]);

  // ── Select / Multi-Select ──
  const handleSelect = useCallback((instanceId, isCtrl) => {
    if (isCtrl) {
      setMultiSelectedIds(prev =>
        prev.includes(instanceId) ? prev.filter(id => id !== instanceId) : [...prev, instanceId]
      );
      setSelectedId(instanceId);
    } else {
      setSelectedId(prev => prev === instanceId ? null : instanceId);
      setMultiSelectedIds([]);
    }
  }, []);

  // ── Duplicate ──
  const handleDuplicate = useCallback(() => {
    if (!selectedId) return;
    const selected = products.find(p => p.instanceId === selectedId);
    if (!selected) return;

    const offset = {
      x: (selected.position?.x || 0) + 50,
      y: selected.position?.y || 0,
      z: selected.position?.z || 0
    };

    authFetch(`${API_HOST}/api/scene/product/${selectedId}/duplicate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ offset })
    })
      .then(res => {
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        return res.json();
      })
      .then(data => {
        if (data.success) {
          const newProduct = {
            ...selected,
            instanceId: data.duplicate.instanceId,
            instanceName: (selected.instanceName || 'Product') + ' (Copy)',
            position: offset,
            color: PRODUCT_COLORS[products.length % PRODUCT_COLORS.length]
          };
          setProducts(prev => [...prev, newProduct]);
          setSelectedId(data.duplicate.instanceId);
        }
      })
      .catch(err => console.error('Duplicate failed:', err));
  }, [selectedId, products]);

  // ── Delete (multi-aware) ──
  const handleDeleteSelected = useCallback(() => {
    const ids = multiSelectedIds.length > 0
      ? multiSelectedIds
      : (selectedId ? [selectedId] : []);
    if (ids.length === 0) return;

    ids.forEach(id => {
      authFetch(`${API_HOST}/api/scene/product/${id}`, { method: 'DELETE' })
        .catch(err => console.error('Delete failed:', err));
    });
    setProducts(prev => prev.filter(p => !ids.includes(p.instanceId)));
    setSelectedId(null);
    setMultiSelectedIds([]);
  }, [selectedId, multiSelectedIds]);

  // ── Assemble (multi-select aware) ──
  const handleAssemble = useCallback(() => {
    if (!sceneId || products.length < 2) return;

    let selected = multiSelectedIds.length >= 2
      ? products.filter(p => multiSelectedIds.includes(p.instanceId))
      : [];

    if (selected.length < 2) {
      alert('Select at least 2 products to assemble.\nUse Ctrl+Click to multi-select, then click 🔗 Assemble.');
      return;
    }

    authFetch(`${API_HOST}/api/scene/${sceneId}/assemble`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        name: 'Assembly',
        parentInstanceId: selected[0].instanceId,
        childInstanceIds: selected.slice(1).map(p => p.instanceId)
      })
    })
      .then(res => {
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        return res.json();
      })
      .then(data => {
        if (data.success) {
          setAssemblies(prev => [...prev, data.assembly]);
          setMultiSelectedIds([]);
        }
      })
      .catch(err => console.error('Assembly failed:', err));
  }, [sceneId, products, multiSelectedIds]);

  // ── Disassemble ──
  const handleDisassemble = useCallback(() => {
    if (!selectedId || assemblies.length === 0) return;
    const assembly = assemblies.find(a =>
      a.parentInstanceId === selectedId || a.childInstanceIds?.includes(selectedId)
    );
    if (!assembly) { alert('Selected product is not part of an assembly'); return; }

    authFetch(`${API_HOST}/api/scene/assembly/${assembly.assemblyId}`, { method: 'DELETE' })
      .then(res => {
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        return res.json();
      })
      .then(data => {
        if (data.success) setAssemblies(prev => prev.filter(a => a.assemblyId !== assembly.assemblyId));
      })
      .catch(err => console.error('Disassembly failed:', err));
  }, [selectedId, assemblies]);

  // ── Alignment helpers ──
  const getSelectedProducts = useCallback(() => {
    const ids = multiSelectedIds.length > 0 ? multiSelectedIds : (selectedId ? [selectedId] : []);
    return products.filter(p => ids.includes(p.instanceId));
  }, [products, selectedId, multiSelectedIds]);

  const handleAlign = useCallback((axis, mode) => {
    const sel = getSelectedProducts();
    if (sel.length < 2) { alert('Select 2+ products to align (Ctrl+Click).'); return; }

    const vals = sel.map(p => p.position?.[axis] || 0);
    let target;

    if (mode === 'distribute') {
      const sorted = [...sel].sort((a, b) => (a.position?.[axis] || 0) - (b.position?.[axis] || 0));
      const lo = sorted[0].position?.[axis] || 0;
      const hi = sorted[sorted.length - 1].position?.[axis] || 0;
      const step = (hi - lo) / (sorted.length - 1);
      sorted.forEach((p, i) => {
        const newPos = { ...(p.position || { x: 0, y: 0, z: 0 }), [axis]: lo + i * step };
        handleTransformChange(p.instanceId, { position: newPos, rotation: p.rotation, scale: p.scale });
      });
      return;
    }

    if (mode === 'min') target = Math.min(...vals);
    else if (mode === 'max') target = Math.max(...vals);
    else target = (Math.min(...vals) + Math.max(...vals)) / 2;

    sel.forEach(p => {
      const newPos = { ...(p.position || { x: 0, y: 0, z: 0 }), [axis]: target };
      handleTransformChange(p.instanceId, { position: newPos, rotation: p.rotation, scale: p.scale });
    });
  }, [getSelectedProducts, handleTransformChange]);

  const handleResetPosition = useCallback(() => {
    if (!selectedId) return;
    handleTransformChange(selectedId, {
      position: { x: 0, y: 0, z: 0 },
      rotation: { x: 0, y: 0, z: 0 },
      scale: { x: 1, y: 1, z: 1 }
    });
  }, [selectedId, handleTransformChange]);

  const handleSpreadProducts = useCallback(() => {
    if (products.length < 2) return;
    const spacing = 80;
    products.forEach((p, i) => {
      const newPos = { x: i * spacing - ((products.length - 1) * spacing) / 2, y: 0, z: 0 };
      handleTransformChange(p.instanceId, { position: newPos, rotation: p.rotation || { x: 0, y: 0, z: 0 }, scale: p.scale || { x: 1, y: 1, z: 1 } });
    });
  }, [products, handleTransformChange]);

  const hasMulti = multiSelectedIds.length >= 2;
  const selCount = multiSelectedIds.length > 0 ? multiSelectedIds.length : (selectedId ? 1 : 0);

  return (
    <div className="multi-product-canvas">
      <div className="canvas-toolbar">
        {/* Transform */}
        <div className="transform-controls">
          <button className={`tb-icon-btn ${transformMode === 'translate' ? 'active' : ''}`} onClick={() => setTransformMode('translate')} title="Move (G)" aria-label="Move">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M5 9l-3 3 3 3"/><path d="M9 5l3-3 3 3"/><path d="M15 19l-3 3-3-3"/><path d="M19 9l3 3-3 3"/>
              <path d="M2 12h20"/><path d="M12 2v20"/>
            </svg>
          </button>
          <button className={`tb-icon-btn ${transformMode === 'rotate' ? 'active' : ''}`} onClick={() => setTransformMode('rotate')} title="Rotate (R)" aria-label="Rotate">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M3 12a9 9 0 1 0 3-6.7"/><path d="M3 4v5h5"/>
            </svg>
          </button>
          <button className={`tb-icon-btn ${transformMode === 'scale' ? 'active' : ''}`} onClick={() => setTransformMode('scale')} title="Scale (S)" aria-label="Scale">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M15 3h6v6"/><path d="M9 21H3v-6"/><path d="M21 3l-7 7"/><path d="M3 21l7-7"/>
            </svg>
          </button>
        </div>

        {/* Snap */}
        <div className="snap-controls">
          <button className={`tb-icon-btn ${snapGrid > 0 ? 'active' : ''}`} onClick={() => setSnapGrid(prev => prev > 0 ? 0 : 10)} title={snapGrid > 0 ? `Snap ${snapGrid}mm` : 'Toggle snap-to-grid'} aria-label="Snap">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M3 3h7v7H3z"/><path d="M14 3h7v7h-7z"/><path d="M3 14h7v7H3z"/><path d="M14 14h7v7h-7z"/>
            </svg>
            {snapGrid > 0 && <span className="tb-badge">{snapGrid}</span>}
          </button>
          {snapGrid > 0 && (
            <select value={snapGrid} onChange={(e) => setSnapGrid(Number(e.target.value))} className="snap-select">
              <option value={5}>5mm</option>
              <option value={10}>10mm</option>
              <option value={25}>25mm</option>
              <option value={50}>50mm</option>
            </select>
          )}
        </div>

        {/* View */}
        <div className="view-controls">
          <button className="tb-icon-btn" onClick={() => setWireframe(!wireframe)} title={wireframe ? 'Show solid' : 'Show wireframe'} aria-label="Wireframe">
            {wireframe ? (
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <rect x="3" y="3" width="18" height="18" rx="2"/><path d="M3 9h18"/><path d="M9 3v18"/>
              </svg>
            ) : (
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M12 2L2 7l10 5 10-5-10-5z"/><path d="M2 17l10 5 10-5"/><path d="M2 12l10 5 10-5"/>
              </svg>
            )}
          </button>
          <button className="tb-icon-btn" onClick={() => setCameraTrigger(c => c + 1)} title="Fit camera to scene (F)" aria-label="Fit view">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <circle cx="12" cy="12" r="9"/><circle cx="12" cy="12" r="3"/><path d="M12 3v3"/><path d="M12 18v3"/><path d="M3 12h3"/><path d="M18 12h3"/>
            </svg>
          </button>
          <button className={`tb-icon-btn ${showPrecision ? 'active' : ''}`} onClick={() => setShowPrecision(!showPrecision)} title="Toggle precision panel (P)" aria-label="Precise">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M3 3h18v18H3z"/><path d="M3 9h18"/><path d="M9 21V9"/>
            </svg>
          </button>
          <button className={`tb-icon-btn ${showDimensions ? 'active' : ''}`} onClick={() => setShowDimensions(!showDimensions)} title="Toggle dimension lines on selected model" aria-label="Dimensions">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M3 6h18"/><path d="M3 4v4"/><path d="M21 4v4"/><path d="M3 18h18"/><path d="M3 16v4"/><path d="M21 16v4"/>
            </svg>
          </button>
        </div>

        {/* Product actions */}
        <div className="product-controls">
          <button className="tb-icon-btn" onClick={handleDuplicate} disabled={!selectedId} title="Duplicate (Ctrl+D)" aria-label="Duplicate">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <rect x="9" y="9" width="13" height="13" rx="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/>
            </svg>
          </button>
          <button className="tb-icon-btn danger" onClick={handleDeleteSelected} disabled={selCount === 0} title={`Delete${selCount > 1 ? ` (${selCount})` : ''} (Del)`} aria-label="Delete">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M3 6h18"/><path d="M8 6V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/><path d="M19 6l-1 14a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2L5 6"/>
            </svg>
            {selCount > 1 && <span className="tb-badge">{selCount}</span>}
          </button>
          <button className="tb-icon-btn" onClick={handleResetPosition} disabled={!selectedId} title="Reset to origin" aria-label="Reset position">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M21 12a9 9 0 1 1-3-6.7"/><path d="M21 4v5h-5"/><circle cx="12" cy="12" r="1.5"/>
            </svg>
          </button>
        </div>

        {/* Assembly */}
        <div className="assembly-controls">
          <button className="tb-icon-btn" onClick={handleAssemble} disabled={!hasMulti} title={`Group into assembly${hasMulti ? ` (${multiSelectedIds.length})` : ''}`} aria-label="Assemble">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M10 13a5 5 0 0 0 7 0l3-3a5 5 0 0 0-7-7l-1 1"/>
              <path d="M14 11a5 5 0 0 0-7 0l-3 3a5 5 0 0 0 7 7l1-1"/>
            </svg>
            {hasMulti && <span className="tb-badge">{multiSelectedIds.length}</span>}
          </button>
          <button className="tb-icon-btn" onClick={handleDisassemble} disabled={!selectedId} title="Break assembly apart" aria-label="Break assembly">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M9 17H7a5 5 0 0 1 0-10h2"/><path d="M15 7h2a5 5 0 0 1 4 8"/>
              <path d="M8 12h3"/><path d="M16 4l4 4"/><path d="M20 4l-4 4"/>
            </svg>
          </button>
        </div>

        {/* Align (shown when multi-selected or 2+ products) */}
        {(hasMulti || products.length >= 2) && (
          <div className="align-controls">
            <button className="tb-icon-btn" onClick={() => handleAlign('x', 'min')} disabled={!hasMulti} title="Align left (X min)" aria-label="Align left">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M4 3v18"/><rect x="7" y="6" width="10" height="4"/><rect x="7" y="14" width="6" height="4"/>
              </svg>
            </button>
            <button className="tb-icon-btn" onClick={() => handleAlign('x', 'center')} disabled={!hasMulti} title="Align center X" aria-label="Align center">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M12 3v18"/><rect x="7" y="6" width="10" height="4"/><rect x="9" y="14" width="6" height="4"/>
              </svg>
            </button>
            <button className="tb-icon-btn" onClick={() => handleAlign('x', 'max')} disabled={!hasMulti} title="Align right (X max)" aria-label="Align right">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M20 3v18"/><rect x="7" y="6" width="10" height="4"/><rect x="11" y="14" width="6" height="4"/>
              </svg>
            </button>
            <button className="tb-icon-btn" onClick={() => handleAlign('x', 'distribute')} disabled={!hasMulti} title="Distribute evenly along X" aria-label="Distribute">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <rect x="3" y="6" width="4" height="12"/><rect x="10" y="6" width="4" height="12"/><rect x="17" y="6" width="4" height="12"/>
              </svg>
            </button>
            <button className="tb-icon-btn" onClick={handleSpreadProducts} disabled={products.length < 2} title="Spread all products apart" aria-label="Spread">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M5 12H2"/><path d="M22 12h-3"/><path d="M5 12l3-3"/><path d="M5 12l3 3"/><path d="M19 12l-3-3"/><path d="M19 12l-3 3"/>
                <rect x="10" y="8" width="4" height="8"/>
              </svg>
            </button>
          </div>
        )}
      </div>

      <div className="canvas-wrapper">
        {products.length === 0 && (
          <div className="empty-workspace">
            <div className="empty-ws-icon">
              <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.2">
                <path d="M12 2L2 7l10 5 10-5-10-5z"/>
                <path d="M2 17l10 5 10-5"/>
                <path d="M2 12l10 5 10-5"/>
              </svg>
            </div>
            <h3>Your 3D model will appear here</h3>
            <p>Type what you want to build in the chat on the left, and your design will load right here.</p>
            <div className="empty-ws-controls">
              <span>🖱️ Drag to orbit</span>
              <span>🔍 Scroll to zoom</span>
              <span>👆 Click to select</span>
              <span>⌨️ Ctrl+Click multi-select</span>
            </div>
          </div>
        )}
        <Canvas onPointerMissed={() => { setSelectedId(null); setMultiSelectedIds([]); }}>
          <PerspectiveCamera makeDefault position={[400, 300, 400]} fov={50} />
          <Scene
            products={products}
            selectedId={selectedId}
            multiSelectedIds={multiSelectedIds}
            onSelect={handleSelect}
            onTransformChange={handleTransformChange}
            transformMode={transformMode}
            wireframe={wireframe}
            snapGrid={snapGrid}
            orbitRef={orbitRef}
            assemblies={assemblies}
            cameraTrigger={cameraTrigger}
            onBoundingBox={handleBoundingBox}
            showDimensions={showDimensions}
            boundingBoxes={boundingBoxes}
          />
          <OrbitControls
            ref={orbitRef}
            makeDefault
            minDistance={10}
            maxDistance={2000}
            enableDamping={true}
            dampingFactor={0.05}
          />
        </Canvas>
      </div>

      {showPrecision && selectedId && (
        <PrecisionPanel
          selectedProduct={products.find(p => p.instanceId === selectedId)}
          onTransformChange={handleTransformChange}
          decimals={decimals}
          setDecimals={setDecimals}
          lockedAxes={lockedAxes}
          setLockedAxes={setLockedAxes}
          nudgeAmount={nudgeAmount}
          setNudgeAmount={setNudgeAmount}
          boundingBox={boundingBoxes[selectedId]}
        />
      )}

      <div className="scene-info">
        <p>Products: {products.length}{assemblies.length > 0 ? ` · Assemblies: ${assemblies.length}` : ''}</p>
        {selCount > 0 && (
          <p>Selected: {selCount > 1
            ? `${selCount} products`
            : (products.find(p => p.instanceId === selectedId)?.instanceName || 'Product')
          }</p>
        )}
        {selectedId && products.find(p => p.instanceId === selectedId)?.position && (
          <p className="position-info">
            Pos: {toFixed(products.find(p => p.instanceId === selectedId).position.x, decimals)},
            {toFixed(products.find(p => p.instanceId === selectedId).position.y, decimals)},
            {toFixed(products.find(p => p.instanceId === selectedId).position.z, decimals)}
          </p>
        )}
        {snapGrid > 0 && <p className="snap-indicator">🧲 Snap: {snapGrid}mm</p>}
        {Object.values(lockedAxes).some(v => v) && (
          <p className="lock-indicator">🔒 Locked: {Object.entries(lockedAxes).filter(([,v]) => v).map(([k]) => k.toUpperCase()).join(', ')}</p>
        )}
      </div>
    </div>
  );
}

export default MultiProductCanvas;
