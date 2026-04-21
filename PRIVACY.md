# Privacy Policy — inventa.ai

_Last updated: 2026-04-21_

This is a placeholder Privacy Policy. Replace with production text reviewed
by legal counsel.

## 1. Data we collect

- **Account data**: email address, hashed password (via Supabase Auth).
- **Prompt data**: natural-language design prompts you submit.
- **Generated artifacts**: STL/STEP files, parametric scripts, parameters.
- **Usage data**: build counts, timestamps, error events.
- **Payment data**: handled entirely by Stripe; we store only the Stripe
  customer ID.

## 2. How we use it

- Generating CAD output in response to your prompts.
- Debugging failures via the self-heal loop and error log.
- Aggregate analytics for product improvement.
- Preventing abuse (rate limiting, fraud detection).

## 3. Third-party processors

| Processor  | Purpose                              | Data shared              |
|------------|--------------------------------------|--------------------------|
| Anthropic  | LLM inference (Claude API)           | Prompt text, code output |
| Supabase   | Authentication + database            | Email, project data      |
| Stripe     | Payment processing                   | Billing details          |
| Render     | Application hosting                  | All request/response data |

## 4. Data retention

- Generated CAD artifacts: 7 days in `/exports/` cache, indefinite in DB.
- Error logs: rotated, max 15 MB retained.
- Account data: retained until account deletion is requested.

## 5. Your rights (GDPR / CCPA)

Email privacy@inventa.ai to:
- Export all data associated with your account.
- Request permanent deletion.
- Object to processing for analytics.

## 6. Cookies

We use essential cookies for session management only. No advertising or
analytics cookies are set without your consent.

## 7. Security

Data in transit is TLS-encrypted. Data at rest uses provider-managed
encryption (Supabase, Stripe). User passwords are never stored in
plaintext.

## 8. Changes

We will notify users of material changes to this policy via email at
least 30 days before they take effect.

## 9. Contact

privacy@inventa.ai
