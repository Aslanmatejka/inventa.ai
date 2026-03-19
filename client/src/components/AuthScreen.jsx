import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { supabase } from '../supabaseClient';
import './AuthScreen.css';

function AuthScreen() {
  const { signIn, signUp, signInWithGoogle, signInWithGitHub, resetPassword, updatePassword } = useAuth();

  // Detect /reset-password path for Supabase recovery flow
  const isResetPath = window.location.pathname === '/reset-password';
  const [mode, setMode] = useState(isResetPath ? 'new-password' : 'login'); // 'login' | 'register' | 'forgot' | 'new-password'
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [fullName, setFullName] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmNewPassword, setConfirmNewPassword] = useState('');
  const [error, setError] = useState('');
  const [message, setMessage] = useState('');
  const [loading, setLoading] = useState(false);
  const [showPassword, setShowPassword] = useState(false);

  // Listen for Supabase PASSWORD_RECOVERY event
  useEffect(() => {
    const { data: { subscription } } = supabase.auth.onAuthStateChange((event) => {
      if (event === 'PASSWORD_RECOVERY') {
        setMode('new-password');
        setError('');
        setMessage('');
      }
    });
    return () => subscription.unsubscribe();
  }, []);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setMessage('');
    setLoading(true);

    try {
      if (mode === 'login') {
        const { error: err } = await signIn(email, password);
        if (err) throw err;
      } else if (mode === 'register') {
        if (password !== confirmPassword) {
          throw new Error('Passwords do not match');
        }
        if (password.length < 6) {
          throw new Error('Password must be at least 6 characters');
        }
        const { error: err } = await signUp(email, password, fullName);
        if (err) throw err;
        setMessage('Account created! Check your email to verify your account.');
        setMode('login');
      } else if (mode === 'forgot') {
        const { error: err } = await resetPassword(email);
        if (err) throw err;
        setMessage('Password reset email sent! Check your inbox.');
        setMode('login');
      } else if (mode === 'new-password') {
        if (newPassword.length < 6) {
          throw new Error('Password must be at least 6 characters');
        }
        if (newPassword !== confirmNewPassword) {
          throw new Error('Passwords do not match');
        }
        const { error: err } = await updatePassword(newPassword);
        if (err) throw err;
        setMessage('Password updated successfully! You can now sign in.');
        // Clean up URL and switch to login
        window.history.replaceState(null, '', '/');
        setMode('login');
        setNewPassword('');
        setConfirmNewPassword('');
      }
    } catch (err) {
      setError(err.message || 'An error occurred');
    } finally {
      setLoading(false);
    }
  };

  const handleOAuth = async (provider) => {
    setError('');
    try {
      const fn = provider === 'google' ? signInWithGoogle : signInWithGitHub;
      const { error: err } = await fn();
      if (err) throw err;
    } catch (err) {
      setError(err.message || 'OAuth login failed');
    }
  };

  const switchMode = (newMode) => {
    setMode(newMode);
    setError('');
    setMessage('');
  };

  return (
    <div className="auth-screen">
      {/* Background decoration */}
      <div className="auth-bg">
        <div className="auth-bg-grid" />
        <div className="auth-bg-glow auth-bg-glow-1" />
        <div className="auth-bg-glow auth-bg-glow-2" />
      </div>

      <div className="auth-container">
        {/* Logo / Brand */}
        <div className="auth-brand">
          <div className="auth-logo">
            <svg width="40" height="40" viewBox="0 0 40 40" fill="none">
              <rect width="40" height="40" rx="10" fill="#3b82f6" />
              <path d="M12 28V12h5l5 8 5-8h5v16h-4V18l-4 6h-4l-4-6v10h-4z" fill="white" />
            </svg>
          </div>
          <h1>inventa.AI</h1>
          <p className="auth-subtitle">AI-Powered CAD Design Platform</p>
        </div>

        {/* Auth Card */}
        <div className="auth-card">
          <div className="auth-card-header">
            <h2>
              {mode === 'login' && 'Welcome back'}
              {mode === 'register' && 'Create account'}
              {mode === 'forgot' && 'Reset password'}
              {mode === 'new-password' && 'Set new password'}
            </h2>
            <p>
              {mode === 'login' && 'Sign in to your account to continue'}
              {mode === 'register' && 'Start building 3D models with AI'}
              {mode === 'forgot' && 'Enter your email to receive a reset link'}
              {mode === 'new-password' && 'Choose a new password for your account'}
            </p>
          </div>

          {/* OAuth Buttons */}
          {(mode !== 'forgot' && mode !== 'new-password') && (
            <div className="auth-oauth">
              <button
                className="auth-oauth-btn"
                onClick={() => handleOAuth('google')}
                disabled={loading}
                type="button"
              >
                <svg width="18" height="18" viewBox="0 0 24 24">
                  <path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92a5.06 5.06 0 01-2.2 3.32v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.1z" fill="#4285F4"/>
                  <path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" fill="#34A853"/>
                  <path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" fill="#FBBC05"/>
                  <path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" fill="#EA4335"/>
                </svg>
                Continue with Google
              </button>
              <button
                className="auth-oauth-btn"
                onClick={() => handleOAuth('github')}
                disabled={loading}
                type="button"
              >
                <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor">
                  <path d="M12 0C5.37 0 0 5.37 0 12c0 5.31 3.435 9.795 8.205 11.385.6.105.825-.255.825-.57 0-.285-.015-1.23-.015-2.235-3.015.555-3.795-.735-4.035-1.41-.135-.345-.72-1.41-1.23-1.695-.42-.225-1.02-.78-.015-.795.945-.015 1.62.87 1.845 1.23 1.08 1.815 2.805 1.305 3.495.99.105-.78.42-1.305.765-1.605-2.67-.3-5.46-1.335-5.46-5.925 0-1.305.465-2.385 1.23-3.225-.12-.3-.54-1.53.12-3.18 0 0 1.005-.315 3.3 1.23.96-.27 1.98-.405 3-.405s2.04.135 3 .405c2.295-1.56 3.3-1.23 3.3-1.23.66 1.65.24 2.88.12 3.18.765.84 1.23 1.905 1.23 3.225 0 4.605-2.805 5.625-5.475 5.925.435.375.81 1.095.81 2.22 0 1.605-.015 2.895-.015 3.3 0 .315.225.69.825.57A12.02 12.02 0 0024 12c0-6.63-5.37-12-12-12z"/>
                </svg>
                Continue with GitHub
              </button>
            </div>
          )}

          {(mode !== 'forgot' && mode !== 'new-password') && (
            <div className="auth-divider">
              <span>or continue with email</span>
            </div>
          )}

          {/* Error / Success Messages */}
          {error && (
            <div className="auth-alert auth-alert-error">
              <svg width="16" height="16" viewBox="0 0 16 16" fill="currentColor">
                <path d="M8 1a7 7 0 100 14A7 7 0 008 1zM7 4.5a1 1 0 112 0v3a1 1 0 11-2 0v-3zM8 11.5a1 1 0 100-2 1 1 0 000 2z"/>
              </svg>
              {error}
            </div>
          )}
          {message && (
            <div className="auth-alert auth-alert-success">
              <svg width="16" height="16" viewBox="0 0 16 16" fill="currentColor">
                <path d="M8 1a7 7 0 100 14A7 7 0 008 1zm3.7 5.3a.75.75 0 00-1.06-1.06L7 8.88 5.36 7.24a.75.75 0 10-1.06 1.06l2.25 2.25a.75.75 0 001.06 0l4.09-4.25z"/>
              </svg>
              {message}
            </div>
          )}

          {/* Form */}
          <form onSubmit={handleSubmit} className="auth-form">
            {mode === 'register' && (
              <div className="auth-field">
                <label htmlFor="fullName">Full Name</label>
                <div className="auth-input-wrapper">
                  <svg className="auth-input-icon" width="16" height="16" viewBox="0 0 16 16" fill="currentColor">
                    <path d="M8 8a3 3 0 100-6 3 3 0 000 6zM2 14s-1 0-1-1 1-4 7-4 7 3 7 4-1 1-1 1H2z"/>
                  </svg>
                  <input
                    id="fullName"
                    type="text"
                    placeholder="John Doe"
                    value={fullName}
                    onChange={(e) => setFullName(e.target.value)}
                    required
                    autoComplete="name"
                  />
                </div>
              </div>
            )}

            {/* Email field — not shown on new-password mode */}
            {mode !== 'new-password' && (
            <div className="auth-field">
              <label htmlFor="email">Email address</label>
              <div className="auth-input-wrapper">
                <svg className="auth-input-icon" width="16" height="16" viewBox="0 0 16 16" fill="currentColor">
                  <path d="M2.5 3A1.5 1.5 0 001 4.5v.793c.026.009.051.02.076.032L7.674 8.51c.206.1.446.1.652 0l6.598-3.185A.755.755 0 0115 5.293V4.5A1.5 1.5 0 0013.5 3h-11z"/>
                  <path d="M15 6.954L8.978 9.86a2.25 2.25 0 01-1.956 0L1 6.954V11.5A1.5 1.5 0 002.5 13h11a1.5 1.5 0 001.5-1.5V6.954z"/>
                </svg>
                <input
                  id="email"
                  type="email"
                  placeholder="you@example.com"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  required
                  autoComplete="email"
                  autoFocus
                />
              </div>
            </div>
            )}

            {(mode === 'login' || mode === 'register') && (
              <div className="auth-field">
                <div className="auth-label-row">
                  <label htmlFor="password">Password</label>
                  {mode === 'login' && (
                    <button
                      type="button"
                      className="auth-link-btn"
                      onClick={() => switchMode('forgot')}
                    >
                      Forgot password?
                    </button>
                  )}
                </div>
                <div className="auth-input-wrapper">
                  <svg className="auth-input-icon" width="16" height="16" viewBox="0 0 16 16" fill="currentColor">
                    <path d="M8 1a2 2 0 00-2 2v4H5a2 2 0 00-2 2v3a2 2 0 002 2h6a2 2 0 002-2V9a2 2 0 00-2-2h-1V3a2 2 0 00-2-2zm1 5V3a1 1 0 10-2 0v3h2z"/>
                  </svg>
                  <input
                    id="password"
                    type={showPassword ? 'text' : 'password'}
                    placeholder={mode === 'register' ? 'Min. 6 characters' : 'Your password'}
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    required
                    minLength={6}
                    autoComplete={mode === 'login' ? 'current-password' : 'new-password'}
                  />
                  <button
                    type="button"
                    className="auth-toggle-password"
                    onClick={() => setShowPassword(!showPassword)}
                    tabIndex={-1}
                  >
                    {showPassword ? (
                      <svg width="16" height="16" viewBox="0 0 16 16" fill="currentColor">
                        <path d="M13.359 11.238C15.06 9.72 16 8 16 8s-3-5.5-8-5.5a7.028 7.028 0 00-2.79.588l.77.771A5.944 5.944 0 018 3.5c2.12 0 3.879 1.168 5.168 2.457A13.134 13.134 0 0114.828 8c-.058.087-.122.183-.195.288-.335.48-.83 1.12-1.465 1.755-.165.165-.337.328-.517.486l.708.709z"/>
                        <path d="M11.297 9.176a3.5 3.5 0 00-4.474-4.474l.823.823a2.5 2.5 0 012.829 2.829l.822.822zm-2.943 1.299l.822.822a3.5 3.5 0 01-4.474-4.474l.823.823a2.5 2.5 0 002.829 2.829z"/>
                        <path d="M3.35 5.47c-.18.16-.353.322-.518.487A13.134 13.134 0 001.172 8l.195.288c.335.48.83 1.12 1.465 1.755C4.121 11.332 5.881 12.5 8 12.5c.716 0 1.39-.133 2.02-.36l.77.772A7.029 7.029 0 018 13.5C3 13.5 0 8 0 8s.939-1.721 2.641-3.238l.708.709zM13.646 14.354l-12-12 .708-.708 12 12-.708.708z"/>
                      </svg>
                    ) : (
                      <svg width="16" height="16" viewBox="0 0 16 16" fill="currentColor">
                        <path d="M16 8s-3-5.5-8-5.5S0 8 0 8s3 5.5 8 5.5S16 8 16 8zM1.173 8a13.133 13.133 0 011.66-2.043C4.12 4.668 5.88 3.5 8 3.5c2.12 0 3.879 1.168 5.168 2.457A13.133 13.133 0 0114.828 8c-.058.087-.122.183-.195.288a13.134 13.134 0 01-1.465 1.755C11.879 11.332 10.119 12.5 8 12.5c-2.12 0-3.879-1.168-5.168-2.457A13.134 13.134 0 011.172 8z"/>
                        <path d="M8 5.5a2.5 2.5 0 100 5 2.5 2.5 0 000-5zM4.5 8a3.5 3.5 0 117 0 3.5 3.5 0 01-7 0z"/>
                      </svg>
                    )}
                  </button>
                </div>
              </div>
            )}

            {mode === 'register' && (
              <div className="auth-field">
                <label htmlFor="confirmPassword">Confirm Password</label>
                <div className="auth-input-wrapper">
                  <svg className="auth-input-icon" width="16" height="16" viewBox="0 0 16 16" fill="currentColor">
                    <path d="M8 1a2 2 0 00-2 2v4H5a2 2 0 00-2 2v3a2 2 0 002 2h6a2 2 0 002-2V9a2 2 0 00-2-2h-1V3a2 2 0 00-2-2zm1 5V3a1 1 0 10-2 0v3h2z"/>
                  </svg>
                  <input
                    id="confirmPassword"
                    type={showPassword ? 'text' : 'password'}
                    placeholder="Repeat your password"
                    value={confirmPassword}
                    onChange={(e) => setConfirmPassword(e.target.value)}
                    required
                    minLength={6}
                    autoComplete="new-password"
                  />
                </div>
              </div>
            )}

            {/* New Password fields (password recovery flow) */}
            {mode === 'new-password' && (
              <>
                <div className="auth-field">
                  <label htmlFor="newPassword">New Password</label>
                  <div className="auth-input-wrapper">
                    <svg className="auth-input-icon" width="16" height="16" viewBox="0 0 16 16" fill="currentColor">
                      <path d="M8 1a2 2 0 00-2 2v4H5a2 2 0 00-2 2v3a2 2 0 002 2h6a2 2 0 002-2V9a2 2 0 00-2-2h-1V3a2 2 0 00-2-2zm1 5V3a1 1 0 10-2 0v3h2z"/>
                    </svg>
                    <input
                      id="newPassword"
                      type={showPassword ? 'text' : 'password'}
                      placeholder="Min. 6 characters"
                      value={newPassword}
                      onChange={(e) => setNewPassword(e.target.value)}
                      required
                      minLength={6}
                      autoComplete="new-password"
                      autoFocus
                    />
                    <button
                      type="button"
                      className="auth-toggle-password"
                      onClick={() => setShowPassword(!showPassword)}
                      tabIndex={-1}
                    >
                      {showPassword ? '🙈' : '👁️'}
                    </button>
                  </div>
                </div>
                <div className="auth-field">
                  <label htmlFor="confirmNewPassword">Confirm New Password</label>
                  <div className="auth-input-wrapper">
                    <svg className="auth-input-icon" width="16" height="16" viewBox="0 0 16 16" fill="currentColor">
                      <path d="M8 1a2 2 0 00-2 2v4H5a2 2 0 00-2 2v3a2 2 0 002 2h6a2 2 0 002-2V9a2 2 0 00-2-2h-1V3a2 2 0 00-2-2zm1 5V3a1 1 0 10-2 0v3h2z"/>
                    </svg>
                    <input
                      id="confirmNewPassword"
                      type={showPassword ? 'text' : 'password'}
                      placeholder="Repeat new password"
                      value={confirmNewPassword}
                      onChange={(e) => setConfirmNewPassword(e.target.value)}
                      required
                      minLength={6}
                      autoComplete="new-password"
                    />
                  </div>
                </div>
              </>
            )}

            <button
              type="submit"
              className="auth-submit-btn"
              disabled={loading}
            >
              {loading ? (
                <span className="auth-spinner" />
              ) : (
                <>
                  {mode === 'login' && 'Sign In'}
                  {mode === 'register' && 'Create Account'}
                  {mode === 'forgot' && 'Send Reset Link'}
                  {mode === 'new-password' && 'Update Password'}
                </>
              )}
            </button>
          </form>

          {/* Mode Switch */}
          <div className="auth-footer">
            {mode === 'login' && (
              <p>
                Don't have an account?{' '}
                <button type="button" className="auth-link-btn" onClick={() => switchMode('register')}>
                  Sign up
                </button>
              </p>
            )}
            {mode === 'register' && (
              <p>
                Already have an account?{' '}
                <button type="button" className="auth-link-btn" onClick={() => switchMode('login')}>
                  Sign in
                </button>
              </p>
            )}
            {mode === 'forgot' && (
              <p>
                Remember your password?{' '}
                <button type="button" className="auth-link-btn" onClick={() => switchMode('login')}>
                  Back to sign in
                </button>
              </p>
            )}
            {mode === 'new-password' && (
              <p>
                <button type="button" className="auth-link-btn" onClick={() => { window.history.replaceState(null, '', '/'); switchMode('login'); }}>
                  Back to sign in
                </button>
              </p>
            )}
          </div>
        </div>

        {/* Features */}
        <div className="auth-features">
          <div className="auth-feature">
            <svg width="20" height="20" viewBox="0 0 20 20" fill="none" stroke="#3b82f6" strokeWidth="1.5">
              <rect x="3" y="3" width="14" height="14" rx="2" />
              <path d="M7 10l2 2 4-4" />
            </svg>
            <span>Natural language to 3D CAD</span>
          </div>
          <div className="auth-feature">
            <svg width="20" height="20" viewBox="0 0 20 20" fill="none" stroke="#10b981" strokeWidth="1.5">
              <path d="M10 2v16M2 10h16" />
              <circle cx="10" cy="10" r="7" />
            </svg>
            <span>Parametric design with live sliders</span>
          </div>
          <div className="auth-feature">
            <svg width="20" height="20" viewBox="0 0 20 20" fill="none" stroke="#f59e0b" strokeWidth="1.5">
              <path d="M4 16l4-4 4 4 4-8" />
              <rect x="2" y="2" width="16" height="16" rx="2" />
            </svg>
            <span>Export to STEP, STL & more</span>
          </div>
        </div>
      </div>
    </div>
  );
}

export default AuthScreen;
