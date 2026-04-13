import React from 'react';

class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, errorInfo) {
    console.error('ErrorBoundary caught:', error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div style={{
          minHeight: '100vh',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          background: '#0e1117',
          color: '#e8eaed',
          padding: '2rem',
          fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif'
        }}>
          <div style={{
            maxWidth: '600px',
            background: '#1a1d24',
            padding: '2rem',
            borderRadius: '8px',
            border: '1px solid #2d3139'
          }}>
            <h1 style={{ color: '#ff4757', margin: '0 0 1rem' }}>
              ⚠️ Something went wrong
            </h1>
            <p style={{ color: '#8b8d98', marginBottom: '1rem' }}>
              The application encountered an unexpected error. Please refresh the page to try again.
            </p>
            <details style={{ 
              background: '#0e1013', 
              padding: '1rem', 
              borderRadius: '4px',
              border: '1px solid #2d3139',
              marginBottom: '1rem'
            }}>
              <summary style={{ cursor: 'pointer', color: '#4a9eff' }}>
                Error details
              </summary>
              <pre style={{ 
                margin: '1rem 0 0', 
                fontSize: '0.85rem', 
                color: '#ff4757',
                whiteSpace: 'pre-wrap',
                wordBreak: 'break-word'
              }}>
                {this.state.error && this.state.error.toString()}
              </pre>
            </details>
            <button
              onClick={() => window.location.reload()}
              style={{
                background: '#4a9eff',
                color: '#fff',
                border: 'none',
                padding: '0.75rem 1.5rem',
                borderRadius: '6px',
                cursor: 'pointer',
                fontSize: '1rem',
                fontWeight: '500'
              }}
            >
              🔄 Reload Page
            </button>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

export default ErrorBoundary;
