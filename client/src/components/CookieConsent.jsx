import React, { useEffect, useState } from 'react';
import './CookieConsent.css';

/**
 * Minimal GDPR-friendly cookie banner.
 * Only dismisses once the user acknowledges. Stores choice in localStorage.
 */
export default function CookieConsent() {
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    try {
      const choice = localStorage.getItem('inventa.cookieConsent');
      if (!choice) setVisible(true);
    } catch {
      setVisible(true);
    }
  }, []);

  const accept = () => {
    try { localStorage.setItem('inventa.cookieConsent', 'accepted'); } catch {}
    setVisible(false);
  };

  const essentialOnly = () => {
    try { localStorage.setItem('inventa.cookieConsent', 'essential'); } catch {}
    setVisible(false);
  };

  if (!visible) return null;

  return (
    <div className="cookie-consent" role="dialog" aria-label="Cookie consent">
      <div className="cookie-consent-text">
        We use essential cookies for sign-in and session management. See our{' '}
        <a href="/PRIVACY.md" target="_blank" rel="noopener noreferrer">Privacy Policy</a>{' '}
        for details. No tracking or advertising cookies are set.
      </div>
      <div className="cookie-consent-actions">
        <button className="cookie-consent-btn secondary" onClick={essentialOnly}>
          Essential only
        </button>
        <button className="cookie-consent-btn primary" onClick={accept}>
          Got it
        </button>
      </div>
    </div>
  );
}
