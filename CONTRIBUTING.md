# Contributing to inventa.ai

## Quick start

```powershell
git clone <repo>
cd inventa.ai

# Backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r Backend/requirements.txt

# Frontend
cd client
npm install
cd ..

# Copy example env and fill in secrets
cp .env.example .env
```

Run both services from separate terminals:

```powershell
cd Backend && python start.py        # :3001
cd client && npm start               # :3000
```

## Pre-commit hooks

```powershell
pip install pre-commit
pre-commit install
```

Runs `ruff`, `black`, `gitleaks`, and whitespace/YAML/JSON checks on staged files.

## Tests

```powershell
python -m pytest -q                   # all 20 backend tests
python scripts/check_namespace_parity.py   # triple-update rule
```

CI (`.github/workflows/ci.yml`) runs both on every push and PR.

## Pull request checklist

- [ ] `pytest -q` passes locally
- [ ] `check_namespace_parity.py` passes
- [ ] New AI-generated code imports added to ALL THREE places:
      `_validate_code_safety`, `_execute_cadquery_code`, `rebuild_with_parameters`
- [ ] New tests for new behavior (see `test_*.py` patterns)
- [ ] No hardcoded `http://localhost` in frontend — use `API_BASE`/`API_HOST` from
      `client/src/config.js`
- [ ] Pre-commit hooks pass
- [ ] No emoji in error messages that might be logged on Windows without
      `PYTHONIOENCODING=utf-8`
- [ ] If you edited parametric script markers — **don't**. They're load-bearing.

## Coding conventions

### Python

- Black-formatted, 100-char lines.
- Type hints on public function signatures.
- Don't add error handling for scenarios that can't happen.
- Services are module-level singletons (`claude_service`, `parametric_cad_service`).
- Geometry operations are synchronous — no `await` on CadQuery calls.

### JavaScript / React

- Prettier-formatted.
- Components co-located with their `.css` file in `client/src/components/`.
- No Redux — `App.jsx` is the central state manager.
- API calls go through `client/src/api.js` `authFetch`, not raw `fetch`.

## Adding features

### New import for AI-generated code

Triple-update:

1. `_validate_code_safety()` `allowed_imports` set in `parametric_cad_service.py`
2. `_execute_cadquery_code()` namespace dict in the same file
3. `rebuild_with_parameters()` namespace dict in the same file

Run `python scripts/check_namespace_parity.py` before committing.

### New product template

Add to `PRODUCTS` list in `Backend/services/product_library.py`. Required keys:
`keywords`, `name`, `category`, `dimensions`, `features`.

### New error-recovery strategy

Add a keyword match + category + targeted_fix to
`claude_service.fix_code_with_error()`. Add a representative error string to
`test_fix_code_error_classification.py`.

### New API endpoint

Add the route in `Backend/main.py`. If the frontend consumes it, add an API
function in `client/src/api.js` and call from `App.jsx` (don't `fetch()`
directly — we need the auth header).

## Security reporting

Email security@inventa.ai — do not open public issues for vulnerabilities.
