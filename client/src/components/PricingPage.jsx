import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { createCheckoutSession } from '../api';
import './PricingPage.css';

const PLANS = [
  {
    id: 'free',
    name: 'Free',
    tagline: 'Get started with AI-powered CAD',
    monthlyPrice: 0,
    yearlyPrice: 0,
    accent: '#8b949e',
    features: [
      { text: '5 builds per day', included: true },
      { text: 'STL export', included: true },
      { text: 'Basic product templates', included: true },
      { text: 'Community support', included: true },
      { text: 'STEP export', included: false },
      { text: 'Parametric editing', included: false },
      { text: 'Priority AI processing', included: false },
      { text: 'Custom product templates', included: false },
    ],
    cta: 'Current Plan',
    ctaVariant: 'outline',
  },
  {
    id: 'pro',
    name: 'Pro',
    tagline: 'For professionals & small teams',
    monthlyPrice: 29,
    yearlyPrice: 24,
    accent: '#3b82f6',
    popular: true,
    features: [
      { text: '100 builds per day', included: true },
      { text: 'STL & STEP export', included: true },
      { text: 'All product templates (98+)', included: true },
      { text: 'Parametric editing & sliders', included: true },
      { text: 'Priority AI processing', included: true },
      { text: 'GLB / 3MF export', included: true },
      { text: 'Project history (unlimited)', included: true },
      { text: 'Email support', included: true },
    ],
    cta: 'Upgrade to Pro',
    ctaVariant: 'primary',
  },
  {
    id: 'enterprise',
    name: 'Enterprise',
    tagline: 'For organizations at scale',
    monthlyPrice: 99,
    yearlyPrice: 79,
    accent: '#8b5cf6',
    features: [
      { text: 'Unlimited builds', included: true },
      { text: 'All export formats', included: true },
      { text: 'Custom product templates', included: true },
      { text: 'API access & webhooks', included: true },
      { text: 'Team collaboration', included: true },
      { text: 'SSO & SAML', included: true },
      { text: 'Dedicated AI capacity', included: true },
      { text: 'Priority support & SLA', included: true },
    ],
    cta: 'Contact Sales',
    ctaVariant: 'glow',
  },
];

const FAQ = [
  {
    q: 'Can I switch plans at any time?',
    a: 'Yes — upgrade or downgrade whenever you like. Changes take effect immediately and billing is prorated.',
  },
  {
    q: 'What counts as a "build"?',
    a: 'Each time you send a prompt and the AI generates a new CAD model counts as one build. Parametric edits via sliders do not count.',
  },
  {
    q: 'Do you offer discounts for students or educators?',
    a: 'Absolutely. Reach out to us at support@inventa.ai with your .edu email and we\'ll set you up with 50% off Pro.',
  },
  {
    q: 'What happens if I exceed my daily build limit?',
    a: 'You\'ll be prompted to upgrade. Existing models and exports remain fully accessible.',
  },
];

export default function PricingPage({ onClose }) {
  const [billing, setBilling] = useState('yearly');
  const [openFaq, setOpenFaq] = useState(null);
  const [checkoutLoading, setCheckoutLoading] = useState(null);
  const navigate = useNavigate();

  const handleClose = onClose || (() => navigate('/'));

  const handleSubscribe = async (planId) => {
    if (planId === 'free') return;
    if (planId === 'enterprise') {
      window.location.href = 'mailto:sales@inventa.ai?subject=Enterprise%20Plan%20Inquiry';
      return;
    }
    setCheckoutLoading(planId);
    try {
      const { url } = await createCheckoutSession(planId, billing);
      if (url) window.location.href = url;
    } catch (err) {
      console.error('Checkout error:', err);
      alert(err.message || 'Could not start checkout. Please try again.');
    } finally {
      setCheckoutLoading(null);
    }
  };

  return (
    <div className="pricing-screen">
      {/* Background effects (matches AuthScreen) */}
      <div className="pricing-bg">
        <div className="pricing-bg-grid" />
        <div className="pricing-bg-glow pricing-bg-glow-1" />
        <div className="pricing-bg-glow pricing-bg-glow-2" />
        <div className="pricing-bg-glow pricing-bg-glow-3" />
      </div>

      {/* Close button */}
      <button className="pricing-close-btn" onClick={handleClose} title="Close">
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <line x1="18" y1="6" x2="6" y2="18" />
          <line x1="6" y1="6" x2="18" y2="18" />
        </svg>
      </button>

      <div className="pricing-container">
        {/* Header */}
        <div className="pricing-header">
          <div className="pricing-badge">Pricing</div>
          <h1 className="pricing-title">
            Choose the plan that fits<br />your workflow
          </h1>
          <p className="pricing-subtitle">
            From quick prototypes to full production pipelines — inventa.AI scales with you.
          </p>

          {/* Billing toggle */}
          <div className="pricing-toggle-wrap">
            <button
              className={`pricing-toggle-btn ${billing === 'monthly' ? 'active' : ''}`}
              onClick={() => setBilling('monthly')}
            >
              Monthly
            </button>
            <button
              className={`pricing-toggle-btn ${billing === 'yearly' ? 'active' : ''}`}
              onClick={() => setBilling('yearly')}
            >
              Yearly
              <span className="pricing-save-badge">Save 20%</span>
            </button>
          </div>
        </div>

        {/* Plan cards */}
        <div className="pricing-cards">
          {PLANS.map((plan) => {
            const price = billing === 'monthly' ? plan.monthlyPrice : plan.yearlyPrice;
            return (
              <div
                key={plan.id}
                className={`pricing-card ${plan.popular ? 'pricing-card-popular' : ''}`}
                style={{ '--plan-accent': plan.accent }}
              >
                {plan.popular && (
                  <div className="pricing-popular-tag">Most Popular</div>
                )}
                <div className="pricing-card-top">
                  <h3 className="pricing-plan-name">{plan.name}</h3>
                  <p className="pricing-plan-tagline">{plan.tagline}</p>
                  <div className="pricing-price">
                    {price === 0 ? (
                      <span className="pricing-price-amount">Free</span>
                    ) : (
                      <>
                        <span className="pricing-price-currency">$</span>
                        <span className="pricing-price-amount">{price}</span>
                        <span className="pricing-price-period">
                          / mo{billing === 'yearly' ? ' billed yearly' : ''}
                        </span>
                      </>
                    )}
                  </div>
                </div>

                <div className="pricing-card-features">
                  {plan.features.map((f, i) => (
                    <div key={i} className={`pricing-feature ${f.included ? '' : 'pricing-feature-disabled'}`}>
                      {f.included ? (
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                          <polyline points="20 6 9 17 4 12" />
                        </svg>
                      ) : (
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                          <line x1="18" y1="6" x2="6" y2="18" />
                          <line x1="6" y1="6" x2="18" y2="18" />
                        </svg>
                      )}
                      <span>{f.text}</span>
                    </div>
                  ))}
                </div>

                <button
                  className={`pricing-cta pricing-cta-${plan.ctaVariant}`}
                  onClick={() => handleSubscribe(plan.id)}
                  disabled={checkoutLoading === plan.id}
                >
                  {checkoutLoading === plan.id ? 'Redirecting…' : plan.cta}
                </button>
              </div>
            );
          })}
        </div>

        {/* FAQ Section */}
        <div className="pricing-faq">
          <h2 className="pricing-faq-title">Frequently Asked Questions</h2>
          <div className="pricing-faq-list">
            {FAQ.map((item, i) => (
              <div
                key={i}
                className={`pricing-faq-item ${openFaq === i ? 'open' : ''}`}
              >
                <button
                  className="pricing-faq-question"
                  onClick={() => setOpenFaq(openFaq === i ? null : i)}
                >
                  <span>{item.q}</span>
                  <svg
                    className="pricing-faq-chevron"
                    width="16" height="16" viewBox="0 0 24 24"
                    fill="none" stroke="currentColor" strokeWidth="2"
                  >
                    <polyline points="6 9 12 15 18 9" />
                  </svg>
                </button>
                <div className="pricing-faq-answer">
                  <p>{item.a}</p>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Footer */}
        <div className="pricing-page-footer">
          <p>All plans include a 14-day money-back guarantee. No credit card required for Free.</p>
        </div>
      </div>
    </div>
  );
}
