import React, { useRef, useEffect, useCallback, useState } from 'react';
import { Routes, Route, useNavigate, useParams, Navigate } from 'react-router-dom';
import PromptInput from './components/PromptInput';
import MultiProductCanvas from './components/MultiProductCanvas';
import ProjectBrowser from './components/ProjectBrowser';
import ParameterPanel from './components/ParameterPanel';
import ExportPanel from './components/ExportPanel';
import CodeView from './components/CodeView';
import AuthScreen from './components/AuthScreen';
import PricingPage from './components/PricingPage';
import CookieConsent from './components/CookieConsent';
import { useAuth } from './context/AuthContext';
import { useAppContext } from './context/AppContext';
import { useBuild } from './hooks/useBuild';
import { uploadToS3 } from './api';
import { API_HOST } from './config';
import './App.css';
// Modern theme overrides — keep last so it wins the cascade.
import './theme.css';
// Monochrome override (white canvas, black UI elements) — must load last.
import './theme-mono.css';

/* Simple markdown → HTML for Ask responses */
function formatMarkdown(text) {
  if (!text) return '';
  return text
    .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
    .replace(/```(\w*)\n([\s\S]*?)```/g, '<pre><code class="lang-$1">$2</code></pre>')
    .replace(/`([^`]+)`/g, '<code>$1</code>')
    .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*(.+?)\*/g, '<em>$1</em>')
    .replace(/^### (.+)$/gm, '<h4>$1</h4>')
    .replace(/^## (.+)$/gm, '<h3>$1</h3>')
    .replace(/^# (.+)$/gm, '<h2>$1</h2>')
    .replace(/^- (.+)$/gm, '<li>$1</li>')
    .replace(/(<li>.*<\/li>)/gs, '<ul>$1</ul>')
    .replace(/\n{2,}/g, '</p><p>')
    .replace(/\n/g, '<br/>');
}

function App() {
  const { user, signOut } = useAuth();
  const { state, dispatch, canUndo, canRedo, undo, redo } = useAppContext();
  const {
    status, result, messages, currentDesign, currentBuildId,
    chatCollapsed, previewCollapsed,
    activeTab, showProjectBrowser, buildProgress, sceneProducts,
    currentScene, showParameterPanel, buildStartTime, uploadedFile,
  } = state;

  const { handleBuild, handleRebuild, handleStopBuild, handleProjectSelect, handleNewProject, initializeScene } = useBuild();

  const messagesEndRef = useRef(null);
  const chatMessagesRef = useRef(null);
  const [isAtBottom, setIsAtBottom] = useState(true);
  const [isMobile, setIsMobile] = useState(window.innerWidth <= 968);
  const [elapsedTime, setElapsedTime] = useState(0);
  const [showCodeView, setShowCodeView] = useState(false);

  const navigate = useNavigate();

  // Track mobile breakpoint
  useEffect(() => {
    const onResize = () => setIsMobile(window.innerWidth <= 968);
    window.addEventListener('resize', onResize);
    return () => window.removeEventListener('resize', onResize);
  }, []);

  // Smart auto-scroll: only scroll if user is already at bottom
  useEffect(() => {
    if (isAtBottom) {
      messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }
  }, [messages, isAtBottom]);

  const handleChatScroll = useCallback(() => {
    const el = chatMessagesRef.current;
    if (!el) return;
    const atBottom = el.scrollHeight - el.scrollTop - el.clientHeight < 60;
    setIsAtBottom(atBottom);
  }, []);

  // Elapsed time during build
  useEffect(() => {
    if (status !== 'building' || !buildStartTime) {
      setElapsedTime(0);
      return;
    }
    const interval = setInterval(() => {
      setElapsedTime(Math.floor((Date.now() - buildStartTime) / 1000));
    }, 1000);
    return () => clearInterval(interval);
  }, [status, buildStartTime]);



  // Initialize scene on mount
  useEffect(() => {
    if (!currentScene) initializeScene();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Keyboard shortcuts
  useEffect(() => {
    const handleKeyboard = (e) => {
      if (e.ctrlKey && e.key === 'z' && !e.shiftKey) {
        e.preventDefault();
        if (canUndo) undo();
      }
      if (e.ctrlKey && e.key === 'z' && e.shiftKey) {
        e.preventDefault();
        if (canRedo) redo();
      }
      if (e.ctrlKey && e.key === 'y') {
        e.preventDefault();
        if (canRedo) redo();
      }
    };
    window.addEventListener('keydown', handleKeyboard);
    return () => window.removeEventListener('keydown', handleKeyboard);
  }, [canUndo, canRedo, undo, redo]);

  // Compute grid columns — fixed chat width like VS Code
  const getGridColumns = () => {
    if (isMobile) return '1fr';
    if (chatCollapsed) return '48px 0px 1fr';
    if (previewCollapsed) return '1fr 0px 48px';
    return '380px 1px 1fr';
  };

  const formatTime = (seconds) => {
    if (seconds < 60) return `${seconds}s`;
    return `${Math.floor(seconds / 60)}m ${seconds % 60}s`;
  };

  const parameters = currentDesign?.parameters;
  const hasDesign = !!result;

  return (
    <div className="App">
      {/* ════ Header ════ */}
      <header>
        <div className="header-left">
          <h1>
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M12 2L2 7l10 5 10-5-10-5z"/>
              <path d="M2 17l10 5 10-5"/>
              <path d="M2 12l10 5 10-5"/>
            </svg>
            inventa.AI
          </h1>
        </div>
        <div className="header-center">
          {/* Undo / Redo */}
          <button
            className="header-icon-btn"
            onClick={undo}
            disabled={!canUndo}
            title="Undo (Ctrl+Z)"
          >
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <polyline points="1 4 1 10 7 10"/>
              <path d="M3.51 15a9 9 0 1 0 2.13-9.36L1 10"/>
            </svg>
          </button>
          <button
            className="header-icon-btn"
            onClick={redo}
            disabled={!canRedo}
            title="Redo (Ctrl+Shift+Z)"
          >
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <polyline points="23 4 23 10 17 10"/>
              <path d="M20.49 15a9 9 0 1 1-2.13-9.36L23 10"/>
            </svg>
          </button>
        </div>
        <div className="header-right">
          <button
            className="projects-btn"
            onClick={() => dispatch({ type: 'SET_SHOW_PROJECT_BROWSER', payload: true })}
            title="View your saved projects"
          >
            <svg width="16" height="16" viewBox="0 0 16 16" fill="currentColor">
              <path d="M1.5 0A1.5 1.5 0 0 0 0 1.5v13A1.5 1.5 0 0 0 1.5 16h13a1.5 1.5 0 0 0 1.5-1.5v-13A1.5 1.5 0 0 0 14.5 0h-13zM1 1.5a.5.5 0 0 1 .5-.5h13a.5.5 0 0 1 .5.5v13a.5.5 0 0 1-.5.5h-13a.5.5 0 0 1-.5-.5v-13z"/>
              <path d="M4 4a.5.5 0 0 1 .5-.5h7a.5.5 0 0 1 0 1h-7A.5.5 0 0 1 4 4zm0 3a.5.5 0 0 1 .5-.5h7a.5.5 0 0 1 0 1h-7A.5.5 0 0 1 4 7zm0 3a.5.5 0 0 1 .5-.5h7a.5.5 0 0 1 0 1h-7a.5.5 0 0 1 0-1z"/>
            </svg>
            My Projects
          </button>
          {result && (result.stlUrl || result.files?.stl || result.stepUrl || result.files?.step) && (
            <div className="export-links">
              {(result.stlUrl || result.files?.stl) && (
                <a
                  href={(() => { const u = result.stlUrl || result.files.stl; return u.startsWith('http') ? u : `${API_HOST}${u}`; })()}
                  download
                  className="export-btn"
                  title="Download for 3D printing"
                >
                  🖨️ STL
                </a>
              )}
              {(result.stepUrl || result.files?.step) && (
                <a
                  href={(() => { const u = result.stepUrl || result.files.step; return u.startsWith('http') ? u : `${API_HOST}${u}`; })()}
                  download
                  className="export-btn"
                  title="Open in FreeCAD or Fusion 360"
                >
                  ✏️ STEP
                </a>
              )}
            </div>
          )}
          {/* Pricing link */}
          <button
            className="projects-btn"
            onClick={() => navigate('/pricing')}
            title="View plans & pricing"
          >
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M12 2v20M17 5H9.5a3.5 3.5 0 000 7h5a3.5 3.5 0 010 7H6" />
            </svg>
            Pricing
          </button>
          {/* User Profile & Logout */}
          <div className="user-menu">
            <span className="user-avatar" title={user?.email}>
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/>
                <circle cx="12" cy="7" r="4"/>
              </svg>
            </span>
            <button
              className="header-icon-btn logout-btn"
              onClick={signOut}
              title="Sign out"
            >
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M9 21H5a2 2 0 01-2-2V5a2 2 0 012-2h4"/>
                <polyline points="16 17 21 12 16 7"/>
                <line x1="21" y1="12" x2="9" y2="12"/>
              </svg>
            </button>
          </div>
        </div>
      </header>

      {/* ════ Build Progress Bar ════ */}
      {status === 'building' && (
        <div className="build-progress-bar">
          <div
            className="build-progress-fill"
            style={{ width: `${buildProgress}%` }}
          />
          <span className="build-progress-label">
            {buildProgress < 100 ? `Building... ${formatTime(elapsedTime)}` : 'Finishing...'}
          </span>
        </div>
      )}

      {/* ════ Mobile Tab Bar ════ */}
      {isMobile && (
        <div className="mobile-tab-bar">
          <button
            className={`mobile-tab ${activeTab === 'chat' ? 'active' : ''}`}
            onClick={() => dispatch({ type: 'SET_ACTIVE_TAB', payload: 'chat' })}
          >
            💬 Chat
          </button>
          <button
            className={`mobile-tab ${activeTab === 'preview' ? 'active' : ''}`}
            onClick={() => dispatch({ type: 'SET_ACTIVE_TAB', payload: 'preview' })}
          >
            👁️ 3D Preview
            {sceneProducts.length > 0 && (
              <span className="mobile-tab-badge">{sceneProducts.length}</span>
            )}
          </button>
        </div>
      )}

      {/* ════ Main Layout ════ */}
      <main style={{ gridTemplateColumns: getGridColumns() }}>
        {/* ──── Chat Panel ──── */}
        <div className={`chat-container ${chatCollapsed ? 'collapsed' : ''} ${isMobile && activeTab !== 'chat' ? 'mobile-hidden' : ''}`}>
          {chatCollapsed ? (
            <button
              className="panel-expand-btn"
              onClick={() => dispatch({ type: 'TOGGLE_CHAT_COLLAPSED' })}
              title="Expand chat"
            >
              <span className="panel-expand-label">💬</span>
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <polyline points="9 18 15 12 9 6"/>
              </svg>
            </button>
          ) : (
            <>
              {/* Chat panel header with collapse button */}
              {!isMobile && (
                <div className="panel-header chat-panel-header">
                  <span className="panel-title">💬 Chat</span>
                  <div className="panel-header-actions">
                    <button
                      className={`panel-header-btn code-view-toggle ${showCodeView ? 'active' : ''}`}
                      onClick={() => setShowCodeView(v => !v)}
                      title={showCodeView ? 'Hide code' : 'Show code'}
                    >
                      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                        <polyline points="16 18 22 12 16 6"/>
                        <polyline points="8 6 2 12 8 18"/>
                      </svg>
                    </button>
                    <button
                      className="panel-collapse-btn"
                      onClick={() => dispatch({ type: 'TOGGLE_CHAT_COLLAPSED' })}
                      title="Collapse chat panel"
                    >
                      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                        <polyline points="15 18 9 12 15 6"/>
                      </svg>
                    </button>
                  </div>
                </div>
              )}

              <div
                className="chat-messages"
                ref={chatMessagesRef}
                onScroll={handleChatScroll}
              >
                {messages.length === 0 ? (
                  <div className="welcome-screen">
                    <div className="welcome-content">
                      <div className="welcome-hero">
                        <div className="welcome-icon">
                          <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
                            <path d="M12 2L2 7l10 5 10-5-10-5z"/>
                            <path d="M2 17l10 5 10-5"/>
                            <path d="M2 12l10 5 10-5"/>
                          </svg>
                        </div>
                        <h2>What do you want to build?</h2>
                        <p>Describe any product, part, or object — AI will generate a 3D model you can download and 3D print.</p>
                      </div>
                    </div>
                  </div>
                ) : (
                  messages.map((message) => (
                    <div key={message.id} className={`message ${message.type}`}>
                      {message.type === 'user' ? (
                        <div className="message-content user-message">
                          <div className="message-text">{message.content}</div>
                        </div>
                      ) : (
                        <div className="message-content assistant-message">
                          <div className="assistant-avatar">
                            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                              <path d="M12 2L2 7l10 5 10-5-10-5z"/>
                              <path d="M2 17l10 5 10-5"/>
                              <path d="M2 12l10 5 10-5"/>
                            </svg>
                          </div>
                          <div className="assistant-content">
                            {/* ── Building Status ── */}
                            {message.status === 'building' && (
                              <div className="building-status">
                                <div className="build-steps-live">
                                  {(!message.steps || message.steps.length === 0) && (
                                    <div className="step-item active">
                                      <span className="step-spinner"></span>
                                      <span className="step-text">Starting build pipeline...</span>
                                    </div>
                                  )}
                                  {message.steps && message.steps
                                    .sort((a, b) => a.step - b.step)
                                    .map((s, i) => (
                                      <div key={i} className={`step-item ${s.status}`}>
                                        {s.status === 'done' && <span className="step-check">✓</span>}
                                        {s.status === 'active' && <span className="step-spinner"></span>}
                                        {s.status === 'error' && <span className="step-error">✕</span>}
                                        {s.status === 'info' && <span className="step-info-icon">ℹ</span>}
                                        <div className="step-content">
                                          <span className="step-text">{s.message}</span>
                                          {s.detail && (s.status === 'active' || s.status === 'error' || s.status === 'info') && (
                                            <span className="step-detail">{s.detail}</span>
                                          )}
                                          {s.healing?.resolved && (
                                            <span className="step-healing-badge">🛡️ Self-healed</span>
                                          )}
                                        </div>
                                      </div>
                                    ))}

                                  {/* File activity indicator — shows files being created/modified */}
                                  {message.steps && message.steps.length > 0 && (
                                    <div className="file-activity">
                                      {message.steps.some(s => s.step >= 2 && s.step < 4) && (
                                        <div className="file-activity-item">
                                          <span className={`file-activity-icon ${message.steps.some(s => s.step >= 3) ? 'modified' : 'created'}`}>
                                            {message.steps.some(s => s.step >= 3) ? 'M' : 'U'}
                                          </span>
                                          <span className="file-activity-name">design.py</span>
                                          <span className="file-activity-status">
                                            {message.steps.some(s => s.step === 4 && s.status === 'done')
                                              ? 'executed'
                                              : message.steps.some(s => s.step === 4 && s.status === 'active')
                                                ? <><span className="file-activity-spinner" /> executing</>
                                                : message.steps.some(s => s.step === 3.5 && s.status === 'active')
                                                  ? <><span className="file-activity-spinner" /> AI reviewing</>
                                                  : message.steps.some(s => s.step === 3.5 && s.status === 'done')
                                                    ? 'reviewed'
                                                    : message.steps.some(s => s.step >= 3 && s.status === 'done')
                                                      ? 'validated'
                                                      : message.steps.some(s => (s.step === 2 || s.step === 2.1 || s.step === 2.2) && s.status === 'active')
                                                        ? <><span className="file-activity-spinner" /> writing</>
                                                        : 'generated'}
                                          </span>
                                        </div>
                                      )}
                                      {message.steps.some(s => s.step >= 5) && (
                                        <>
                                          <div className="file-activity-item">
                                            <span className="file-activity-icon exported">A</span>
                                            <span className="file-activity-name">model.stl</span>
                                            <span className="file-activity-status">
                                              {message.steps.some(s => s.step === 5 && s.status === 'done') ? 'exported' : <><span className="file-activity-spinner" /> exporting</>}
                                            </span>
                                          </div>
                                          <div className="file-activity-item">
                                            <span className="file-activity-icon exported">A</span>
                                            <span className="file-activity-name">model.step</span>
                                            <span className="file-activity-status">
                                              {message.steps.some(s => s.step === 5 && s.status === 'done') ? 'exported' : 'pending'}
                                            </span>
                                          </div>
                                        </>
                                      )}
                                    </div>
                                  )}

                                  {/* Healing history */}
                                  {message.healingLog && message.healingLog.length > 0 && (
                                    <div className="healing-history">
                                      <details>
                                        <summary className="healing-summary">
                                          🔧 {message.healingLog.length} error{message.healingLog.length > 1 ? 's' : ''} auto-fixed
                                        </summary>
                                        <div className="healing-entries">
                                          {message.healingLog.map((entry, hi) => (
                                            <div key={hi} className="healing-entry">
                                              <span className="healing-attempt">#{entry.attempt}</span>
                                              <span className="healing-msg">{entry.message}</span>
                                            </div>
                                          ))}
                                        </div>
                                      </details>
                                    </div>
                                  )}
                                </div>
                              </div>
                            )}

                            {/* ── Success ── */}
                            {message.status === 'success' && message.responseType === 'ask' && (
                              <div className="ask-response">
                                <div className="ask-content" dangerouslySetInnerHTML={{ __html: formatMarkdown(message.content) }} />
                              </div>
                            )}

                            {message.status === 'success' && message.responseType === 'plan' && message.plan && (
                              <div className="plan-response">
                                <div className="plan-header">
                                  <div className="plan-title">{message.plan.title || 'Build Plan'}</div>
                                  {message.plan.estimated_complexity && (
                                    <span className={`plan-complexity plan-complexity-${message.plan.estimated_complexity}`}>
                                      {message.plan.estimated_complexity}
                                    </span>
                                  )}
                                </div>
                                {message.plan.overview && (
                                  <div className="plan-overview">{message.plan.overview}</div>
                                )}
                                <div className="plan-steps">
                                  {message.plan.steps?.map((step, si) => (
                                    <div key={si} className="plan-step">
                                      <div className="plan-step-header">
                                        <span className="plan-step-number">{step.step}</span>
                                        <span className="plan-step-title">{step.title}</span>
                                        {step.depends_on && (
                                          <span className="plan-step-dep">after step {step.depends_on}</span>
                                        )}
                                      </div>
                                      <div className="plan-step-desc">{step.description}</div>
                                      <button
                                        className="plan-step-execute"
                                        onClick={() => {
                                          dispatch({ type: 'SET_INTERACTION_MODE', payload: 'agent' });
                                          handleBuild(step.prompt);
                                        }}
                                        disabled={status === 'building'}
                                      >
                                        ▶ Execute this step
                                      </button>
                                    </div>
                                  ))}
                                </div>
                                {message.plan.tips && message.plan.tips.length > 0 && (
                                  <div className="plan-tips">
                                    <div className="plan-tips-label">💡 Tips</div>
                                    <ul>
                                      {message.plan.tips.map((tip, ti) => (
                                        <li key={ti}>{tip}</li>
                                      ))}
                                    </ul>
                                  </div>
                                )}
                              </div>
                            )}

                            {message.status === 'success' && message.responseType === 'plan' && !message.plan && (
                              <div className="ask-response">
                                <div className="ask-content" dangerouslySetInnerHTML={{ __html: formatMarkdown(message.content) }} />
                              </div>
                            )}

                            {message.status === 'success' && message.result && !message.responseType && (
                              <div className="design-summary">
                                {/* Completed file activity — shows files created during build */}
                                {message.steps && message.steps.length > 0 && (
                                  <div className="file-activity completed">
                                    {message.steps.some(s => s.step >= 2) && (
                                      <div className="file-activity-item">
                                        <span className="file-activity-icon modified">M</span>
                                        <span className="file-activity-name">design.py</span>
                                        <span className="file-activity-status">executed</span>
                                      </div>
                                    )}
                                    {message.steps.some(s => s.step >= 5) && (
                                      <>
                                        <div className="file-activity-item">
                                          <span className="file-activity-icon exported">A</span>
                                          <span className="file-activity-name">model.stl</span>
                                          <span className="file-activity-status">exported</span>
                                        </div>
                                        <div className="file-activity-item">
                                          <span className="file-activity-icon exported">A</span>
                                          <span className="file-activity-name">model.step</span>
                                          <span className="file-activity-status">exported</span>
                                        </div>
                                      </>
                                    )}
                                  </div>
                                )}
                                {message.result.explanation?.design_intent && (
                                  <div className="summary-section">
                                    <div className="summary-label">🎯 What I Built</div>
                                    <div className="summary-text">{message.result.explanation.design_intent}</div>
                                  </div>
                                )}
                                {message.result.explanation?.features_created && (
                                  <div className="summary-section">
                                    <div className="summary-label">🔩 Features & Details</div>
                                    <div className="summary-text features-list">{message.result.explanation.features_created}</div>
                                  </div>
                                )}
                                {message.result.explanation?.dimensions_summary && (
                                  <div className="summary-section">
                                    <div className="summary-label">📐 Dimensions</div>
                                    <div className="summary-text">{message.result.explanation.dimensions_summary}</div>
                                  </div>
                                )}
                                {message.result.explanation?.construction_method && (
                                  <div className="summary-section">
                                    <div className="summary-label">🏗️ How It Was Built</div>
                                    <div className="summary-text">{message.result.explanation.construction_method}</div>
                                  </div>
                                )}
                                {!message.result.explanation?.design_intent && (
                                  <div className="summary-section">
                                    <div className="summary-text">{message.result.reasoning || "Your design is ready! Check the 3D viewer."}</div>
                                  </div>
                                )}

                                {/* Inline downloads */}
                                <div className="inline-downloads">
                                  {(message.result.stlUrl || message.result.files?.stl) && (
                                    <a
                                      href={(() => { const u = message.result.stlUrl || message.result.files.stl; return u.startsWith('http') ? u : `${API_HOST}${u}`; })()}
                                      download
                                      className="inline-download-link"
                                    >
                                      📥 STL (3D Print)
                                    </a>
                                  )}
                                  {(message.result.stepUrl || message.result.files?.step) && (
                                    <a
                                      href={(() => { const u = message.result.stepUrl || message.result.files.step; return u.startsWith('http') ? u : `${API_HOST}${u}`; })()}
                                      download
                                      className="inline-download-link"
                                    >
                                      📥 STEP (CAD)
                                    </a>
                                  )}
                                  {message.result.parametricScript && (
                                    <a
                                      href={(() => { const u = message.result.parametricScript; return u.startsWith('http') ? u : `${API_HOST}${u}`; })()}
                                      download
                                      className="inline-download-link"
                                    >
                                      📥 Python Script
                                    </a>
                                  )}
                                </div>

                                {/* AI Suggested Improvements */}
                                {message.result.explanation?.suggested_next_steps &&
                                  message.result.explanation.suggested_next_steps.length > 0 &&
                                  status !== 'building' && (
                                    <div className="suggestions-section">
                                      <div className="suggestions-label">💡 Want me to improve it?</div>
                                      <div className="suggestions-list">
                                        {message.result.explanation.suggested_next_steps.map((suggestion, si) => (
                                          <button
                                            key={si}
                                            className="suggestion-chip"
                                            onClick={() => handleBuild(suggestion)}
                                            disabled={status === 'building'}
                                          >
                                            <span className="suggestion-text">{suggestion}</span>
                                            <span className="suggestion-add">+ Add</span>
                                          </button>
                                        ))}
                                      </div>
                                    </div>
                                  )}
                              </div>
                            )}

                            {/* ── Error ── */}
                            {message.status === 'error' && (
                              <div className="error-message">
                                <div className="error-icon">⚠️</div>
                                <div className="error-body">
                                  <div className="error-title">Something went wrong</div>
                                  <div className="error-detail">{message.content}</div>
                                  <button
                                    className="retry-button"
                                    onClick={() => {
                                      const lastUserMsg = messages.filter(m => m.type === 'user').pop();
                                      if (lastUserMsg) handleBuild(lastUserMsg.content);
                                    }}
                                  >
                                    🔄 Try Again
                                  </button>
                                </div>
                              </div>
                            )}
                          </div>
                        </div>
                      )}
                    </div>
                  ))
                )}

                {/* Scroll-to-bottom indicator */}
                {!isAtBottom && messages.length > 0 && (
                  <button
                    className="scroll-to-bottom"
                    onClick={() => {
                      messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
                      setIsAtBottom(true);
                    }}
                  >
                    ↓ New messages
                  </button>
                )}
                <div ref={messagesEndRef} />
              </div>

              {/* ──── Code View Panel ──── */}
              {showCodeView && (
                <CodeView
                  code={currentDesign?.code || ''}
                  isBuilding={status === 'building'}
                  buildPhase={
                    messages.length > 0 && messages[messages.length - 1].steps
                      ? Math.max(...messages[messages.length - 1].steps.map(s => s.step), 0)
                      : 0
                  }
                  onClose={() => setShowCodeView(false)}
                />
              )}

              <PromptInput
                onBuild={handleBuild}
                onStopBuild={handleStopBuild}
                isBuilding={status === 'building'}
                hasExistingDesign={currentDesign !== null}
                modificationStep={state.modificationStep}
                uploadedFile={uploadedFile}
                selectedModel={state.selectedModel}
                onModelChange={(m) => dispatch({ type: 'SET_SELECTED_MODEL', payload: m })}
                interactionMode={state.interactionMode}
                onModeChange={(m) => dispatch({ type: 'SET_INTERACTION_MODE', payload: m })}
                onUndo={undo}
                canUndo={canUndo}
              />
            </>
          )}
        </div>

        {/* ──── Panel divider ──── */}
        {!isMobile && !chatCollapsed && !previewCollapsed && (
          <div className="panel-divider" />
        )}

        {/* ──── Preview Panel ──── */}
        <div className={`preview-panel ${previewCollapsed ? 'collapsed' : ''} ${isMobile && activeTab !== 'preview' ? 'mobile-hidden' : ''}`}>
          {previewCollapsed ? (
            <button
              className="panel-expand-btn"
              onClick={() => dispatch({ type: 'TOGGLE_PREVIEW_COLLAPSED' })}
              title="Expand preview"
            >
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <polyline points="15 18 9 12 15 6"/>
              </svg>
              <span className="panel-expand-label">👁️</span>
            </button>
          ) : (
            <>
              <div className="preview-header">
                <div className="preview-header-left">
                  {!isMobile && (
                    <button
                      className="panel-collapse-btn"
                      onClick={() => dispatch({ type: 'TOGGLE_PREVIEW_COLLAPSED' })}
                      title="Collapse preview panel"
                    >
                      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                        <polyline points="9 18 15 12 9 6"/>
                      </svg>
                    </button>
                  )}
                  <span>👁️ 3D Preview</span>
                </div>
                <div className="preview-header-right">
                  {parameters && parameters.length > 0 && (
                    <button
                      className={`view-mode-toggle ${showParameterPanel ? 'active' : ''}`}
                      onClick={() => dispatch({ type: 'TOGGLE_PARAMETER_PANEL' })}
                      title="Toggle parameter sliders"
                    >
                      🎛️ Parameters
                    </button>
                  )}
                  <span className="preview-status">
                    {sceneProducts.length === 0
                      ? 'Waiting for first design...'
                      : `● ${sceneProducts.length} ${sceneProducts.length === 1 ? 'product' : 'products'}`}
                  </span>
                </div>
              </div>

              <div className="preview-body">
                <div className="canvas-area">
                  {sceneProducts.length === 0 && status !== 'building' && !result ? (
                    <div className="empty-canvas">
                      <div className="empty-canvas-icon">
                        <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1" strokeLinecap="round">
                          <path d="M12 2L2 7l10 5 10-5-10-5z" opacity="0.3"/>
                          <path d="M2 17l10 5 10-5" opacity="0.2"/>
                          <path d="M2 12l10 5 10-5" opacity="0.25"/>
                        </svg>
                      </div>
                      <p className="empty-canvas-text">Your 3D model will appear here</p>
                      <p className="empty-canvas-hint">Type a description in the chat to get started</p>
                    </div>
                  ) : (
                    <MultiProductCanvas
                      sceneId={currentScene?.sceneId}
                      initialProducts={sceneProducts}
                    />
                  )}
                  {status === 'building' && sceneProducts.length === 0 && (
                    <div className="canvas-loading">
                      <div className="canvas-loading-cube">
                        <div className="cube-face front"></div>
                        <div className="cube-face back"></div>
                        <div className="cube-face right"></div>
                        <div className="cube-face left"></div>
                        <div className="cube-face top"></div>
                        <div className="cube-face bottom"></div>
                      </div>
                      <p>Generating 3D model...</p>
                    </div>
                  )}
                </div>

                {/* ── Parameter Sliders ── */}
                {showParameterPanel && parameters && parameters.length > 0 && (
                  <div className="parameter-panel-wrapper">
                    <ParameterPanel
                      parameters={parameters}
                      buildId={currentBuildId}
                      onUpdate={handleRebuild}
                      onClose={() => dispatch({ type: 'TOGGLE_PARAMETER_PANEL' })}
                    />
                  </div>
                )}

                {/* ── Export Panel (compact) ── */}
                {hasDesign && result && (
                  <div className="export-panel-wrapper">
                    <ExportPanel
                      buildId={result.buildId}
                      stlUrl={result.stlUrl || result.files?.stl}
                      stepUrl={result.stepUrl || result.files?.step}
                      parametricScript={result.parametricScript}
                      onShare={(buildId) => uploadToS3(buildId)}
                      sceneProducts={sceneProducts}
                      currentDesign={currentDesign}
                      onVersionRestore={(restored) => {
                        dispatch({ type: 'SET_BUILD_ID', payload: restored.buildId });
                        dispatch({
                          type: 'SET_RESULT',
                          payload: {
                            ...result,
                            buildId: restored.buildId,
                            stlUrl: restored.stlFile,
                            stepUrl: restored.stepFile,
                            design: restored.design,
                          },
                        });
                      }}
                      sceneId={currentScene?.sceneId}
                      onSceneSync={(sceneState, updatedBy) => {
                        if (sceneState?.products) {
                          dispatch({ type: 'REPLACE_ALL_PRODUCTS', payload: sceneState.products });
                        }
                      }}
                    />
                  </div>
                )}


              </div>
            </>
          )}
        </div>
      </main>

      {showProjectBrowser && (
        <ProjectBrowser
          onSelectProject={handleProjectSelect}
          onClose={() => dispatch({ type: 'SET_SHOW_PROJECT_BROWSER', payload: false })}
          onNewProject={handleNewProject}
        />
      )}
    </div>
  );
}

/** Route wrapper: handles auth gate + routing */
function AppRouter() {
  const { user, loading: authLoading } = useAuth();

  if (authLoading) {
    return (
      <div className="App" style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100vh', background: '#0a0e14' }}>
        <div style={{ textAlign: 'center', color: '#8b949e' }}>
          <div className="auth-loading-spinner" />
          <p style={{ marginTop: 16, fontSize: 14 }}>Loading...</p>
        </div>
      </div>
    );
  }

  if (!user) return <AuthScreen />;

  return (
    <>
      <CookieConsent />
      <Routes>
        <Route path="/" element={<App />} />
        <Route path="/project/:projectId" element={<ProjectLoader />} />
        <Route path="/pricing" element={<PricingPage onClose={null} />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </>
  );
}

/** Tiny wrapper that reads :projectId from the URL, loads it, then renders App */
function ProjectLoader() {
  const { projectId } = useParams();
  const { handleProjectSelect } = useBuild();
  const [loaded, setLoaded] = useState(false);

  useEffect(() => {
    if (projectId && !loaded) {
      handleProjectSelect({ id: projectId });
      setLoaded(true);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [projectId, loaded]);

  return <App />;
}

export default AppRouter;
