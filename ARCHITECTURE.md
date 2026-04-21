# inventa.ai — Architecture

## High-level data flow

```
 User prompt
   │
   ▼
React client (client/)  ──────────────────────────────►  FastAPI backend (Backend/)
      ▲       │                                                 │
      │       │  SSE stream of build events                     │
      │       ▼                                                 ▼
      │    MultiProductCanvas.jsx                         claude_service
      │    (Three.js STLLoader)                                 │
      │       ▲                                                 ▼
      │       │  STEP/STL URLs                           parametric_cad_service
      │       │                                                 │
      └───────┴──── /exports/cad/{buildId}.{stl,step} ◄────────┘
```

1. User types a prompt in `PromptInput.jsx`.
2. `App.jsx` opens an EventSource to `POST /api/build/stream`.
3. `claude_service.generate_design_from_prompt()` streams Claude's JSON response
   (`parameters`, `code`, `explanation`).
4. `parametric_cad_service.generate_parametric_cad()` validates, preprocesses, and
   `exec()`s the code in a sandbox; exports STEP + STL.
5. Client fetches STL, renders via `STLLoader`, paints sliders from `parameters`.
6. Slider change → `POST /api/rebuild` re-runs the saved `_parametric.py` with
   new values. **No AI call** on this path.

## Ports and processes

| Service   | Port | Start command                |
|-----------|------|------------------------------|
| Backend   | 3001 | `cd Backend && python start.py` |
| Frontend  | 3000 | `cd client && npm start`        |

## Critical invariants

### 1. Triple-update rule (code-safety allowlist)

The `cadquery` allowlist lives in three places and **must stay in sync**:

1. `_validate_code_safety()` in `parametric_cad_service.py` — the `allowed_imports` set
2. `_execute_cadquery_code()` — the `namespace = {...}` dict passed to `exec()`
3. `rebuild_with_parameters()` — a second, identical namespace dict

CI enforces parity via `scripts/check_namespace_parity.py`.

### 2. Parametric script markers

Generated `_parametric.py` files use these exact strings:

```
# ═══════════════════════════════════════════════════════════════
# GEOMETRY GENERATION
...
# ═══════════════════════════════════════════════════════════════
# EXPORT
```

`rebuild_with_parameters()` parses with literal `str.find()` against these strings.
Any reformatting breaks every saved build.

### 3. UTF-8 stdout/stderr reconfigure

`Backend/start.py` and `Backend/main.py` both reconfigure stdout/stderr to UTF-8
**before any import**, so emoji logging works on Windows (cp1252) consoles.

## Self-healing pipeline

On CadQuery `RuntimeError` / `ValueError`, the build loop catches the exception,
calls `claude_service.fix_code_with_error()`, and retries. Capped at
`MAX_SELF_HEALING_ATTEMPTS = 8`. Phase escalation:

| Phase         | Attempts | Strategy                                            |
|---------------|----------|-----------------------------------------------------|
| Targeted      | 1        | Fix only the crashing line, reduce radii 30%       |
| Conservative  | 2–3      | Reduce radii 60%, wrap in try/except                |
| Aggressive    | 4–5      | Strip all fillets/chamfers/shells                   |
| Rewrite       | 6–7      | Rewrite failing section with safe primitives        |
| Nuclear       | 8        | Rebuild entire model from boxes + cylinders only    |

## Preprocessing pipeline

Before `exec()`, every AI-generated code block passes through 7 transforms in
order (see `_execute_cadquery_code()` and `rebuild_with_parameters()`):

1. `_strip_centered_from_non_box()`
2. `_ensure_box_grounding()`
3. `_fix_zero_dimensions()`
4. `_fix_negative_z_positions()`
5. `_ensure_result_assignment()`
6. `_clamp_fillet_radii()`
7. `_wrap_fillets_in_try_except()`

## Security layers

| Concern                  | Defense                                                     |
|--------------------------|-------------------------------------------------------------|
| Arbitrary code execution | Import allowlist + forbidden-call regex                     |
| Path traversal           | `_validate_build_id()` regex + extension allowlist          |
| DoS via huge payloads    | 1 MB body-size middleware (`MAX_REQUEST_BODY_BYTES`)        |
| Abuse / scraping         | `slowapi` rate limits (`RATE_LIMIT_BUILD`, `RATE_LIMIT_DEFAULT`) |
| Prompt injection         | `_sanitize_user_prompt()` strips role tokens & overrides    |
| Unauthenticated writes   | `_require_auth()` (set `REQUIRE_AUTH=true` in `.env`)       |
| Long log files           | Rotating handler on `exports/error_log.txt` (5 MB × 3)      |

## Observability

- `GET /api/healthz` — liveness (never touches deps)
- `GET /api/readyz` — readiness (Anthropic key, exports dir, DB)
- `exports/error_log.txt` — JSON-formatted, rotated
- Emoji-prefixed console logs: `📨` request, `📤` response, `❌` error,
  `🧠` AI, `🔧` fix, `💾` DB save

## Directory layout

```
Backend/
  main.py                 FastAPI routes
  config.py               Pydantic Settings
  start.py                Entry point (UTF-8 fix first)
  services/
    claude_service.py     AI code generation + self-healing
    parametric_cad_service.py   CadQuery sandbox + export
    product_library.py    140+ product templates
    product_visual_knowledge.py Per-category build guides
    database_service.py   Supabase wrapper (optional)
    s3_service.py         S3 upload (optional)
    glb_service.py        GLB conversion (optional)
    usage_meter.py        Per-user daily counter
client/
  src/
    App.jsx               Central state manager
    api.js                Authenticated fetch wrapper
    config.js             API_BASE + API_HOST (env-driven)
    components/           Co-located .css files
    hooks/                useBuild.js
    context/              AppContext, AuthContext
migrations/               .sql files applied by scripts/apply_migrations.py
scripts/
  apply_migrations.py     Idempotent migration runner
  check_namespace_parity.py   Triple-update rule enforcer
tests/
  test_suite.py           Pytest wrapper for legacy test_*.py scripts
```
