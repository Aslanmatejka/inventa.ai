import React, { useState, useRef, useCallback, useEffect } from 'react';
import { searchPCBComponents, getPCBCategories, routePCBTraces } from '../api';
import './PCBDesigner.css';

/**
 * F42: PCB Drag-and-Drop Component Placement Designer
 * Interactive canvas for placing and arranging PCB components.
 * F41: Integrated trace routing visualization.
 */
function PCBDesigner({ onDesignUpdate }) {
  const [expanded, setExpanded] = useState(false);
  const [boardWidth, setBoardWidth] = useState(100);
  const [boardHeight, setBoardHeight] = useState(80);
  const [placedComponents, setPlacedComponents] = useState([]);
  const [selectedComponent, setSelectedComponent] = useState(null);
  const [dragState, setDragState] = useState(null);

  // Component browser
  const [categories, setCategories] = useState([]);
  const [selectedCategory, setSelectedCategory] = useState('');
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState([]);
  const [searching, setSearching] = useState(false);

  // Trace routing
  const [traces, setTraces] = useState([]);
  const [showTraces, setShowTraces] = useState(true);
  const [routing, setRouting] = useState(false);

  const svgRef = useRef(null);
  const SCALE = 4; // px per mm

  // Load categories
  useEffect(() => {
    if (expanded && categories.length === 0) {
      getPCBCategories()
        .then(data => setCategories(data.categories || []))
        .catch(() => {});
    }
  }, [expanded, categories.length]);

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

  // Add component to board
  const addComponent = useCallback((comp) => {
    const id = `${comp.name || comp.id}_${Date.now()}`;
    const newComp = {
      id,
      name: comp.name || comp.id,
      x: boardWidth / 2,
      y: boardHeight / 2,
      width: comp.footprint?.width || comp.width || 10,
      height: comp.footprint?.height || comp.height || 6,
      rotation: 0,
      pads: (comp.footprint?.pads || comp.pads || []).map((p, i) => ({
        id: `pad_${i}`,
        x: p.x || (i % 2 === 0 ? -3 : 3),
        y: p.y || (Math.floor(i / 2) * 2.54 - 2.54),
        net: p.net || '',
      })),
      category: comp.category || '',
      value: comp.value || '',
    };

    // Default pads if none
    if (newComp.pads.length === 0) {
      const w = newComp.width / 2;
      newComp.pads = [
        { id: 'pad_0', x: -w + 1, y: 0, net: '' },
        { id: 'pad_1', x: w - 1, y: 0, net: '' },
      ];
    }

    setPlacedComponents(prev => [...prev, newComp]);
    setTraces([]); // Clear traces when board changes
  }, [boardWidth, boardHeight]);

  // Remove component
  const removeComponent = useCallback((compId) => {
    setPlacedComponents(prev => prev.filter(c => c.id !== compId));
    if (selectedComponent === compId) setSelectedComponent(null);
    setTraces([]);
  }, [selectedComponent]);

  // Drag handlers
  const handleMouseDown = useCallback((e, compId) => {
    e.preventDefault();
    const svg = svgRef.current;
    if (!svg) return;

    const comp = placedComponents.find(c => c.id === compId);
    if (!comp) return;

    setDragState({
      compId,
      startX: e.clientX,
      startY: e.clientY,
      origX: comp.x,
      origY: comp.y,
    });
    setSelectedComponent(compId);
  }, [placedComponents]);

  const handleMouseMove = useCallback((e) => {
    if (!dragState) return;
    const dx = (e.clientX - dragState.startX) / SCALE;
    const dy = (e.clientY - dragState.startY) / SCALE;

    let newX = dragState.origX + dx;
    let newY = dragState.origY + dy;

    // Clamp to board
    newX = Math.max(5, Math.min(boardWidth - 5, newX));
    newY = Math.max(5, Math.min(boardHeight - 5, newY));

    // Snap to 2.54mm grid
    newX = Math.round(newX / 2.54) * 2.54;
    newY = Math.round(newY / 2.54) * 2.54;

    setPlacedComponents(prev =>
      prev.map(c => c.id === dragState.compId ? { ...c, x: newX, y: newY } : c)
    );
  }, [dragState, boardWidth, boardHeight]);

  const handleMouseUp = useCallback(() => {
    if (dragState) {
      setDragState(null);
      setTraces([]); // Clear cached traces on move
    }
  }, [dragState]);

  useEffect(() => {
    if (dragState) {
      window.addEventListener('mousemove', handleMouseMove);
      window.addEventListener('mouseup', handleMouseUp);
      return () => {
        window.removeEventListener('mousemove', handleMouseMove);
        window.removeEventListener('mouseup', handleMouseUp);
      };
    }
  }, [dragState, handleMouseMove, handleMouseUp]);

  // Rotate selected
  const rotateSelected = () => {
    if (!selectedComponent) return;
    setPlacedComponents(prev =>
      prev.map(c => c.id === selectedComponent ? { ...c, rotation: (c.rotation + 90) % 360 } : c)
    );
    setTraces([]);
  };

  // Auto-route traces
  const handleAutoRoute = async () => {
    if (placedComponents.length < 2) return;
    setRouting(true);
    try {
      const res = await routePCBTraces(boardWidth, boardHeight, placedComponents);
      if (res.success) {
        setTraces(res.traces || []);
      }
    } catch (err) {
      console.error('Auto-routing failed:', err);
    } finally {
      setRouting(false);
    }
  };

  // Notify parent of design changes
  useEffect(() => {
    if (onDesignUpdate) {
      onDesignUpdate({ boardWidth, boardHeight, components: placedComponents, traces });
    }
  }, [placedComponents, traces, boardWidth, boardHeight, onDesignUpdate]);

  // Trace colors
  const TRACE_COLORS = ['#ff4444', '#4444ff', '#ffaa00', '#44ff44', '#ff44ff', '#44ffff', '#ffff44', '#ff8844'];

  if (!expanded) {
    return (
      <div className="pcb-designer">
        <button className="pcb-designer__toggle" onClick={() => setExpanded(true)}>
          <span>🔧 PCB Layout Designer</span>
          {placedComponents.length > 0 && (
            <span className="pcb-designer__count">{placedComponents.length}</span>
          )}
          <span className="pcb-designer__arrow">▸</span>
        </button>
      </div>
    );
  }

  return (
    <div className="pcb-designer pcb-designer--expanded">
      <div className="pcb-designer__header">
        <span>🔧 PCB Layout Designer</span>
        <div className="pcb-designer__header-actions">
          <button className="pcb-designer__btn" onClick={handleAutoRoute} disabled={routing || placedComponents.length < 2}>
            {routing ? '⏳' : '⚡'} Route
          </button>
          <button className="pcb-designer__btn" onClick={() => setShowTraces(!showTraces)}>
            {showTraces ? '👁️' : '🚫'} Traces
          </button>
          <button className="pcb-designer__close" onClick={() => setExpanded(false)}>✕</button>
        </div>
      </div>

      <div className="pcb-designer__layout">
        {/* Board Canvas */}
        <div className="pcb-designer__canvas-container">
          {/* Board size controls */}
          <div className="pcb-designer__board-size">
            <label>
              W: <input type="number" value={boardWidth} onChange={(e) => setBoardWidth(Number(e.target.value))} min={20} max={300} />
            </label>
            <label>
              H: <input type="number" value={boardHeight} onChange={(e) => setBoardHeight(Number(e.target.value))} min={20} max={300} />
            </label>
            mm
          </div>

          <svg
            ref={svgRef}
            className="pcb-designer__svg"
            viewBox={`0 0 ${boardWidth * SCALE} ${boardHeight * SCALE}`}
            width={boardWidth * SCALE}
            height={boardHeight * SCALE}
            style={{ maxWidth: '100%', height: 'auto' }}
          >
            {/* Board background */}
            <rect
              width={boardWidth * SCALE}
              height={boardHeight * SCALE}
              fill="#1a5c1a"
              rx="4"
              stroke="#2d8a2d"
              strokeWidth="2"
            />

            {/* Grid */}
            {Array.from({ length: Math.floor(boardWidth / 2.54) }).map((_, i) => (
              <line key={`gv${i}`} x1={(i + 1) * 2.54 * SCALE} y1={0} x2={(i + 1) * 2.54 * SCALE} y2={boardHeight * SCALE}
                stroke="rgba(255,255,255,0.05)" strokeWidth="0.5" />
            ))}
            {Array.from({ length: Math.floor(boardHeight / 2.54) }).map((_, i) => (
              <line key={`gh${i}`} x1={0} y1={(i + 1) * 2.54 * SCALE} x2={boardWidth * SCALE} y2={(i + 1) * 2.54 * SCALE}
                stroke="rgba(255,255,255,0.05)" strokeWidth="0.5" />
            ))}

            {/* Traces */}
            {showTraces && traces.map((trace, idx) => {
              const color = TRACE_COLORS[idx % TRACE_COLORS.length];
              const points = trace.points.map(p => `${p.x * SCALE},${p.y * SCALE}`).join(' ');
              return (
                <polyline
                  key={`trace-${idx}`}
                  points={points}
                  stroke={color}
                  strokeWidth={trace.width * SCALE}
                  fill="none"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  opacity="0.8"
                />
              );
            })}

            {/* Components */}
            {placedComponents.map((comp) => {
              const cx = comp.x * SCALE;
              const cy = comp.y * SCALE;
              const cw = comp.width * SCALE;
              const ch = comp.height * SCALE;
              const isSelected = selectedComponent === comp.id;

              return (
                <g key={comp.id} transform={`rotate(${comp.rotation}, ${cx}, ${cy})`}>
                  {/* Component body */}
                  <rect
                    x={cx - cw / 2}
                    y={cy - ch / 2}
                    width={cw}
                    height={ch}
                    fill={isSelected ? 'rgba(99,102,241,0.3)' : 'rgba(40,40,40,0.8)'}
                    stroke={isSelected ? '#6366f1' : '#666'}
                    strokeWidth={isSelected ? 2 : 1}
                    rx="2"
                    style={{ cursor: 'grab' }}
                    onMouseDown={(e) => handleMouseDown(e, comp.id)}
                  />

                  {/* Component label */}
                  <text
                    x={cx}
                    y={cy}
                    textAnchor="middle"
                    dominantBaseline="middle"
                    fill="#ccc"
                    fontSize={Math.max(6, Math.min(10, cw / 4))}
                    style={{ pointerEvents: 'none', userSelect: 'none' }}
                  >
                    {comp.name.substring(0, 8)}
                  </text>

                  {/* Pads */}
                  {comp.pads.map((pad) => (
                    <circle
                      key={pad.id}
                      cx={(comp.x + pad.x) * SCALE}
                      cy={(comp.y + pad.y) * SCALE}
                      r={1.5 * SCALE}
                      fill="#c0c0c0"
                      stroke="#888"
                      strokeWidth="0.5"
                    />
                  ))}
                </g>
              );
            })}
          </svg>

          {/* Selected component controls */}
          {selectedComponent && (
            <div className="pcb-designer__comp-controls">
              <span className="pcb-designer__comp-name">
                {placedComponents.find(c => c.id === selectedComponent)?.name}
              </span>
              <button onClick={rotateSelected} title="Rotate 90°">🔄</button>
              <button onClick={() => removeComponent(selectedComponent)} title="Delete">🗑️</button>
            </div>
          )}
        </div>

        {/* Component Library Sidebar */}
        <div className="pcb-designer__sidebar">
          <div className="pcb-designer__search">
            <input
              type="text"
              placeholder="Search components..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
              className="pcb-designer__search-input"
            />
            <select
              value={selectedCategory}
              onChange={(e) => setSelectedCategory(e.target.value)}
              className="pcb-designer__category-select"
            >
              <option value="">All Categories</option>
              {categories.map(cat => (
                <option key={cat} value={cat}>{cat}</option>
              ))}
            </select>
            <button className="pcb-designer__search-btn" onClick={handleSearch} disabled={searching}>
              {searching ? '⏳' : '🔍'}
            </button>
          </div>

          <div className="pcb-designer__results">
            {searchResults.length === 0 && !searching && (
              <div className="pcb-designer__results-empty">
                Search for components to add to the board
              </div>
            )}
            {searchResults.map((comp, idx) => (
              <button
                key={idx}
                className="pcb-designer__comp-item"
                onClick={() => addComponent(comp)}
                title={`Add ${comp.name} to board`}
              >
                <span className="pcb-comp-name">{comp.name}</span>
                <span className="pcb-comp-cat">{comp.category}</span>
              </button>
            ))}
          </div>

          {/* Placed components list */}
          {placedComponents.length > 0 && (
            <div className="pcb-designer__placed">
              <div className="pcb-designer__placed-header">
                Placed ({placedComponents.length})
              </div>
              {placedComponents.map((comp) => (
                <div
                  key={comp.id}
                  className={`pcb-designer__placed-item ${selectedComponent === comp.id ? 'active' : ''}`}
                  onClick={() => setSelectedComponent(comp.id)}
                >
                  <span>{comp.name}</span>
                  <span className="pcb-placed-pos">
                    ({comp.x.toFixed(1)}, {comp.y.toFixed(1)})
                  </span>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default PCBDesigner;
