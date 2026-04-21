# inventa.ai — Runbook

## Incidents

### Backend returning 500s

1. Hit `GET /api/healthz` — if 503, service itself is dead (Render-level).
2. Hit `GET /api/readyz` — inspect `checks` object. Common failures:
   - `anthropic_key: false` → `ANTHROPIC_API_KEY` missing in Render env.
   - `exports_writable: false` → disk quota exhausted; trigger cleanup.
   - `database: "error: ..."` → Supabase down or credentials rotated.
3. Tail `exports/error_log.txt` (rotating, 5 MB × 3 backups).
4. Check Render logs for uvicorn stack traces.
5. If many `BRep_API command not done` errors: upstream CadQuery build got a
   bad prompt. Capture the prompt and add to `test_shape_quality.py`.

### CadQuery segfault / worker dies

- Symptom: Render worker restarts mid-build, client sees SSE disconnect.
- Cause: OCC kernel hit a shape it cannot handle.
- Mitigation: self-heal loop normally catches this via `RuntimeError`, but
  true SIGSEGVs kill the worker. Future: isolate geometry in a subprocess
  (see roadmap #6).
- Immediate action: capture the prompt, open GitHub issue with stack trace.

### Rate limiter rejecting legitimate users

- `slowapi` uses remote IP. Behind Render's proxy, `X-Forwarded-For` is set.
- If too tight: edit `RATE_LIMIT_BUILD` in Render env (e.g. `10/minute`).
- If spoof-prone: consider per-API-key limiting (requires auth).

### Path-traversal alert

- `/exports/cad/{filename}` rejects `..`, hidden files, bad extensions, and
  non-file paths. `test_path_traversal.py` covers 14 attack variants.
- If an attack succeeds in production: revert immediately and add the attack
  string to the test suite.

### Claude API hang / timeout

- `claude_service.__init__` sets `httpx.Timeout(connect=10s, write=30s, read=None)`.
- `read=None` is intentional for SSE streaming.
- If a single request pins a worker: check Anthropic status page; the
  retry-on-network-error loop (2s/4s backoff, max 3 attempts) should kick in.

### Disk full

- `exports/` can accumulate STL/STEP/GLB files. Safe to prune anything
  older than 7 days — the frontend re-requests via `buildId`.
- Keep `_parametric.py` scripts; those are the editable source.

## Deploy

### Local dev

```powershell
# Kill stale servers first
Get-Process -Name python -ErrorAction SilentlyContinue | Stop-Process -Force

# Backend
cd Backend
python start.py               # uvicorn on :3001, hot reload

# Frontend (new terminal)
cd client
npm start                     # CRA dev server on :3000
```

### Render production

- Backend: auto-deploy from `main` branch.
- Frontend: `npm run build` then serve `client/build/`.
- Health check path: `/api/healthz`.
- Required env vars: `ANTHROPIC_API_KEY`, optional `SUPABASE_URL`,
  `SUPABASE_ANON_KEY`, `STRIPE_SECRET_KEY`, `CORS_ORIGINS`.

### Migrations

```powershell
export DATABASE_URL="postgresql://..."
python scripts/apply_migrations.py --dry-run    # preview
python scripts/apply_migrations.py              # apply
```

Migrations are tracked in a `_migrations` table. Re-running is a no-op.

## Tests

```powershell
python -m pytest -q                                  # pytest harness
python scripts/check_namespace_parity.py             # triple-update rule
```

CI runs both on every push/PR (`.github/workflows/ci.yml`).

## On-call checklist

- [ ] Does `/api/healthz` return 200?
- [ ] Does `/api/readyz` return 200 with all checks true?
- [ ] Are the last 100 lines of `exports/error_log.txt` repetitive
      (same root cause) or varied?
- [ ] Is CPU/memory on Render >80%?
- [ ] Has `CORS_ORIGINS` drifted from the production frontend URL?
- [ ] Are Anthropic credits exhausted? (Their status page + dashboard.)

## Common fixes

| Symptom                                   | Action                                         |
|-------------------------------------------|-------------------------------------------------|
| Emoji shows as `?` in logs                | Verify `PYTHONIOENCODING=utf-8` in Render env  |
| Slider changes don't regenerate           | Check `_parametric.py` exists; inspect 404      |
| Exports return 404                        | Verify `settings.CAD_DIR.exists()` on start-up  |
| Every build fails identical error         | Regression in preprocessing — run full `pytest` |
| Rate limit triggered for tests            | Set `RATE_LIMIT_BUILD=1000/minute` in test env |
