"""
Chat-to-CAD Platform - Phase 4
FastAPI Backend with Async Task Queue
"""

import sys as _sys
import os as _os

# Fix Windows console encoding for emoji characters (must run before any print)
_os.environ['PYTHONIOENCODING'] = 'utf-8'
try:
    _sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    _sys.stderr.reconfigure(encoding='utf-8', errors='replace')
except Exception as _enc_err:
    print(f'Warning: UTF-8 encoding setup failed: {_enc_err}')

from fastapi import FastAPI, HTTPException, Request, UploadFile, File, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse, JSONResponse
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
import os
from pathlib import Path
import uuid
import time
import json
import asyncio
import hashlib
import datetime
import traceback
import re

# Import services
from services import (
    claude_service, 
    parametric_cad_service, 
    database_service,
    DB_IMPORT_OK,
    s3_service, 
    S3_AVAILABLE,
    glb_service,
    GLB_AVAILABLE,
    cad_import_service,
    CAD_SUPPORTED_FORMATS,
)
from config import settings

# Ensure exports directories exist (needed on fresh Render deploys)
settings.EXPORTS_DIR.mkdir(parents=True, exist_ok=True)
settings.CAD_DIR.mkdir(parents=True, exist_ok=True)
(settings.EXPORTS_DIR / "uploads").mkdir(parents=True, exist_ok=True)

print("\n" + "="*60)
print("🚀 BACKEND STARTING UP")
print("="*60)
print(f"Services loaded successfully:")
print(f"  - Claude Service: {claude_service is not None}")
print(f"  - Parametric CAD Service: {parametric_cad_service is not None}")
print(f"  - S3 Available: {S3_AVAILABLE}")
print(f"  - GLB Available: {GLB_AVAILABLE}")

# Initialize Supabase database
DB_AVAILABLE = False
try:
    if not DB_IMPORT_OK:
        print(f"  - Supabase Database: ⚠️  'supabase' package not installed — storage disabled")
    elif settings.SUPABASE_URL and (settings.SUPABASE_SERVICE_ROLE_KEY or settings.SUPABASE_ANON_KEY):
        # Prefer service role key so backend can read/write rows regardless of RLS
        # (user ownership is enforced in application code via explicit user_id filters).
        db_key = settings.SUPABASE_SERVICE_ROLE_KEY or settings.SUPABASE_ANON_KEY
        using_service_role = bool(settings.SUPABASE_SERVICE_ROLE_KEY)
        database_service.initialize(
            supabase_url=settings.SUPABASE_URL,
            supabase_key=db_key,
        )
        DB_AVAILABLE = True
        key_label = "service_role" if using_service_role else "anon (⚠️ RLS will hide rows)"
        print(f"  - Supabase Database: ✅ Connected to {settings.SUPABASE_URL} [{key_label}]")
        if not using_service_role:
            print(f"    ⚠️  Add SUPABASE_SERVICE_ROLE_KEY to .env so projects/builds persist")
    else:
        print(f"  - Supabase Database: ⚠️  Missing SUPABASE_URL or SUPABASE_ANON_KEY in .env — storage disabled")
except Exception as db_err:
    print(f"  - Supabase Database: ❌ Connection failed: {db_err}")
    print(f"    Check your Supabase credentials in .env")

print("="*60 + "\n")

# Import Celery tasks (optional - only if Celery is installed)
# Celery (optional — only if tasks module + Redis configured)
try:
    from tasks import generate_cad_async
    CELERY_AVAILABLE = True
except ImportError:
    CELERY_AVAILABLE = False

# ── In-memory scene store ─────────────────────────────────────
_scenes: Dict[str, dict] = {}    # sceneId -> { sceneId, name, products: [...] }
_products: Dict[str, dict] = {}  # instanceId -> product dict

# ── Prompt cache ─────────────────────────────────────────────
_prompt_cache: Dict[str, dict] = {}  # hash -> cached build result

# ── Version history store (F36) ──────────────────────────────
_version_history: Dict[str, list] = {}  # buildId -> [{ versionId, timestamp, label, design, code, parameters }]

# ── Material metadata store ──────────────────────────────────
_material_metadata: Dict[str, dict] = {}  # buildId -> material info

# ── Collaboration rooms (F35) ───────────────────────────────
_collab_rooms: Dict[str, dict] = {}  # roomId -> { host, members: [...], scene, createdAt }
_collab_connections: Dict[str, list] = {}  # roomId -> [WebSocket, ...]

MAX_SELF_HEALING_ATTEMPTS = 8  # hard cap on infinite self-healing loop
BUILD_WALLCLOCK_BUDGET_SECONDS = 300  # total wall-clock cap for one /api/build/stream request

# ── Rotating error logger ─────────────────────────────────────
# Replaces ad-hoc `exports/error_log.txt` writes. Rotates at 5 MB,
# keeps 3 backups so the log never grows unbounded on Render.
import logging
from logging.handlers import RotatingFileHandler

_error_log_path = settings.EXPORTS_DIR / "error_log.txt"
_error_logger = logging.getLogger("inventa.errors")
_error_logger.setLevel(logging.ERROR)
if not _error_logger.handlers:
    try:
        _handler = RotatingFileHandler(
            _error_log_path, maxBytes=5 * 1024 * 1024, backupCount=3, encoding="utf-8"
        )
        _handler.setFormatter(logging.Formatter("%(asctime)s %(message)s"))
        _error_logger.addHandler(_handler)
    except Exception as _log_err:
        print(f"⚠️  Rotating log setup failed: {_log_err}")

def _log_error(context: str, err: Exception, **extra) -> None:
    """Centralized error logger — writes to rotating file + console."""
    try:
        payload = {"context": context, "error": str(err), **extra}
        _error_logger.error(json.dumps(payload, default=str))
    except Exception:
        pass
    # Forward to Sentry if configured — safe no-op otherwise
    try:
        from services.sentry_bridge import capture_exception
        capture_exception(err, context=context, **extra)
    except Exception:
        pass

# ── Per-build concurrency locks for /api/rebuild ─────────────
# Two slider changes on the same build_id must serialize to avoid races
# on the parametric script file and exported STL/STEP.
_rebuild_locks: Dict[str, asyncio.Lock] = {}

def _get_rebuild_lock(build_id: str) -> asyncio.Lock:
    lock = _rebuild_locks.get(build_id)
    if lock is None:
        lock = asyncio.Lock()
        _rebuild_locks[build_id] = lock
    return lock

# ── Build cancellation tracking ──────────────────────────────
_cancelled_builds: set = set()  # buildIds that user requested to cancel

def _prompt_hash(prompt: str, user_id: str = None) -> str:
    """Generate a deterministic hash for a prompt, scoped by user."""
    key = prompt.strip().lower() + (user_id or "anonymous")
    return hashlib.sha256(key.encode()).hexdigest()[:16]

_BUILD_ID_RE = re.compile(r'^[a-zA-Z0-9_-]+$')

def _validate_build_id(bid: str) -> str:
    """Validate a build ID contains only safe characters (prevents path traversal)."""
    if not bid or not _BUILD_ID_RE.match(bid):
        raise HTTPException(status_code=400, detail=f"Invalid buildId format: {bid!r}")
    return bid

def _check_prompt_cache(prompt: str, user_id: str = None) -> dict | None:
    """Return cached result if the same prompt was built before by this user."""
    h = _prompt_hash(prompt, user_id)
    cached = _prompt_cache.get(h)
    if not cached:
        return None
    # Verify files still exist (cache stores "stlUrl", not "stlFile")
    stl_path = cached.get("stlUrl", "") or cached.get("stlFile", "")
    if stl_path:
        full_path = (CAD_DIR / Path(stl_path).name).resolve()
        if not full_path.exists():
            del _prompt_cache[h]
            return None
    return cached

def _store_prompt_cache(prompt: str, result: dict, user_id: str = None):
    """Cache a successful build result keyed by prompt hash + user."""
    h = _prompt_hash(prompt, user_id)
    _prompt_cache[h] = result
    # Limit cache to 100 entries
    if len(_prompt_cache) > 100:
        oldest = next(iter(_prompt_cache))
        del _prompt_cache[oldest]

# Initialize FastAPI app
app = FastAPI(
    title="inventa.AI Platform",
    description=f"Natural Language to CAD Generation with {settings.AI_MODEL_NAME} & CadQuery",
    version="3.0.0"
)

# CORS configuration for React frontend
# Explicit origins from settings.CORS_ORIGINS (comma-separated). Plus a regex
# fallback that matches any *.onrender.com host so a production deploy does NOT
# silently break if CORS_ORIGINS is forgotten in the dashboard.
_cors_origins = [o.strip() for o in settings.CORS_ORIGINS.split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_origin_regex=r"https://([a-z0-9-]+\.)*onrender\.com",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Body size limit middleware ────────────────────────────────────────
# Reject requests larger than MAX_REQUEST_BODY_BYTES (1 MB) with 413.
# Checks Content-Length header. File-upload routes are exempt.
MAX_REQUEST_BODY_BYTES = 1 * 1024 * 1024  # 1 MB

@app.middleware("http")
async def limit_request_body(request: Request, call_next):
    if request.url.path.startswith(("/api/upload", "/api/s3/upload", "/api/convert/glb")):
        return await call_next(request)
    content_length = request.headers.get("content-length")
    if content_length:
        try:
            if int(content_length) > MAX_REQUEST_BODY_BYTES:
                return JSONResponse(
                    status_code=413,
                    content={"detail": f"Request body too large (max {MAX_REQUEST_BODY_BYTES} bytes)"},
                )
        except ValueError:
            return JSONResponse(status_code=400, content={"detail": "Invalid Content-Length"})
    return await call_next(request)

# ── Request-ID middleware ─────────────────────────────────────────────
# Attaches a short correlation ID to every request. Exposed on the response
# via `X-Request-ID` and available as `request.state.request_id` for logs.
@app.middleware("http")
async def request_id_middleware(request: Request, call_next):
    incoming = request.headers.get("x-request-id", "").strip()
    # Only trust short, safe incoming IDs; otherwise mint our own.
    if incoming and len(incoming) <= 64 and all(c.isalnum() or c in "-_" for c in incoming):
        rid = incoming
    else:
        rid = uuid.uuid4().hex[:12]
    request.state.request_id = rid
    _req_start = time.time()
    try:
        response = await call_next(request)
    except Exception:
        # Record failure metric and re-raise for FastAPI's handler chain
        try:
            from services.metrics import metrics as _metrics
            _metrics.incr(
                "inventa_http_requests_total",
                {"method": request.method, "path": request.url.path, "status": "500"},
            )
        except Exception:
            pass
        raise
    response.headers["X-Request-ID"] = rid
    # Record request metrics
    try:
        from services.metrics import metrics as _metrics
        _metrics.incr(
            "inventa_http_requests_total",
            {
                "method": request.method,
                "path": request.url.path,
                "status": str(response.status_code),
            },
        )
        _metrics.observe(
            "inventa_http_request_duration_seconds",
            time.time() - _req_start,
            {"method": request.method, "path": request.url.path},
        )
    except Exception:
        pass
    return response

# ── Rate limiting (slowapi) ────────────────────────────────────────────
try:
    from slowapi import Limiter, _rate_limit_exceeded_handler
    from slowapi.util import get_remote_address
    from slowapi.errors import RateLimitExceeded
    limiter = Limiter(key_func=get_remote_address)
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
    RATE_LIMIT_AVAILABLE = True
    print("  - Rate Limiting: ✅ slowapi active")
except ImportError:
    RATE_LIMIT_AVAILABLE = False
    # Create a no-op decorator so routes still work without slowapi
    class _NoOpLimiter:
        def limit(self, *a, **kw):
            def decorator(func):
                return func
            return decorator
    limiter = _NoOpLimiter()
    print("  - Rate Limiting: ⚠️  slowapi not installed — no rate limits")

# ── Exports cleanup background task ────────────────────────────────────
# Deletes CAD artifacts older than EXPORTS_RETENTION_DAYS. Keeps
# `_parametric.py` scripts (they're tiny and editable source of truth).
EXPORTS_RETENTION_DAYS = 7
EXPORTS_CLEANUP_INTERVAL_SECONDS = 6 * 60 * 60  # every 6 hours
_EXPORTS_CLEANUP_EXTS = {".stl", ".step", ".stp", ".glb", ".svg", ".csv"}

async def _exports_cleanup_loop():
    while True:
        try:
            cutoff = time.time() - EXPORTS_RETENTION_DAYS * 86400
            removed = 0
            if CAD_DIR.exists():
                for p in CAD_DIR.iterdir():
                    if not p.is_file():
                        continue
                    if p.suffix.lower() not in _EXPORTS_CLEANUP_EXTS:
                        continue
                    try:
                        if p.stat().st_mtime < cutoff:
                            p.unlink()
                            removed += 1
                    except OSError:
                        pass
            if removed:
                print(f"🧹 exports cleanup: removed {removed} file(s) older than {EXPORTS_RETENTION_DAYS}d")
        except Exception as e:
            print(f"⚠️  exports cleanup error: {e}")
        await asyncio.sleep(EXPORTS_CLEANUP_INTERVAL_SECONDS)

@app.on_event("startup")
async def _start_background_tasks():
    asyncio.create_task(_exports_cleanup_loop())
    print(f"  - Exports cleanup: ✅ every {EXPORTS_CLEANUP_INTERVAL_SECONDS // 3600}h, retention {EXPORTS_RETENTION_DAYS}d")

# ── Auth middleware — extract Supabase JWT user info ────────────────────
# Parses the Authorization header if present and attaches user info
# to request.state.user. When REQUIRE_AUTH=true in .env, write endpoints
# will reject unauthenticated requests with 401.
import base64

try:
    import jwt as _pyjwt
    _PYJWT_AVAILABLE = True
except ImportError:
    _PYJWT_AVAILABLE = False
    print("  ⚠️  PyJWT not installed — JWT signatures will NOT be verified")

def _decode_jwt_payload(token: str) -> dict | None:
    """Decode and verify a Supabase JWT. Falls back to unverified decode if no secret configured."""
    # Prefer verified decode when JWT secret is available
    if _PYJWT_AVAILABLE and settings.SUPABASE_JWT_SECRET:
        try:
            payload = _pyjwt.decode(
                token,
                settings.SUPABASE_JWT_SECRET,
                algorithms=["HS256"],
                audience="authenticated",
            )
            return payload
        except _pyjwt.ExpiredSignatureError:
            return None
        except _pyjwt.InvalidTokenError:
            return None
    # Fallback: unverified decode (development only)
    try:
        parts = token.split('.')
        if len(parts) != 3:
            return None
        payload = parts[1]
        # Add padding
        payload += '=' * (4 - len(payload) % 4)
        decoded = base64.urlsafe_b64decode(payload)
        return json.loads(decoded)
    except Exception:
        return None

@app.middleware("http")
async def auth_middleware(request: Request, call_next):
    """Extract user from Supabase JWT if Authorization header is present."""
    request.state.user = None
    auth_header = request.headers.get("authorization", "")
    if auth_header.startswith("Bearer "):
        token = auth_header[7:]
        payload = _decode_jwt_payload(token)
        if payload:
            request.state.user = {
                "id": payload.get("sub"),
                "email": payload.get("email"),
                "role": payload.get("role"),
            }
    response = await call_next(request)
    return response

def _require_auth(request: Request):
    """FastAPI dependency: reject unauthenticated requests when REQUIRE_AUTH=true."""
    if settings.REQUIRE_AUTH and not getattr(request.state, "user", None):
        raise HTTPException(status_code=401, detail="Authentication required")

# Request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    print(f"\n{'='*60}")
    print(f"📨 INCOMING REQUEST")
    print(f"{'='*60}")
    print(f"Method: {request.method}")
    print(f"URL: {request.url}")
    print(f"Client: {request.client}")
    print(f"{'='*60}\n")
    
    response = await call_next(request)
    
    process_time = time.time() - start_time
    print(f"\n{'='*60}")
    print(f"📤 RESPONSE")
    print(f"{'='*60}")
    print(f"Status: {response.status_code}")
    print(f"Process Time: {process_time:.3f}s")
    print(f"{'='*60}\n")
    
    return response

# Create exports directory structure
EXPORTS_DIR = settings.EXPORTS_DIR
CAD_DIR = settings.CAD_DIR

# Request/Response Models
class ChatRequest(BaseModel):
    message: str
    conversationHistory: Optional[list] = []
    currentDesign: Optional[Dict[str, Any]] = None

class BuildRequest(BaseModel):
    prompt: str = Field(..., min_length=1, max_length=10000)
    previousDesign: Optional[Dict[str, Any]] = None
    projectId: Optional[str] = None
    model: Optional[str] = None
    mode: Optional[str] = "agent"  # 'agent' | 'ask' | 'plan'
    image: Optional[Dict[str, str]] = None  # { base64, mediaType }

class AskRequest(BaseModel):
    prompt: str = Field(..., min_length=1, max_length=10000)
    currentDesign: Optional[Dict[str, Any]] = None
    model: Optional[str] = None

class PlanRequest(BaseModel):
    prompt: str
    currentDesign: Optional[Dict[str, Any]] = None
    model: Optional[str] = None

class ChatResponse(BaseModel):
    message: str
    updatedDesign: Optional[Dict[str, Any]] = None
    shouldBuild: bool = False
    buildResult: Optional[Dict[str, Any]] = None

class BuildResponse(BaseModel):
    buildId: str
    stlUrl: str
    stepUrl: str
    parametricScript: Optional[str] = None
    parameters: Optional[list] = None
    explanation: Optional[Dict[str, Any]] = None
    success: bool = True

class RebuildRequest(BaseModel):
    buildId: str
    parameters: Dict[str, float]

class AsyncBuildRequest(BaseModel):
    prompt: str
    useAsync: bool = False

# Health check endpoint
@app.get("/")
async def root():
    """Health check endpoint"""
    print("✅ Health check endpoint called")
    return {
        "status": "healthy",
        "service": "inventa.AI",
        "phase": "4",
        "engines": {
            "geometry": "CadQuery",
            "llm": settings.AI_MODEL_NAME,
            "framework": "FastAPI",
            "async_tasks": "Celery" if CELERY_AVAILABLE else "Synchronous"
        }
    }

@app.get("/api/health")
async def api_health():
    """API health check"""
    print("✅ API health check called")
    return {"status": "ok", "message": "Backend is running"}

@app.get("/api/healthz")
async def healthz():
    """Liveness probe — process is running. Never touches external deps."""
    return {"status": "ok"}

@app.get("/api/readyz")
async def readyz():
    """Readiness probe — checks that critical dependencies are reachable.
    Returns 200 if the service can accept traffic, 503 otherwise.
    """
    checks = {}
    ok = True

    # Claude (Anthropic) key presence — cheap check, not a network call
    checks["anthropic_key"] = bool(getattr(settings, "ANTHROPIC_API_KEY", ""))
    if not checks["anthropic_key"]:
        ok = False

    # Exports directory writable
    try:
        exports_dir = Path("exports/cad")
        exports_dir.mkdir(parents=True, exist_ok=True)
        checks["exports_writable"] = os.access(exports_dir, os.W_OK)
        if not checks["exports_writable"]:
            ok = False
    except Exception as e:
        checks["exports_writable"] = False
        checks["exports_error"] = str(e)
        ok = False

    # Database (optional — only flagged if configured but failing)
    try:
        from services import database_service
        if database_service is not None and getattr(database_service, "engine", None):
            checks["database"] = "configured"
        else:
            checks["database"] = "not_configured"
    except Exception as e:
        checks["database"] = f"error: {e}"
        # DB is optional — do not flip ok to False

    status_code = 200 if ok else 503
    return JSONResponse(status_code=status_code, content={"status": "ready" if ok else "not_ready", "checks": checks})

# ── Prometheus-style metrics endpoint ──────────────────────────────────
@app.get("/metrics")
async def metrics_endpoint():
    """Prometheus scrape target. Returns counters + histograms in text format."""
    from fastapi.responses import PlainTextResponse
    from services.metrics import metrics as _metrics
    return PlainTextResponse(_metrics.snapshot_prometheus(), media_type="text/plain; version=0.0.4")

# ── Build feedback (thumbs up/down) ────────────────────────────────────
@app.post("/api/feedback")
async def submit_feedback(body: dict, request: Request):
    """Record 👍/👎/neutral feedback on a build. Body: { buildId, rating: -1|0|1, note? }"""
    build_id = (body.get("buildId") or "").strip()
    rating = body.get("rating")
    if not build_id or rating not in (-1, 0, 1):
        raise HTTPException(status_code=400, detail="buildId and rating (-1|0|1) required")
    note = (body.get("note") or "")[:2000]
    user_id = None
    if hasattr(request.state, "user") and request.state.user:
        user_id = request.state.user.get("id")
    try:
        from services.metrics import metrics as _metrics
        _metrics.incr("inventa_build_feedback_total", {"rating": str(rating)})
    except Exception:
        pass
    if DB_AVAILABLE:
        try:
            database_service.save_feedback(
                build_id=build_id, user_id=user_id, rating=rating, note=note
            )
        except Exception as e:
            print(f"⚠️ save_feedback failed: {e}")
    return {"success": True}

# ── Share links (public read-only viewer) ──────────────────────────────
@app.post("/api/share")
async def create_share_link(body: dict, request: Request):
    """Create a public read-only share token for a build."""
    _require_auth(request)
    build_id = (body.get("buildId") or "").strip()
    if not build_id or not re.match(r"^[A-Za-z0-9_-]{1,64}$", build_id):
        raise HTTPException(status_code=400, detail="Invalid buildId")
    token = uuid.uuid4().hex
    user_id = request.state.user.get("id") if getattr(request.state, "user", None) else None
    if DB_AVAILABLE:
        try:
            database_service.create_share_link(
                token=token, build_id=build_id, owner_id=user_id
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"share create failed: {e}")
    frontend = getattr(settings, "FRONTEND_URL", "http://localhost:3000").rstrip("/")
    return {"success": True, "token": token, "url": f"{frontend}/view/{token}"}

@app.get("/api/share/{token}")
async def resolve_share_link(token: str):
    """Resolve a share token → build data for public viewer."""
    if not re.match(r"^[a-f0-9]{16,64}$", token):
        raise HTTPException(status_code=400, detail="Invalid token")
    if not DB_AVAILABLE:
        raise HTTPException(status_code=501, detail="Database not configured")
    try:
        data = database_service.resolve_share_link(token)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    if not data:
        raise HTTPException(status_code=404, detail="Share link not found or expired")
    return {"success": True, **data}

# ── GDPR: data export + account deletion ───────────────────────────────
@app.get("/api/me/export")
async def export_my_data(request: Request):
    """Export all data associated with the authenticated user."""
    _require_auth(request)
    user_id = request.state.user.get("id") if getattr(request.state, "user", None) else None
    if not user_id:
        raise HTTPException(status_code=401, detail="Authentication required")
    if not DB_AVAILABLE:
        return {"success": True, "projects": [], "builds": [], "note": "DB not configured"}
    try:
        data = database_service.export_user_data(user_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    return {"success": True, **data}

@app.delete("/api/me")
async def delete_my_account(request: Request):
    """Delete all data associated with the authenticated user."""
    _require_auth(request)
    user_id = request.state.user.get("id") if getattr(request.state, "user", None) else None
    if not user_id:
        raise HTTPException(status_code=401, detail="Authentication required")
    if not DB_AVAILABLE:
        raise HTTPException(status_code=501, detail="Database not configured")
    try:
        result = database_service.delete_user_data(user_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    return {"success": True, **result}

# ── Token usage summary ────────────────────────────────────────────────
@app.get("/api/me/usage")
async def my_usage(request: Request):
    """Return the authenticated user's token usage, grouped by period."""
    _require_auth(request)
    user_id = request.state.user.get("id") if getattr(request.state, "user", None) else None
    if not user_id:
        raise HTTPException(status_code=401, detail="Authentication required")
    if not DB_AVAILABLE:
        return {
            "success": True,
            "today": {"input_tokens": 0, "output_tokens": 0, "builds": 0, "cost_usd": 0.0},
            "month": {"input_tokens": 0, "output_tokens": 0, "builds": 0, "cost_usd": 0.0},
            "note": "DB not configured",
        }
    try:
        summary = database_service.summarize_user_tokens(user_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    return {"success": True, **summary}

# ── Available AI Models ───────────────────────────────────────────────
# This app is locked to a single model: Claude Opus 4.7. The list is kept
# as a list-of-one so the client UI / API contract stays unchanged.
AVAILABLE_MODELS = [
    {
        "id": "claude-opus-4-7",
        "name": "Claude Opus 4.7",
        "provider": "Anthropic",
        "description": "Flagship — used for all CAD generation in this app",
        "tier": "flagship",
    },
]

@app.get("/api/models")
async def list_models():
    """Return available AI models. Always Claude Opus 4.7 for this app."""
    available = AVAILABLE_MODELS if settings.ANTHROPIC_API_KEY else []
    return {
        "models": available,
        "default": settings.AI_MODEL_NAME,
    }


# ── Intent classification (idiot-proof front door) ─────────────────────
class IntentRequest(BaseModel):
    prompt: str = Field(..., min_length=0, max_length=10000)
    hasPreviousDesign: bool = False


@app.post("/api/intent")
@limiter.limit(settings.RATE_LIMIT_DEFAULT)
async def classify_user_intent(request: Request, body: IntentRequest = None):
    """Classify what the user is trying to do BEFORE running a build.

    Returns: {intent, reason, suggestions, reply}
    Intents: build | modify | question | chitchat | vague | empty | gibberish

    The frontend should:
      • build/modify  → run the build pipeline
      • question      → call /api/ask instead
      • chitchat/vague/empty/gibberish → render `reply` + `suggestions` chips,
        do NOT spend tokens on a build.
    """
    _require_auth(request)
    if body is None:
        raw = await request.json()
        body = IntentRequest(**raw)
    return JSONResponse(
        claude_service.classify_intent(body.prompt, body.hasPreviousDesign)
    )


# ── Ask endpoint (text-only Q&A, no CAD build) ─────────────────────────
@app.post("/api/ask")
@limiter.limit(settings.RATE_LIMIT_DEFAULT)
async def ask_about_design(request: Request, body: AskRequest = None):
    """
    Text-only Q&A — answers questions about CAD, design, materials,
    manufacturing, etc. No code generation, no build.
    Returns a streaming SSE response with the AI's text answer.
    """
    _require_auth(request)
    if body is None:
        raw = await request.json()
        body = AskRequest(**raw)

    async def event_generator():
        def sse(data: dict) -> str:
            return f"data: {json.dumps(data)}\n\n"

        try:
            # Native model — body.model is ignored on purpose.
            active_model = settings.AI_MODEL_NAME

            # Build context about current design if available
            design_context = ""
            if body.currentDesign and body.currentDesign.get("code"):
                design_context = f"""
The user currently has this CadQuery design loaded:
```python
{body.currentDesign['code'][:3000]}
```
Parameters: {json.dumps(body.currentDesign.get('parameters', [])[:10])}
"""

            system_prompt = """You are a knowledgeable CAD engineering assistant for inventa.AI.
Answer questions about:
- CAD design principles, best practices, and techniques
- CadQuery Python API usage and syntax
- Manufacturing processes (3D printing, CNC, injection molding)
- Materials selection and properties
- Mechanical engineering concepts
- The user's current design (if context provided)

Be concise, practical, and specific. Use examples when helpful.
If the user asks about their current design, reference the code/parameters directly.
Do NOT generate CadQuery code unless the user explicitly asks for a code example.
Format your response in clean markdown with headers and bullet points where appropriate."""

            user_message = body.prompt
            if design_context:
                user_message = f"{design_context}\n\nUser question: {body.prompt}"

            yield sse({"status": "thinking", "message": "Thinking..."})

            answer = await asyncio.to_thread(
                claude_service._stream_completion,
                model=active_model,
                max_tokens=4096,
                temperature=0.4,
                system=system_prompt,
                messages=[{"role": "user", "content": user_message}]
            )

            yield sse({
                "status": "complete",
                "message": answer,
                "type": "ask"
            })

        except Exception as e:
            yield sse({"status": "error", "message": str(e)})

    return StreamingResponse(event_generator(), media_type="text/event-stream")


# ── Plan endpoint (structured multi-step build plan) ────────────────────
@app.post("/api/plan")
@limiter.limit(settings.RATE_LIMIT_DEFAULT)
async def plan_design(request: Request, body: PlanRequest = None):
    """
    Returns a structured multi-step build plan for a complex design.
    Each step is a discrete build action the user can execute sequentially.
    """
    _require_auth(request)
    if body is None:
        raw = await request.json()
        body = PlanRequest(**raw)

    async def event_generator():
        def sse(data: dict) -> str:
            return f"data: {json.dumps(data)}\n\n"

        try:
            # Native model — body.model is ignored on purpose.
            active_model = settings.AI_MODEL_NAME

            design_context = ""
            if body.currentDesign and body.currentDesign.get("code"):
                design_context = f"""
The user currently has this design loaded (CadQuery code):
```python
{body.currentDesign['code'][:2000]}
```
"""

            system_prompt = """You are a CAD project planner for inventa.AI. The user describes a complex product and you break it down into a step-by-step build plan.

Return ONLY this JSON (no markdown fences):
{
  "title": "Build Plan: <product name>",
  "overview": "Brief summary of the overall design approach",
  "estimated_complexity": "low|medium|high",
  "steps": [
    {
      "step": 1,
      "title": "Short step title",
      "prompt": "The exact prompt the user should send to the Agent to build this step",
      "description": "What this step creates and why",
      "depends_on": null
    },
    {
      "step": 2,
      "title": "Short step title",
      "prompt": "Exact prompt — reference step 1 output as 'modify the existing design to add...'",
      "description": "What this step adds",
      "depends_on": 1
    }
  ],
  "tips": ["Practical tip 1", "Practical tip 2"]
}

RULES:
- Break the design into 3-8 logical steps
- Each step's "prompt" must be a complete, self-contained instruction that the Agent mode can execute
- Step 1 is always the base shape/body
- Later steps modify/add to the existing design
- Each step should be achievable in a single build
- Include realistic dimensions in prompts
- Tips should cover manufacturing, material selection, or design best practices"""

            user_message = body.prompt
            if design_context:
                user_message = f"{design_context}\n\nPlan this design: {body.prompt}"

            yield sse({"status": "thinking", "message": "Creating build plan..."})

            answer = await asyncio.to_thread(
                claude_service._stream_completion,
                model=active_model,
                max_tokens=8192,
                temperature=0.3,
                system=system_prompt,
                messages=[{"role": "user", "content": user_message}]
            )

            # Try to parse as JSON for structured response
            plan_json = None
            try:
                plan_json = json.loads(answer)
            except json.JSONDecodeError:
                # Try to extract JSON from the response
                json_match = re.search(r'\{[\s\S]*\}', answer)
                if json_match:
                    try:
                        plan_json = json.loads(json_match.group())
                    except json.JSONDecodeError:
                        pass

            if plan_json:
                yield sse({
                    "status": "complete",
                    "message": plan_json.get("overview", "Plan ready"),
                    "plan": plan_json,
                    "type": "plan"
                })
            else:
                yield sse({
                    "status": "complete",
                    "message": answer,
                    "type": "plan"
                })

        except Exception as e:
            yield sse({"status": "error", "message": str(e)})

    return StreamingResponse(event_generator(), media_type="text/event-stream")


# Chat endpoint (conversational mode)
@app.post("/api/chat", response_model=ChatResponse)
@limiter.limit(settings.RATE_LIMIT_BUILD)
async def chat_with_engineer(request: Request, body: ChatRequest = None):
    """
    Conversational interface for refining CAD designs
    Claude guides the user through design parameters
    """
    _require_auth(request)
    if body is None:
        raw = await request.json()
        body = ChatRequest(**raw)
    try:
        result = await claude_service.chat_about_design(
            message=body.message,
            conversation_history=body.conversationHistory,
            current_design=body.currentDesign
        )
        
        # If design is ready, trigger build via parametric_cad_service (full pipeline)
        build_result = None
        if result.get("shouldBuild") and result.get("updatedDesign"):
            cad_result = await parametric_cad_service.generate_parametric_cad(result["updatedDesign"])
            build_result = {
                "buildId": cad_result["buildId"],
                "stlUrl": cad_result["stlFile"],
                "stepUrl": cad_result["stepFile"],
                "parametricScript": cad_result.get("parametricScript")
            }
        
        return ChatResponse(
            message=result["message"],
            updatedDesign=result.get("updatedDesign"),
            shouldBuild=result.get("shouldBuild", False),
            buildResult=build_result
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Build endpoint (single-shot mode)
@app.post("/api/build", response_model=BuildResponse)
@limiter.limit(settings.RATE_LIMIT_BUILD)
async def build_product(request: Request, body: BuildRequest = None):
    """
    Single-shot CAD generation from natural language prompt
    Phase 2: Claude -> Parametric Code Schema -> CadQuery Execution -> STEP/STL
    """
    _require_auth(request)
    if body is None:
        raw = await request.json()
        body = BuildRequest(**raw)
    print(f"\n{'='*60}")
    print(f"🔨 BUILD REQUEST RECEIVED")
    print(f"{'='*60}")
    print(f"Prompt: {body.prompt}")
    print(f"Has previous design: {body.previousDesign is not None}")
    print(f"{'='*60}\n")
    
    last_error = None
    ai_response = None
    
    try:
        # Step 1: Claude generates parametric code schema (phased for new designs)
        print("📡 Step 1: Calling Claude AI for design generation...")
        
        # Fetch project history from DB for AI context
        project_history = None
        if body.projectId and DB_AVAILABLE:
            try:
                project_history = database_service.get_project_history_for_ai(body.projectId)
                if project_history:
                    print(f"📚 Loaded project history: {project_history['build_count']} builds")
            except Exception as hist_err:
                print(f"⚠️ Failed to load project history: {hist_err}")
        
        ai_response = await claude_service.generate_design_auto(
            prompt=body.prompt,
            previous_design=body.previousDesign,
            image=body.image,
            project_history=project_history
        )
        print(f"✅ Claude AI response received")
        print(f"Response keys: {list(ai_response.keys())}")
        
        # Step 1.5: Completeness check + enhancement (same as streaming endpoint)
        code = ai_response.get("code", "")
        if code:
            analysis = claude_service.analyze_code_completeness(code, body.prompt)
            print(f"📊 Completeness: features={analysis['total_features']}, complete={'✅' if analysis['is_complete'] else '❌'}")
            if not analysis["is_complete"] and len(analysis["missing_features"]) >= 3:
                print(f"🔁 Enhancement pass — missing: {', '.join(analysis['missing_features'][:4])}")
                ai_response = await claude_service.enhance_incomplete_design(ai_response, body.prompt, analysis)
                enhanced_code = ai_response.get("code", "")
                if enhanced_code:
                    analysis = claude_service.analyze_code_completeness(enhanced_code, body.prompt)
                    print(f"📊 Post-enhancement: features={analysis['total_features']}, complete={'✅' if analysis['is_complete'] else '⚠️'}")
        
        # Step 2: Execute parametric CadQuery code (self-healing with retry cap)
        attempt = 0
        while attempt < MAX_SELF_HEALING_ATTEMPTS:
            attempt += 1
            try:
                print(f"\n🔧 Step 2 (attempt {attempt}): Generating CAD model with CadQuery...")
                
                # Pre-execution code review — catch common mistakes before CadQuery runs
                code_to_review = ai_response.get("code", "")
                if code_to_review:
                    review = claude_service.review_code_before_execution(code_to_review)
                    if review["has_issues"]:
                        issue_summary = "; ".join(f"L{i['line']}: {i['problem']}" for i in review["issues"][:5])
                        print(f"🔍 Pre-exec review found {len(review['issues'])} issue(s): {issue_summary}")
                        ai_response["code"] = review["fixed_code"]
                
                cad_result = await parametric_cad_service.generate_parametric_cad(ai_response)
                print(f"✅ CAD generation complete (after {attempt} attempt{'s' if attempt > 1 else ''})")
                print(f"Build ID: {cad_result['buildId']}")
                print(f"Files generated: STL={cad_result.get('stlFile')}, STEP={cad_result.get('stepFile')}")
                
                return BuildResponse(
                    buildId=cad_result["buildId"],
                    stlUrl=cad_result["stlFile"],
                    stepUrl=cad_result["stepFile"],
                    parametricScript=cad_result.get("parametricScript"),
                    parameters=cad_result.get("parameters"),
                    explanation=cad_result.get("explanation"),
                    success=True
                )
            except (RuntimeError, ValueError) as cad_err:
                last_error = str(cad_err)
                print(f"\n⚠️ CadQuery attempt {attempt} failed: {last_error}")
                
                if attempt >= MAX_SELF_HEALING_ATTEMPTS:
                    raise HTTPException(status_code=500, detail=f"Build failed after {attempt} self-healing attempts: {last_error}")
                
                print(f"🔄 Self-healing (attempt {attempt}/{MAX_SELF_HEALING_ATTEMPTS})...")
                failed_code = ai_response.get("code", "")
                ai_response = await claude_service.fix_code_with_error(
                    failed_code=failed_code,
                    error_message=last_error,
                    original_prompt=body.prompt,
                    attempt=attempt,
                    max_retries=MAX_SELF_HEALING_ATTEMPTS
                )
                print(f"✅ Claude fix response received")
        
    except Exception as e:
        error_details = traceback.format_exc()
        print(f"\n{'='*60}")
        print(f"❌ ERROR in /api/build")
        print(f"{'='*60}")
        print(error_details)
        print(f"{'='*60}\n")
        
        # Log to file for debugging
        try:
            log_path = Path(EXPORTS_DIR) / "error_log.txt"
            with open(log_path, "a", encoding="utf-8") as f:
                f.write(f"\n{'='*60}\n")
                f.write(f"[{datetime.datetime.now()}] /api/build error\n")
                f.write(f"Prompt: {body.prompt}\n")
                f.write(f"Error: {str(e)}\n")
                f.write(error_details)
                f.write(f"{'='*60}\n")
        except Exception as log_err:
            print(f"⚠️ Failed to write error log: {log_err}")
        
        raise HTTPException(status_code=500, detail=str(e))

# ── Streaming build endpoint (SSE) ──────────────────────────────────────

@app.post("/api/build/stream")
@limiter.limit(settings.RATE_LIMIT_BUILD)
async def build_product_stream(request: Request, body: BuildRequest = None):
    """
    SSE streaming build endpoint — sends step-by-step progress events.
    Each event is a JSON line: { step, message, status, ... }
    Final event includes the full build result or error.
    """
    _require_auth(request)
    # Parse body from request if FastAPI didn't inject it (due to Request being first)
    if body is None:
        raw = await request.json()
        body = BuildRequest(**raw)

    # ── Free-tier guardrail (usage metering) ─────────────────────────
    _user_obj = getattr(request.state, "user", None) if hasattr(request, "state") else None
    _user_id = _user_obj.get("id") if _user_obj else None
    try:
        from services.usage_meter import usage_meter
        _plan = (_user_obj or {}).get("plan", "free") if _user_obj else "free"
        if _plan == "free":
            allowed, used, limit = usage_meter.check_free_tier(_user_id)
            if not allowed:
                raise HTTPException(
                    status_code=429,
                    detail=f"Free-tier daily limit reached ({used}/{limit} builds). Upgrade to Pro for unlimited builds."
                )
        usage_meter.increment(_user_id)
    except HTTPException:
        raise
    except Exception as _meter_err:
        print(f"⚠️  usage_meter skipped: {_meter_err}")
    async def event_generator():
        def sse(data: dict) -> str:
            return f"data: {json.dumps(data)}\n\n"

        # Assign a build_id early so the frontend can cancel this build
        stream_build_id = str(uuid.uuid4())[:8]

        # ── Token tracking: mark this build as the active scope so
        # claude_service streaming wrappers can attribute usage to it ──
        from services import token_tracker
        _tt_token = token_tracker.start(stream_build_id)

        # ── Wall-clock deadline + client-disconnect guard ─────────────
        # Prevents the self-heal loop from pinning a worker forever.
        _build_deadline = time.time() + BUILD_WALLCLOCK_BUDGET_SECONDS

        async def _client_gone() -> bool:
            try:
                return await request.is_disconnected()
            except Exception:
                return False

        def is_cancelled():
            if stream_build_id in _cancelled_builds:
                return True
            if time.time() > _build_deadline:
                print(f"⏰ Build {stream_build_id} exceeded {BUILD_WALLCLOCK_BUDGET_SECONDS}s budget — aborting")
                return True
            return False

        last_error = None
        ai_response = None
        attempt = 0
        is_modification = body.previousDesign is not None and bool(body.previousDesign)
        has_previous_code = is_modification and bool(body.previousDesign.get("code", ""))

        # ── DB fallback: if projectId exists but no previousDesign, restore from DB ──
        if not is_modification and body.projectId and DB_AVAILABLE:
            try:
                proj_hist = database_service.get_project_history_for_ai(body.projectId)
                if proj_hist and proj_hist.get("latest_code"):
                    body.previousDesign = {
                        "code": proj_hist["latest_code"],
                        "parameters": proj_hist.get("latest_parameters", []),
                        "explanation": proj_hist.get("latest_explanation", {}),
                    }
                    is_modification = True
                    has_previous_code = True
                    print(f"📚 Restored previousDesign from DB project ({proj_hist['build_count']} builds)")
            except Exception as db_err:
                print(f"⚠️ DB fallback failed: {db_err}")

        print(f"\n{'='*60}")
        print(f"🔨 STREAM BUILD REQUEST")
        print(f"{'='*60}")
        print(f"Prompt: {body.prompt[:100]}..." if len(body.prompt) > 100 else f"Prompt: {body.prompt}")
        print(f"Is modification: {is_modification}")
        print(f"Has previous code: {has_previous_code}")
        if has_previous_code:
            code_preview = body.previousDesign['code'][:150].replace('\n', ' ')
            print(f"Previous code preview: {code_preview}...")
        print(f"{'='*60}\n")

        try:
            # ── Cache-hit shortcut (new designs only) ────────────────────
            if not is_modification and not body.previousDesign:
                _cache_user_id = request.state.user.get("id") if getattr(request.state, "user", None) else None
                cached = _check_prompt_cache(body.prompt, _cache_user_id)
                if cached:
                    print(f"⚡ Prompt cache HIT — skipping AI")

                    # Still create a new project and save build to DB
                    cached_project_id = body.projectId
                    if DB_AVAILABLE:
                        try:
                            if not cached_project_id:
                                project_name = body.prompt[:50].strip()
                                if len(body.prompt) > 50:
                                    project_name += "..."
                                user_id = None
                                if hasattr(request.state, 'user') and request.state.user:
                                    user_id = request.state.user.get("id")
                                proj = database_service.create_project(name=project_name, user_id=user_id)
                                cached_project_id = proj["id"]
                            database_service.save_build(
                                project_id=cached_project_id,
                                build_id=cached.get("buildId", str(uuid.uuid4())[:8]),
                                prompt=body.prompt,
                                code=cached.get("design", {}).get("code"),
                                parameters=cached.get("design", {}).get("parameters"),
                                explanation=cached.get("design", {}).get("explanation"),
                                stl_path=cached.get("stlUrl"),
                                step_path=cached.get("stepUrl"),
                                script_path=cached.get("parametricScript"),
                                is_modification=False,
                            )
                            print(f"💾 Cached build saved to Supabase (project={cached_project_id})")
                        except Exception as db_cache_err:
                            print(f"⚠️ Failed to save cached build to DB: {db_cache_err}")

                    # Return cached result with the new project ID
                    cached_result = {**cached, "projectId": cached_project_id}

                    yield sse({"step": 1, "message": "Cache hit — reusing previous build", "status": "done"})
                    yield sse({"step": 2, "message": "Skipped (cached)", "status": "done"})
                    yield sse({"step": 3, "message": "Skipped (cached)", "status": "done"})
                    yield sse({"step": 4, "message": "Skipped (cached)", "status": "done"})
                    yield sse({"step": 5, "message": "Skipped (cached)", "status": "done"})
                    yield sse({"step": 6, "message": "Build complete! (cached)", "status": "complete", "result": cached_result})
                    return

            # Step 1: Searching product library
            yield sse({"step": 0, "message": "Build started", "status": "started", "streamBuildId": stream_build_id})
            yield sse({"step": 1, "message": "Searching product library for real-world dimensions and reference specs...", "status": "active", "detail": "Checking our database of 98+ product templates for matching measurements."})
            await asyncio.sleep(0.05)  # allow flush

            # Detect complexity for adaptive behavior
            complexity = claude_service._detect_complexity(body.prompt)
            complexity_labels = {"high": "Professional", "medium": "Detailed", "standard": "Standard"}
            complexity_label = complexity_labels.get(complexity, "Standard")

            # ── Cancellation / disconnect check ──
            if is_cancelled() or await _client_gone():
                yield sse({"step": -1, "message": "Build cancelled by user", "status": "cancelled"})
                _cancelled_builds.discard(stream_build_id)
                return

            # Step 2: Analyzing prompt with AI
            yield sse({"step": 1, "message": f"Product library checked — {complexity_label} complexity detected", "status": "done"})
            if is_modification:
                step2_msg = "Modifying your design — reading previous code and applying your changes..."
                step2_detail = "Claude is editing the existing CadQuery code to add/change only what you asked for."
            else:
                # Pre-decide single-shot vs phased so the UI message is honest.
                _use_phased, _route_reason = claude_service._should_use_phased(body.prompt, body.previousDesign)
                if _use_phased:
                    step2_msg = "Phase 1/3: Building foundation shape..."
                    step2_detail = "Claude is creating the main body shape, dimensions, and overall form."
                else:
                    step2_msg = "Designing your product..."
                    step2_detail = "Claude is generating the full CadQuery model in a single pass."
            yield sse({"step": 2, "message": step2_msg, "status": "active", "detail": step2_detail})

            # ── Fetch project history from DB for AI context ──
            project_history = None
            if body.projectId and DB_AVAILABLE:
                try:
                    project_history = database_service.get_project_history_for_ai(body.projectId)
                    if project_history:
                        print(f"📚 Loaded project history: {project_history['build_count']} builds for '{project_history['project_name']}'")
                except Exception as hist_err:
                    print(f"⚠️ Failed to load project history: {hist_err}")

            # Track phase progress for SSE updates
            phase_messages = []
            def on_phase(phase_num, phase_name, status):
                phase_messages.append((phase_num, phase_name, status))
            
            ai_response = await claude_service.generate_design_auto(
                prompt=body.prompt,
                previous_design=body.previousDesign,
                model_override=None,  # native model only
                image=body.image,
                on_phase=on_phase,
                project_history=project_history
            )

            # Send phase completion SSE events. Detect which path ran by
            # looking for the multi-phase 'Foundation' tick — single-shot
            # emits a 'Single-shot' tick instead.
            ran_phased = any(
                pn == "Foundation" for (_, pn, _s) in phase_messages
            )
            if not is_modification and ran_phased:
                yield sse({"step": 2, "message": "Phase 1/3: Foundation shape complete", "status": "done"})
                yield sse({"step": 2.1, "message": "Phase 2/3: Adding functional features...", "status": "active", "detail": "Adding cutouts, ports, openings, and structural elements."})
                yield sse({"step": 2.1, "message": "Phase 2/3: Features added", "status": "done"})
                yield sse({"step": 2.2, "message": "Phase 3/3: Adding details & finishing...", "status": "active", "detail": "Adding fillets, surface details, patterns, feet, and polish."})
                yield sse({"step": 2.2, "message": "Phase 3/3: Details complete", "status": "done"})
            else:
                yield sse({"step": 2, "message": "AI design complete", "status": "done"})

            # ── Cancellation check ──
            if is_cancelled():
                yield sse({"step": -1, "message": "Build cancelled by user", "status": "cancelled"})
                _cancelled_builds.discard(stream_build_id)
                return

            # ── Modification quality check: warn if Claude rewrote instead of editing ──
            if is_modification and body.previousDesign and body.previousDesign.get("code"):
                prev_code = body.previousDesign["code"]
                new_code = ai_response.get("code", "")
                prev_lines = prev_code.strip().splitlines()
                new_lines = new_code.strip().splitlines()
                # Check if the first 5 lines match (structural preservation)
                match_count = 0
                for i in range(min(5, len(prev_lines), len(new_lines))):
                    if prev_lines[i].strip() == new_lines[i].strip():
                        match_count += 1
                if match_count < 3:
                    print(f"⚠️ MODIFICATION WARNING: Only {match_count}/5 first lines match — Claude may have rewritten the code!")
                    print(f"   Previous code: {len(prev_lines)} lines → New code: {len(new_lines)} lines")
                else:
                    print(f"✅ Modification preserved structure: {match_count}/5 first lines match, {len(prev_lines)}→{len(new_lines)} lines")

            # Step 3: Completeness check + design review (now runs for BOTH new designs AND modifications)
            code = ai_response.get("code", "")
            param_count = len(ai_response.get("parameters", []))
            code_lines = code.count("\n") + 1
            explanation = ai_response.get("explanation", {})
            design_intent = explanation.get("design_intent", "")
            
            # Run completeness check for both new designs AND modifications (quality must be consistent)
            if code:
                yield sse({"step": 3, "message": "Checking design completeness...", "status": "active", "detail": "Analyzing generated code for missing features, cutouts, and detail level."})
                analysis = claude_service.analyze_code_completeness(code, body.prompt)
                
                print(f"\n📊 Completeness Analysis:")
                print(f"   Product type: {analysis['product_type']}")
                print(f"   Features: {analysis['total_features']} (cut={analysis['cut_count']}, union={analysis['union_count']})")
                print(f"   Treatments: fillet={analysis['fillet_count']}, round_cutters={analysis.get('round_cutter_count', 0)}")
                print(f"   Advanced: spline={analysis.get('spline_count', 0)}, loft={analysis.get('loft_count', 0)}, revolve={analysis.get('revolve_count', 0)}, sweep={analysis.get('sweep_count', 0)}")
                print(f"   Body: {'box-based' if analysis.get('main_body_is_box', True) else 'advanced shape'}")
                print(f"   Code lines: {analysis['code_lines']}")
                print(f"   Complete: {'✅' if analysis['is_complete'] else '❌'}")
                
                if not analysis["is_complete"] and len(analysis["missing_features"]) >= 3:
                    missing_summary = ", ".join(analysis["missing_features"][:4])
                    yield sse({"step": 3, "message": f"Found {len(analysis['missing_features'])} missing features — enhancing design...", "status": "active", "detail": f"Missing: {missing_summary}. Sending back to AI for targeted enhancement."})
                    
                    for mf in analysis["missing_features"]:
                        print(f"     • {mf}")
                    
                    # CREDIT OPTIMIZATION: Max 1 enhancement pass after phased build.
                    # 3 phases already produce good results — 1 pass for stragglers.
                    
                    # SINGLE enhancement pass
                    ai_response = await claude_service.enhance_incomplete_design(ai_response, body.prompt, analysis)
                    
                    enhanced_code = ai_response.get("code", "")
                    if enhanced_code:
                        code_lines = enhanced_code.count("\n") + 1
                        param_count = len(ai_response.get("parameters", []))
                        print(f"\n📊 Post-enhancement: lines={code_lines}, params={param_count}")
                    
                    yield sse({"step": 3, "message": f"Design enhanced — {param_count} params, {code_lines} lines", "status": "done"})
                else:
                    step3_detail = f"Created {param_count} adjustable parameters across {code_lines} lines of CadQuery code."
                    if design_intent:
                        step3_detail += f" {design_intent}"
                    yield sse({"step": 3, "message": f"Design complete — {analysis['total_features']} features, {param_count} params", "status": "done", "detail": step3_detail})
            else:
                step3_detail = f"Created {param_count} adjustable parameters across {code_lines} lines of CadQuery code."
                if design_intent:
                    step3_detail += f" {design_intent}"
                yield sse({"step": 3, "message": f"Design validated — {param_count} parameters, {code_lines} lines", "status": "done", "detail": step3_detail})

            # Step 4: Executing CadQuery (self-healing, max {MAX_SELF_HEALING_ATTEMPTS} attempts)
            attempt = 0
            # Track whether arrangement fix was already attempted (avoid infinite re-fix loop)
            _arrangement_fix_done = False
            
            while attempt < MAX_SELF_HEALING_ATTEMPTS:
                attempt += 1

                # ── Cancellation / disconnect / timeout check inside healing loop ──
                if is_cancelled() or await _client_gone():
                    yield sse({"step": -1, "message": "Build cancelled or timed out", "status": "cancelled"})
                    _cancelled_builds.discard(stream_build_id)
                    return

                # Determine the healing phase name
                if attempt == 1:
                    phase_name = None  # first try, no healing yet
                elif attempt == 2:
                    phase_name = "Targeted fix"
                elif attempt <= 4:
                    phase_name = "Conservative fix"
                elif attempt <= 6:
                    phase_name = "Aggressive simplification"
                elif attempt <= 8:
                    phase_name = "Section rewrite"
                else:
                    phase_name = "Full rebuild"

                if attempt == 1:
                    yield sse({"step": 4, "message": "Building 3D geometry with CadQuery engine...", "status": "active", "detail": "Executing the Python code to construct solid 3D geometry with boolean operations, fillets, and cutouts."})
                else:
                    yield sse({"step": 4, "message": f"🔧 Self-healing ({phase_name}) — attempt {attempt-1}...", "status": "active", "detail": f"AI is applying {phase_name.lower()} strategy to fix the geometry error.", "healing": {"attempt": attempt - 1, "phase": phase_name}})

                try:
                    # Pre-execution code review — catch common mistakes before CadQuery runs
                    review = {"has_issues": False}  # default if no code to review
                    code_to_review = ai_response.get("code", "")
                    if code_to_review:
                        review = claude_service.review_code_before_execution(code_to_review)
                        if review["has_issues"]:
                            issue_summary = "; ".join(f"L{i['line']}: {i['problem']}" for i in review["issues"][:5])
                            print(f"🔍 Pre-exec review found {len(review['issues'])} issue(s): {issue_summary}")
                            ai_response["code"] = review["fixed_code"]

                    # AI-powered line-by-line review (first attempt only — too expensive for healing loops)
                    # CREDIT OPTIMIZATION: Skip AI review for simple builds (< 60 lines, regex review clean)
                    _code_lines = ai_response.get("code", "").count("\n") + 1
                    _needs_ai_review = attempt == 1 and ai_response.get("code") and (
                        _code_lines >= 60  # Complex enough to benefit
                        or review.get("has_issues", False)  # Regex review found problems
                    )
                    if _needs_ai_review:
                        yield sse({"step": 3.5, "message": "AI reviewing code line by line...", "status": "active", "detail": "Reading every line to verify geometry, spatial arrangement, connectivity, and proportions."})
                        ai_review = await asyncio.to_thread(
                            claude_service.ai_review_cadquery_code,
                            code=ai_response["code"],
                            original_prompt=body.prompt,
                            parameters=ai_response.get("parameters", [])
                        )
                        if ai_review["has_fixes"]:
                            # SAFETY NET: Reject reviews that drop significant features.
                            # The reviewer sometimes "simplifies" models into empty shells.
                            _orig_code = ai_response["code"]
                            _new_code = ai_review["fixed_code"]
                            def _feat_signature(src: str) -> tuple:
                                import re as _re
                                return (
                                    len(src),
                                    len(_re.findall(r"\.union\(", src)),
                                    len(_re.findall(r"\.cut\(", src)),
                                    len(_re.findall(r"\.extrude\(|\.revolve\(|\.loft\(|\.sweep\(", src)),
                                    len(_re.findall(r"\.fillet\(|\.chamfer\(", src)),
                                )
                            _o = _feat_signature(_orig_code)
                            _n = _feat_signature(_new_code)
                            # Reject if reviewed code is <60% the size OR drops >40% of boolean/feature ops
                            _size_shrunk = _n[0] < _o[0] * 0.60
                            _feats_orig = sum(_o[1:])
                            _feats_new = sum(_n[1:])
                            _feats_dropped = _feats_orig > 0 and _feats_new < _feats_orig * 0.60
                            if _size_shrunk or _feats_dropped:
                                print(f"⚠️ AI review REJECTED — would shrink code "
                                      f"({_o[0]}→{_n[0]} chars, feats {_feats_orig}→{_feats_new}). Keeping original.")
                                yield sse({"step": 3.5, "message": "AI review suggested regressions — keeping original code", "status": "done"})
                            else:
                                ai_response["code"] = _new_code
                                fix_count = len(ai_review["issues_found"])
                                yield sse({"step": 3.5, "message": f"AI review fixed {fix_count} issue{'s' if fix_count != 1 else ''}: {ai_review['review_summary']}", "status": "done", "detail": "; ".join(ai_review["issues_found"][:5])})
                        else:
                            yield sse({"step": 3.5, "message": "AI review passed — code verified", "status": "done"})

                    cad_result = await parametric_cad_service.generate_parametric_cad(ai_response)

                    if attempt == 1:
                        yield sse({"step": 4, "message": "3D model built successfully", "status": "done"})
                    else:
                        yield sse({"step": 4, "message": f"✅ 3D model built after {attempt - 1} self-healing fix{'es' if attempt > 2 else ''}", "status": "done", "healing": {"attempt": attempt - 1, "phase": phase_name, "resolved": True}})

                    # Emit quality warnings if any
                    quality_info = cad_result.get("quality", {})
                    quality_warnings = quality_info.get("warnings", [])
                    quality_metrics = quality_info.get("metrics", {})
                    if quality_warnings:
                        warnings_text = " | ".join(quality_warnings)
                        yield sse({"step": 4.5, "message": f"Quality notes: {warnings_text}", "status": "info", "detail": json.dumps(quality_metrics)})
                    
                    # ── Quality-driven arrangement re-healing ──
                    # If disconnected solids or critical assembly errors detected, send back to Claude
                    disconnected = quality_metrics.get("disconnected_solids", 0)
                    assembly_error = any("ASSEMBLY ERROR" in w for w in quality_warnings)
                    
                    if (assembly_error or disconnected > 0) and attempt <= MAX_SELF_HEALING_ATTEMPTS - 2 and not _arrangement_fix_done:
                        _arrangement_fix_done = True  # Only attempt arrangement fix once
                        yield sse({"step": 4.5, "message": f"🔧 Fixing assembly — {disconnected} floating part(s) detected", "status": "active", "detail": "AI is repositioning disconnected components to create a properly connected assembly."})
                        print(f"🔧 ARRANGEMENT FIX: {disconnected} disconnected solids — sending back to Claude")
                        
                        arrangement_error_msg = (
                            f"ASSEMBLY ARRANGEMENT ERROR: The model has {disconnected} disconnected/floating solid(s). "
                            f"Parts are NOT physically touching or overlapping the main body. "
                            f"Quality warnings: {'; '.join(quality_warnings)}. "
                            f"Bounding box: X={quality_metrics.get('bbox_x', '?')}mm, Y={quality_metrics.get('bbox_y', '?')}mm, Z={quality_metrics.get('bbox_z', '?')}mm. "
                            f"FIX INSTRUCTIONS: 1) Check EVERY .translate() call — parts must overlap by at least 0.5mm. "
                            f"2) Compute positions FROM parent part dimensions (arm_top_z = arm_z + arm_height, etc). "
                            f"3) Do NOT add gaps between parts (+5, +10 offsets). "
                            f"4) Ensure every .union() pair physically overlaps in 3D space. "
                            f"5) Double-check Z positions: first .box() uses centered=(True,True,False) so Z starts at 0."
                        )
                        
                        try:
                            fixed_response = await claude_service.fix_code_with_error(
                                failed_code=ai_response.get("code", ""),
                                error_message=arrangement_error_msg,
                                original_prompt=body.prompt,
                                attempt=attempt,
                                max_retries=MAX_SELF_HEALING_ATTEMPTS
                            )
                            ai_response["code"] = fixed_response.get("code", ai_response.get("code", ""))
                            ai_response["parameters"] = fixed_response.get("parameters", ai_response.get("parameters", []))
                            continue  # Re-execute with fixed code
                        except Exception as fix_err:
                            print(f"⚠️ Arrangement fix failed: {fix_err}")
                            # Continue to export with current result

                    # Step 5: Exporting files
                    yield sse({"step": 5, "message": "Exporting STL and STEP files...", "status": "active", "detail": "Generating STL (for 3D printing) and STEP (for CAD editing) from the solid model."})
                    await asyncio.sleep(0.05)
                    yield sse({"step": 5, "message": "Files exported — ready to download", "status": "done"})

                    # Final result — include full design for modification flow
                    # Save to database if available
                    saved_project_id = body.projectId
                    if DB_AVAILABLE:
                        try:
                            # Auto-create project if none specified
                            if not saved_project_id:
                                # Use first ~50 chars of prompt as project name
                                project_name = body.prompt[:50].strip()
                                if len(body.prompt) > 50:
                                    project_name += "..."
                                user_id = None
                                if hasattr(request.state, 'user') and request.state.user:
                                    user_id = request.state.user.get("id")
                                proj = database_service.create_project(name=project_name, user_id=user_id)
                                saved_project_id = proj["id"]

                            database_service.save_build(
                                project_id=saved_project_id,
                                build_id=cad_result["buildId"],
                                prompt=body.prompt,
                                code=ai_response.get("code"),
                                parameters=ai_response.get("parameters"),
                                explanation=ai_response.get("explanation"),
                                stl_path=cad_result.get("stlFile"),
                                step_path=cad_result.get("stepFile"),
                                script_path=cad_result.get("parametricScript"),
                                is_modification=is_modification,
                            )
                            print(f"💾 Build saved to Supabase (project={saved_project_id})")
                        except Exception as db_save_err:
                            print(f"⚠️ Failed to save build to DB: {db_save_err}")

                    # ── Analytics (best-effort) ──
                    try:
                        from services.metrics import metrics as _metrics
                        _metrics.incr("inventa_builds_total", {"success": "true"})
                        _metrics.observe(
                            "inventa_build_duration_seconds",
                            max(0.0, time.time() - (_build_deadline - BUILD_WALLCLOCK_BUDGET_SECONDS)),
                        )
                        _metrics.observe("inventa_build_self_heal_attempts", float(attempt - 1 if attempt > 1 else 0))
                    except Exception:
                        pass
                    if DB_AVAILABLE:
                        try:
                            _tok_totals = token_tracker.peek(stream_build_id)
                            database_service.save_analytics(
                                build_id=cad_result.get("buildId"),
                                project_id=saved_project_id,
                                user_id=_user_id,
                                prompt=body.prompt[:2000],
                                model=settings.AI_MODEL_NAME,
                                complexity=complexity,
                                duration_ms=int((time.time() - (_build_deadline - BUILD_WALLCLOCK_BUDGET_SECONDS)) * 1000),
                                self_heal_attempts=attempt - 1 if attempt > 1 else 0,
                                cache_hit=False,
                                success=True,
                                input_tokens=_tok_totals.get("input_tokens", 0),
                                output_tokens=_tok_totals.get("output_tokens", 0),
                                request_id=getattr(request.state, "request_id", None),
                            )
                        except Exception:
                            pass

                    _tok = token_tracker.flush(stream_build_id)
                    yield sse({
                        "step": 6,
                        "message": "Build complete!",
                        "status": "complete",
                        "result": {
                            "buildId": cad_result["buildId"],
                            "stlUrl": cad_result["stlFile"],
                            "stepUrl": cad_result["stepFile"],
                            "parametricScript": cad_result.get("parametricScript"),
                            "parameters": cad_result.get("parameters"),
                            "explanation": cad_result.get("explanation"),
                            "design": {
                                "parameters": ai_response.get("parameters", []),
                                "code": ai_response.get("code", ""),
                                "explanation": ai_response.get("explanation", {}),
                            },
                            "projectId": saved_project_id,
                            "healingAttempts": attempt - 1 if attempt > 1 else 0,
                            "healingWarning": (
                                "Some design features were simplified during auto-repair to ensure a valid 3D model. "
                                "Try regenerating for a more detailed result."
                            ) if attempt >= 4 else None,
                            "tokens": {
                                "input": _tok.get("input_tokens", 0),
                                "output": _tok.get("output_tokens", 0),
                                "cacheRead": _tok.get("cache_read_input_tokens", 0),
                                "cacheWrite": _tok.get("cache_creation_input_tokens", 0),
                                "calls": _tok.get("calls", 0),
                                "costUsd": _tok.get("cost_usd", 0.0),
                            },
                            "success": True
                        }
                    })

                    # Store in prompt cache (new designs only)
                    if not is_modification:
                        _store_user_id = request.state.user.get("id") if getattr(request.state, "user", None) else None
                        _store_prompt_cache(body.prompt, {
                            "buildId": cad_result["buildId"],
                            "stlUrl": cad_result["stlFile"],
                            "stepUrl": cad_result["stepFile"],
                            "parametricScript": cad_result.get("parametricScript"),
                            "parameters": cad_result.get("parameters"),
                            "explanation": cad_result.get("explanation"),
                            "design": {
                                "parameters": ai_response.get("parameters", []),
                                "code": ai_response.get("code", ""),
                                "explanation": ai_response.get("explanation", {})
                            },
                            "projectId": saved_project_id,
                            "healingAttempts": attempt - 1 if attempt > 1 else 0,
                            "success": True
                        }, user_id=_store_user_id)

                    return  # done

                except (RuntimeError, ValueError) as cad_err:
                    last_error = str(cad_err)
                    short_error = last_error[:150] + "..." if len(last_error) > 150 else last_error
                    # Use step 4 for errors too — keeps the list clean
                    yield sse({"step": 4, "message": f"⚠️ Error: {short_error}", "status": "error", "detail": last_error[:500], "healing": {"attempt": attempt, "errorType": type(cad_err).__name__}})

                    if attempt >= MAX_SELF_HEALING_ATTEMPTS:
                        yield sse({"step": -1, "message": f"Build failed after {attempt} self-healing attempts: {short_error}", "status": "fatal"})
                        return

                    # Self-healing retry
                    failed_code = ai_response.get("code", "")
                    ai_response = await claude_service.fix_code_with_error(
                        failed_code=failed_code,
                        error_message=last_error,
                        original_prompt=body.prompt,
                        attempt=attempt,
                        max_retries=MAX_SELF_HEALING_ATTEMPTS
                    )

        except Exception as e:
            error_details = traceback.format_exc()
            print(f"\n{'='*60}\n❌ ERROR in /api/build/stream\n{'='*60}")
            print(error_details)

            try:
                log_path = Path(EXPORTS_DIR) / "error_log.txt"
                with open(log_path, "a", encoding="utf-8") as f:
                    f.write(f"\n{'='*60}\n[{datetime.datetime.now()}] /api/build/stream error\n")
                    f.write(f"Prompt: {body.prompt}\nError: {str(e)}\n{error_details}\n{'='*60}\n")
            except Exception as log_err:
                print(f"⚠️ Failed to write error log: {log_err}")

            # Persist failure analytics with whatever tokens we've already consumed
            if DB_AVAILABLE:
                try:
                    _tok_fail = token_tracker.peek(stream_build_id)
                    database_service.save_analytics(
                        build_id=stream_build_id,
                        user_id=_user_id,
                        prompt=body.prompt[:2000],
                        model=settings.AI_MODEL_NAME,
                        complexity=complexity if "complexity" in locals() else None,
                        duration_ms=int((time.time() - (_build_deadline - BUILD_WALLCLOCK_BUDGET_SECONDS)) * 1000),
                        self_heal_attempts=attempt - 1 if "attempt" in locals() and attempt > 1 else 0,
                        cache_hit=False,
                        success=False,
                        error_message=str(e)[:500],
                        input_tokens=_tok_fail.get("input_tokens", 0),
                        output_tokens=_tok_fail.get("output_tokens", 0),
                        request_id=getattr(request.state, "request_id", None),
                    )
                except Exception:
                    pass

            yield sse({"step": -1, "message": str(e), "status": "fatal"})
        finally:
            # Always release the token-tracker ContextVar and clear partial ledger
            try:
                token_tracker.flush(stream_build_id)
                token_tracker.restore(_tt_token)
            except Exception:
                pass

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
    )

@app.post("/api/build/cancel")
async def cancel_build(request: Request):
    """Cancel an in-progress build by its stream build ID."""
    _require_auth(request)
    body = await request.json()
    stream_build_id = body.get("streamBuildId")
    if not stream_build_id:
        raise HTTPException(status_code=400, detail="streamBuildId is required")
    _cancelled_builds.add(stream_build_id)
    print(f"🛑 Build cancel requested: {stream_build_id}")
    return {"success": True, "message": "Cancel signal sent"}

@app.post("/api/rebuild")
async def rebuild_with_parameters(request: Request, body: RebuildRequest):
    """
    Phase 4: Re-execute existing parametric script with new parameter values
    NO AI CALL - just re-runs Python code with updated parameters
    """
    _require_auth(request)
    _validate_build_id(body.buildId)
    try:
        async with _get_rebuild_lock(body.buildId):
            result = await parametric_cad_service.rebuild_with_parameters(
                build_id=body.buildId,
                updated_parameters=body.parameters
            )
        
        return {
            "success": True,
            "buildId": result["buildId"],
            "stlUrl": result["stlFile"],
            "stepUrl": result["stepFile"],
            "message": "Model regenerated with updated parameters"
        }
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/build/async")
async def build_product_async(request: AsyncBuildRequest):
    """
    Phase 4: Async CAD generation for CPU-intensive operations
    Returns task_id for status polling
    """
    if not CELERY_AVAILABLE:
        raise HTTPException(
            status_code=501,
            detail="Celery not configured. Install redis and celery to use async mode."
        )
    
    try:
        build_id = str(uuid.uuid4())
        
        # Submit task to Celery worker
        task = generate_cad_async.delay(request.prompt, build_id)
        
        return {
            "success": True,
            "taskId": task.id,
            "buildId": build_id,
            "status": "queued",
            "message": "CAD generation task queued. Poll /api/task/{taskId} for status."
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/task/{task_id}")
async def get_task_status(task_id: str):
    """
    Phase 4: Get async task status and result
    """
    if not CELERY_AVAILABLE:
        raise HTTPException(status_code=501, detail="Celery not configured")
    
    from celery.result import AsyncResult
    
    task = AsyncResult(task_id, app=generate_cad_async.app)
    
    if task.state == 'PENDING':
        response = {
            "state": task.state,
            "status": "Task is waiting in queue...",
            "progress": 0
        }
    elif task.state == 'PROCESSING':
        response = {
            "state": task.state,
            "status": task.info.get('status', ''),
            "progress": task.info.get('progress', 0)
        }
    elif task.state == 'SUCCESS':
        response = {
            "state": task.state,
            "status": "Completed",
            "progress": 100,
            "result": task.info
        }
    elif task.state == 'FAILURE':
        response = {
            "state": task.state,
            "status": str(task.info),
            "progress": 0,
            "error": str(task.info)
        }
    else:
        response = {
            "state": task.state,
            "status": str(task.info)
        }
    
    return response

@app.post("/api/s3/upload")
async def upload_to_s3(request: Request, body: Dict[str, str]):
    """
    Phase 4: Upload build to S3 for sharing and caching
    """
    _require_auth(request)
    if not S3_AVAILABLE:
        raise HTTPException(
            status_code=501,
            detail="S3 not configured. Set AWS credentials in .env"
        )
    
    try:
        build_id = body.get("buildId")
        if not build_id:
            raise HTTPException(status_code=400, detail="buildId required")
        _validate_build_id(build_id)
        
        result = await s3_service.upload_build(build_id, settings.CAD_DIR)
        
        return {
            "success": True,
            "buildId": build_id,
            "shareUrl": result["shareUrl"],
            "s3Key": result["s3Key"],
            "expiresAt": result["expiresAt"],
            "files": result["uploadedFiles"]
        }
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Build files not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/s3/download/{s3_key:path}")
async def download_from_s3(s3_key: str):
    """
    Phase 4: Download shared build from S3
    """
    if not S3_AVAILABLE:
        raise HTTPException(status_code=501, detail="S3 not configured")
    
    try:
        result = await s3_service.download_build(s3_key, settings.CAD_DIR)
        
        return {
            "success": True,
            "buildId": result["buildId"],
            "stlUrl": result.get("stlFile"),
            "stepUrl": result.get("stepFile"),
            "scriptUrl": result.get("scriptFile")
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/s3/check/{build_id}")
async def check_s3_cache(build_id: str):
    """
    Phase 4: Check if build exists in S3 cache
    """
    if not S3_AVAILABLE:
        return {"cached": False, "message": "S3 not configured"}
    
    try:
        exists = await s3_service.check_build_exists(build_id)
        metadata = None
        
        if exists:
            metadata = await s3_service.get_build_metadata(build_id)
        
        return {
            "cached": exists,
            "buildId": build_id,
            "metadata": metadata
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/convert/glb")
async def convert_to_glb(request: Request, body: Dict[str, Any]):
    """
    Phase 4: Convert STL/STEP to GLB format for optimized web rendering
    """
    _require_auth(request)
    if not GLB_AVAILABLE:
        raise HTTPException(
            status_code=501,
            detail="GLB conversion not available. Install trimesh: pip install trimesh"
        )
    
    try:
        build_id = body.get("buildId")
        source_format = body.get("sourceFormat", "stl")  # "stl" or "step"
        optimize = body.get("optimize", True)
        
        if not build_id:
            raise HTTPException(status_code=400, detail="buildId required")
        _validate_build_id(build_id)
        
        if source_format == "stl":
            glb_url = await glb_service.convert_stl_to_glb(build_id, optimize=optimize)
        elif source_format == "step":
            quality = body.get("quality", "medium")
            glb_url = await glb_service.convert_step_to_glb(build_id, quality=quality)
        else:
            raise HTTPException(status_code=400, detail="sourceFormat must be 'stl' or 'step'")
        
        # Get mesh stats
        stats = await glb_service.get_mesh_stats(build_id, "glb")
        
        return {
            "success": True,
            "buildId": build_id,
            "glbUrl": glb_url,
            "stats": stats
        }
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/mesh/stats/{build_id}")
async def get_mesh_stats(request: Request, build_id: str, file_type: str = "stl"):
    """
    Phase 4: Get mesh statistics (vertices, faces, volume, etc.)
    """
    _require_auth(request)
    _validate_build_id(build_id)
    if not GLB_AVAILABLE:
        raise HTTPException(status_code=501, detail="Mesh analysis not available")
    
    try:
        stats = await glb_service.get_mesh_stats(build_id, file_type)
        return {
            "success": True,
            "buildId": build_id,
            "fileType": file_type,
            "stats": stats
        }
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ── Scene management endpoints (DB-backed with in-memory fallback) ──────
@app.post("/api/scene/create")
async def create_scene(request: Request, body: dict = None):
    """Create a new scene for managing multiple products"""
    _require_auth(request)
    if body is None:
        try:
            body = await request.json()
        except Exception:
            body = {}
    name = (body or {}).get("name", "Default Scene")
    project_id = (body or {}).get("projectId")

    if DB_AVAILABLE and database_service.is_available:
        try:
            scene = database_service.create_scene(name=name, project_id=project_id)
            return {"success": True, "scene": scene}
        except Exception as e:
            print(f"⚠️ DB scene create failed, falling back to memory: {e}")

    scene_id = str(uuid.uuid4())
    scene_data = {
        "sceneId": scene_id,
        "name": name,
        "products": [],
        "createdAt": time.time(),
    }
    _scenes[scene_id] = scene_data
    return {"success": True, "scene": scene_data}

@app.get("/api/scene/{scene_id}")
async def get_scene(request: Request, scene_id: str):
    """Get scene details with all products"""
    _require_auth(request)
    if DB_AVAILABLE and database_service.is_available:
        try:
            scene = database_service.get_scene(scene_id)
            if scene:
                return {"success": True, **scene}
        except Exception as e:
            print(f"⚠️ DB scene get failed, falling back to memory: {e}")

    scene = _scenes.get(scene_id)
    if not scene:
        return {"success": True, "sceneId": scene_id, "name": "Default Scene", "products": []}
    return {"success": True, **scene}

@app.post("/api/scene/{scene_id}/add-product")
async def add_product_to_scene(request: Request, scene_id: str, product: dict = None):
    """Add a product to the scene"""
    _require_auth(request)
    if product is None:
        product = await request.json()
    if "instanceId" not in product or not product["instanceId"]:
        product["instanceId"] = str(uuid.uuid4())
    product.setdefault("position", {"x": 0, "y": 0, "z": 0})
    product.setdefault("rotation", {"x": 0, "y": 0, "z": 0})
    product.setdefault("scale", {"x": 1, "y": 1, "z": 1})

    if DB_AVAILABLE and database_service.is_available:
        try:
            saved = database_service.add_scene_product(scene_id, product)
            return {"success": True, "sceneId": scene_id, "product": saved}
        except Exception as e:
            print(f"⚠️ DB add product failed, falling back to memory: {e}")

    _products[product["instanceId"]] = product
    if scene_id in _scenes:
        _scenes[scene_id]["products"].append(product)
    else:
        raise HTTPException(status_code=404, detail=f"Scene {scene_id} not found")
    return {"success": True, "sceneId": scene_id, "product": product}

@app.put("/api/scene/product/{instance_id}/transform")
async def update_product_transform(request: Request, instance_id: str, transform: dict = None):
    """Update a product's position/rotation/scale in the scene"""
    _require_auth(request)
    if transform is None:
        transform = await request.json()
    pos = transform.get("position")
    rot = transform.get("rotation")
    scl = transform.get("scale")

    if DB_AVAILABLE and database_service.is_available:
        try:
            updated = database_service.update_scene_product_transform(instance_id, position=pos, rotation=rot, scale=scl)
            if updated:
                return {"success": True, "instanceId": instance_id, "position": updated["position"], "rotation": updated["rotation"], "scale": updated["scale"]}
        except Exception as e:
            print(f"⚠️ DB transform update failed, falling back to memory: {e}")

    p = _products.get(instance_id, {})
    p["position"] = pos or p.get("position", {"x": 0, "y": 0, "z": 0})
    p["rotation"] = rot or p.get("rotation", {"x": 0, "y": 0, "z": 0})
    p["scale"] = scl or p.get("scale", {"x": 1, "y": 1, "z": 1})
    return {"success": True, "instanceId": instance_id, "position": p["position"], "rotation": p["rotation"], "scale": p["scale"]}

@app.post("/api/scene/product/{instance_id}/duplicate")
async def duplicate_product(request: Request, instance_id: str, options: dict = None):
    """Duplicate a product in the scene with an offset"""
    _require_auth(request)
    if options is None:
        try:
            options = await request.json()
        except Exception:
            options = {}
    original = _products.get(instance_id)
    # Fall back to DB if not in memory
    if not original and DB_AVAILABLE and database_service.is_available:
        try:
            result = database_service.client.table("scene_products").select("*").eq("instance_id", instance_id).execute()
            if result.data:
                row = result.data[0]
                original = database_service._scene_product_to_dict(row)
        except Exception as e:
            print(f"⚠️ DB lookup for duplicate failed: {e}")
    if not original:
        raise HTTPException(status_code=404, detail="Product not found")
    if options is None:
        options = {}
    offset = options.get("offset", {"x": 50, "y": 0, "z": 0})
    new_instance_id = str(uuid.uuid4())
    new_product = {
        **original,
        "instanceId": new_instance_id,
        "position": offset,
    }
    _products[new_instance_id] = new_product
    # Add to the same scene
    for scene in list(_scenes.values()):
        if any(p.get("instanceId") == instance_id for p in scene["products"]):
            scene["products"].append(new_product)
            break
    return {"success": True, "duplicate": {"instanceId": new_instance_id, "originalId": instance_id, "position": offset}}

@app.delete("/api/scene/product/{instance_id}")
async def delete_product_from_scene(request: Request, instance_id: str):
    """Remove a product from the scene"""
    _require_auth(request)
    if DB_AVAILABLE and database_service.is_available:
        try:
            database_service.delete_scene_product(instance_id)
            return {"success": True, "deleted": instance_id}
        except Exception as e:
            print(f"⚠️ DB delete product failed, falling back to memory: {e}")

    _products.pop(instance_id, None)
    for scene in list(_scenes.values()):
        scene["products"] = [p for p in scene["products"] if p.get("instanceId") != instance_id]
    return {"success": True, "deleted": instance_id}

@app.post("/api/scene/{scene_id}/assemble")
async def assemble_products(request: Request, scene_id: str, assembly: dict):
    """Group products into an assembly (not yet implemented)"""
    _require_auth(request)
    raise HTTPException(status_code=501, detail="Assembly grouping not yet implemented")

@app.delete("/api/scene/assembly/{assembly_id}")
async def disassemble_products(request: Request, assembly_id: str):
    """Break an assembly back into individual products (not yet implemented)"""
    _require_auth(request)
    raise HTTPException(status_code=501, detail="Assembly disassembly not yet implemented")


# ── Assembly STEP Export (F34) ───────────────────────────────────────
@app.post("/api/scene/export-assembly")
async def export_assembly_step(request: Request, body: dict):
    """
    Merge multiple scene products into a single assembly STEP file.
    Expects { "buildIds": ["id1", "id2", ...], "name": "My Assembly" }
    Each buildId must have a .step file in exports/cad/.
    """
    _require_auth(request)
    import cadquery as cq

    build_ids = body.get("buildIds", [])
    assembly_name = body.get("name", "Assembly")

    if not build_ids:
        raise HTTPException(status_code=400, detail="No buildIds provided")

    # Validate all buildIds to prevent path traversal
    for bid in build_ids:
        _validate_build_id(bid)

    assembly = cq.Assembly(name=assembly_name)
    found = 0

    for bid in build_ids:
        step_path = settings.CAD_DIR / f"{bid}.step"
        if not step_path.exists():
            continue
        try:
            shape = cq.importers.importStep(str(step_path))
            assembly.add(shape, name=f"part_{bid[:8]}")
            found += 1
        except Exception as e:
            print(f"⚠️ Could not load {bid}.step into assembly: {e}")

    if found == 0:
        raise HTTPException(status_code=404, detail="No valid STEP files found for the given buildIds")

    # Export merged assembly
    assembly_id = str(uuid.uuid4())
    assembly_path = settings.CAD_DIR / f"{assembly_id}_assembly.step"
    assembly.save(str(assembly_path))

    return {
        "success": True,
        "assemblyFile": f"/exports/cad/{assembly_id}_assembly.step",
        "assemblyId": assembly_id,
        "partsCount": found,
        "name": assembly_name,
    }


# ── Material Metadata (F37) ─────────────────────────────────────────

MATERIAL_LIBRARY = {
    "pla": {"name": "PLA", "density": 1.24, "color": "#FFFFFF", "finish": "matte", "category": "3D Print"},
    "abs": {"name": "ABS", "density": 1.05, "color": "#F5F5DC", "finish": "matte", "category": "3D Print"},
    "petg": {"name": "PETG", "density": 1.27, "color": "#E0E0E0", "finish": "glossy", "category": "3D Print"},
    "nylon": {"name": "Nylon", "density": 1.15, "color": "#FFFDD0", "finish": "matte", "category": "3D Print"},
    "resin": {"name": "Resin (SLA)", "density": 1.18, "color": "#D3D3D3", "finish": "smooth", "category": "3D Print"},
    "aluminum": {"name": "Aluminum 6061", "density": 2.70, "color": "#C0C0C0", "finish": "machined", "category": "Metal"},
    "steel": {"name": "Steel (Mild)", "density": 7.85, "color": "#808080", "finish": "machined", "category": "Metal"},
    "stainless": {"name": "Stainless Steel 304", "density": 8.00, "color": "#A8A8A8", "finish": "brushed", "category": "Metal"},
    "titanium": {"name": "Titanium Grade 5", "density": 4.43, "color": "#878681", "finish": "machined", "category": "Metal"},
    "brass": {"name": "Brass", "density": 8.50, "color": "#B5A642", "finish": "polished", "category": "Metal"},
    "copper": {"name": "Copper", "density": 8.96, "color": "#B87333", "finish": "polished", "category": "Metal"},
    "wood_oak": {"name": "Oak", "density": 0.63, "color": "#C19A6B", "finish": "natural", "category": "Wood"},
    "wood_pine": {"name": "Pine", "density": 0.51, "color": "#DEB887", "finish": "natural", "category": "Wood"},
    "acrylic": {"name": "Acrylic (PMMA)", "density": 1.18, "color": "#E0F7FA", "finish": "glossy", "category": "Plastic"},
    "polycarbonate": {"name": "Polycarbonate", "density": 1.20, "color": "#F0F0F0", "finish": "glossy", "category": "Plastic"},
    "carbon_fiber": {"name": "Carbon Fiber Composite", "density": 1.55, "color": "#333333", "finish": "woven", "category": "Composite"},
}

@app.get("/api/materials")
async def list_materials():
    """List all available materials"""
    return {"success": True, "materials": MATERIAL_LIBRARY}

@app.get("/api/materials/{build_id}")
async def get_material(build_id: str):
    """Get material metadata for a build"""
    # Try DB first
    if DB_AVAILABLE and database_service.is_available:
        try:
            mat = database_service.get_material(build_id)
            if mat:
                return {"success": True, "material": mat}
        except Exception:
            pass
    mat = _material_metadata.get(build_id, None)
    if not mat:
        return {"success": True, "material": None, "message": "No material assigned"}
    return {"success": True, "material": mat}

@app.put("/api/materials/{build_id}")
async def set_material(request: Request, build_id: str, body: dict):
    """
    Assign material metadata to a build.
    Expects { "materialId": "aluminum", "color": "#C0C0C0", "finish": "brushed", "notes": "..." }
    """
    _require_auth(request)
    _validate_build_id(build_id)
    material_id = body.get("materialId", "")
    if material_id and material_id in MATERIAL_LIBRARY:
        base = MATERIAL_LIBRARY[material_id].copy()
    else:
        base = {"name": body.get("name", "Custom"), "density": body.get("density", 1.0), "category": "Custom"}
    
    base["color"] = body.get("color", base.get("color", "#CCCCCC"))
    base["finish"] = body.get("finish", base.get("finish", "unspecified"))
    base["notes"] = body.get("notes", "")
    base["materialId"] = material_id
    
    _material_metadata[build_id] = base
    
    # Estimate weight if we can read the STEP file volume
    step_path = settings.CAD_DIR / f"{build_id}.step"
    volume_cm3 = None
    weight_g = None
    if step_path.exists():
        try:
            import cadquery as cq
            shape = cq.importers.importStep(str(step_path))
            # CadQuery volumes are in mm³, convert to cm³
            bb = shape.val().BoundingBox()
            # Approximate volume from bounding box (real volume requires OCC Mass)
            try:
                from OCP.GProp import GProp_GProps
                from OCP.BRepGProp import brepgprop
                props = GProp_GProps()
                brepgprop.VolumeProperties(shape.val().wrapped, props)
                volume_cm3 = props.Mass() / 1000.0  # mm³ → cm³
            except Exception:
                # Fallback: bounding box volume * fill factor
                vol_mm3 = bb.xlen * bb.ylen * bb.zlen
                volume_cm3 = (vol_mm3 * 0.6) / 1000.0  # 60% fill estimate
            
            density = base.get("density", 1.0)
            weight_g = round(volume_cm3 * density, 2)
        except Exception as e:
            print(f"⚠️ Could not compute volume for {build_id}: {e}")
    
    base["volume_cm3"] = round(volume_cm3, 2) if volume_cm3 else None
    base["weight_g"] = weight_g

    # Persist to DB
    if DB_AVAILABLE and database_service.is_available:
        try:
            database_service.save_material(build_id, base)
        except Exception as e:
            print(f"⚠️ DB material save failed: {e}")

    return {"success": True, "material": base}


# ── Stripe Billing ──────────────────────────────────────────────────
STRIPE_AVAILABLE = False
try:
    import stripe as _stripe_mod
    if settings.STRIPE_SECRET_KEY:
        _stripe_mod.api_key = settings.STRIPE_SECRET_KEY
        STRIPE_AVAILABLE = True
        print("💳 Stripe billing enabled")
except ImportError:
    _stripe_mod = None

# Map plan+interval to Stripe Price IDs
STRIPE_PRICE_MAP = {
    ("pro", "monthly"): settings.STRIPE_PRO_PRICE_MONTHLY,
    ("pro", "yearly"): settings.STRIPE_PRO_PRICE_YEARLY,
    ("enterprise", "monthly"): settings.STRIPE_ENT_PRICE_MONTHLY,
    ("enterprise", "yearly"): settings.STRIPE_ENT_PRICE_YEARLY,
}

@app.post("/api/billing/checkout")
async def create_checkout_session(body: dict, request: Request):
    """
    Create a Stripe Checkout session.
    Expects { "planId": "pro"|"enterprise", "interval": "monthly"|"yearly" }
    Returns { "url": "<stripe checkout URL>" }
    """
    if not STRIPE_AVAILABLE:
        raise HTTPException(status_code=501, detail="Billing not configured. Set STRIPE_SECRET_KEY in .env")

    plan_id = body.get("planId", "")
    interval = body.get("interval", "monthly")
    price_id = STRIPE_PRICE_MAP.get((plan_id, interval))
    if not price_id:
        raise HTTPException(status_code=400, detail=f"No Stripe price configured for {plan_id}/{interval}")

    try:
        session = _stripe_mod.checkout.Session.create(
            mode="subscription",
            payment_method_types=["card"],
            line_items=[{"price": price_id, "quantity": 1}],
            success_url=f"{settings.FRONTEND_URL}/?checkout=success",
            cancel_url=f"{settings.FRONTEND_URL}/pricing?checkout=cancelled",
            metadata={"plan": plan_id, "interval": interval},
        )
        return {"success": True, "url": session.url}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/billing/portal")
async def create_billing_portal(body: dict):
    """
    Create a Stripe Customer Portal session for managing subscriptions.
    Expects { "customerId": "cus_xxx" }
    """
    if not STRIPE_AVAILABLE:
        raise HTTPException(status_code=501, detail="Billing not configured")
    customer_id = body.get("customerId", "")
    if not customer_id:
        raise HTTPException(status_code=400, detail="customerId required")
    try:
        session = _stripe_mod.billing_portal.Session.create(
            customer=customer_id,
            return_url=f"{settings.FRONTEND_URL}/pricing",
        )
        return {"success": True, "url": session.url}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/billing/webhook")
async def stripe_webhook(request: Request):
    """
    Handle Stripe webhook events (subscription create/update/cancel).
    Configure webhook endpoint in Stripe Dashboard → Developers → Webhooks.
    """
    if not STRIPE_AVAILABLE:
        raise HTTPException(status_code=501, detail="Billing not configured")

    payload = await request.body()
    sig_header = request.headers.get("stripe-signature", "")

    try:
        if not settings.STRIPE_WEBHOOK_SECRET:
            raise HTTPException(status_code=501, detail="Stripe webhook secret not configured — cannot verify events")
        event = _stripe_mod.Webhook.construct_event(payload, sig_header, settings.STRIPE_WEBHOOK_SECRET)
    except (ValueError, _stripe_mod.error.SignatureVerificationError) as e:
        raise HTTPException(status_code=400, detail=str(e))

    event_type = event["type"]
    data = event["data"]["object"]
    print(f"💳 Stripe event: {event_type}")

    if event_type == "checkout.session.completed":
        customer_id = data.get("customer")
        plan = data.get("metadata", {}).get("plan", "pro")
        print(f"  ✅ New subscription: customer={customer_id}, plan={plan}")
        # TODO: Update user's plan in Supabase (link customer_id to user)

    elif event_type in ("customer.subscription.updated", "customer.subscription.deleted"):
        customer_id = data.get("customer")
        status = data.get("status")
        print(f"  🔄 Subscription {event_type.split('.')[-1]}: customer={customer_id}, status={status}")
        # TODO: Update user's subscription status in Supabase

    return {"received": True}

@app.get("/api/billing/status")
async def billing_status():
    """Check if billing is configured"""
    return {"success": True, "enabled": STRIPE_AVAILABLE}


# ── BOM Generation (F39) ────────────────────────────────────────────
@app.post("/api/bom/generate")
async def generate_bom(request: Request, body: dict):
    """
    Generate a Bill of Materials from scene products.
    Expects { "items": [{ "buildId": "...", "name": "...", "quantity": 1 }] }
    Returns structured BOM data (JSON + CSV download).
    """
    _require_auth(request)
    items = body.get("items", [])
    if not items:
        raise HTTPException(status_code=400, detail="No items provided")
    
    bom_rows = []
    for idx, item in enumerate(items, 1):
        bid = item.get("buildId", "")
        if bid:
            _validate_build_id(bid)
        name = item.get("name", f"Part {idx}")
        qty = item.get("quantity", 1)
        
        # Try to get dimensions from STEP file
        dimensions = None
        volume_cm3 = None
        step_path = settings.CAD_DIR / f"{bid}.step"
        if step_path.exists():
            try:
                import cadquery as cq
                shape = cq.importers.importStep(str(step_path))
                bb = shape.val().BoundingBox()
                dimensions = {
                    "length_mm": round(bb.xlen, 2),
                    "width_mm": round(bb.ylen, 2),
                    "height_mm": round(bb.zlen, 2),
                }
                try:
                    from OCP.GProp import GProp_GProps
                    from OCP.BRepGProp import brepgprop
                    props = GProp_GProps()
                    brepgprop.VolumeProperties(shape.val().wrapped, props)
                    volume_cm3 = round(props.Mass() / 1000.0, 2)
                except Exception:
                    vol_mm3 = bb.xlen * bb.ylen * bb.zlen
                    volume_cm3 = round((vol_mm3 * 0.6) / 1000.0, 2)
            except Exception:
                pass
        
        # Get material if assigned
        mat = _material_metadata.get(bid, None)
        material_name = mat["name"] if mat else "Unspecified"
        weight_g = None
        if mat and volume_cm3:
            weight_g = round(volume_cm3 * mat.get("density", 1.0), 2)
        
        bom_rows.append({
            "item": idx,
            "name": name,
            "buildId": bid[:8] if bid else "",
            "quantity": qty,
            "material": material_name,
            "dimensions": dimensions,
            "volume_cm3": volume_cm3,
            "weight_g": weight_g,
            "total_weight_g": round(weight_g * qty, 2) if weight_g else None,
        })
    
    # Generate CSV string
    csv_lines = ["Item,Name,Build ID,Qty,Material,L(mm),W(mm),H(mm),Volume(cm³),Weight(g),Total Weight(g)"]
    for row in bom_rows:
        dims = row["dimensions"]
        csv_lines.append(",".join([
            str(row["item"]),
            f'"{row["name"]}"',
            row["buildId"],
            str(row["quantity"]),
            row["material"],
            str(dims["length_mm"]) if dims else "",
            str(dims["width_mm"]) if dims else "",
            str(dims["height_mm"]) if dims else "",
            str(row["volume_cm3"]) if row["volume_cm3"] else "",
            str(row["weight_g"]) if row["weight_g"] else "",
            str(row["total_weight_g"]) if row["total_weight_g"] else "",
        ]))
    
    # Save CSV file
    bom_id = str(uuid.uuid4())[:8]
    csv_path = settings.CAD_DIR / f"bom_{bom_id}.csv"
    csv_path.write_text("\n".join(csv_lines), encoding="utf-8")
    
    total_weight = sum(r["total_weight_g"] for r in bom_rows if r["total_weight_g"])
    
    return {
        "success": True,
        "bom": bom_rows,
        "summary": {
            "totalParts": len(bom_rows),
            "totalQuantity": sum(r["quantity"] for r in bom_rows),
            "totalWeight_g": round(total_weight, 2) if total_weight else None,
        },
        "csvFile": f"/exports/cad/bom_{bom_id}.csv",
    }


# ── 2D Drawing Export (F40) ─────────────────────────────────────────
@app.post("/api/export/2d")
async def export_2d_drawing(request: Request, body: dict):
    """
    Generate 2D engineering drawing projections from a STEP model.
    Expects { "buildId": "...", "views": ["front", "top", "right", "iso"] }
    Returns SVG drawing file.
    """
    _require_auth(request)
    import cadquery as cq

    build_id = body.get("buildId", "")
    _validate_build_id(build_id)
    views = body.get("views", ["front", "top", "right"])

    step_path = settings.CAD_DIR / f"{build_id}.step"
    if not step_path.exists():
        raise HTTPException(status_code=404, detail=f"STEP file not found for build {build_id}")

    try:
        shape = cq.importers.importStep(str(step_path))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Could not load STEP file: {e}")

    # Generate SVG with CadQuery's built-in SVG exporter
    try:
        drawing_id = str(uuid.uuid4())[:8]
        svg_path = settings.CAD_DIR / f"{build_id}_drawing_{drawing_id}.svg"
        
        # CadQuery exporters.export with SVG format
        # Generate orthographic views as SVG
        from cadquery import exporters
        
        # Build multi-view SVG
        svg_parts = []
        svg_parts.append('<?xml version="1.0" encoding="UTF-8"?>')
        svg_parts.append('<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="900" viewBox="0 0 1200 900">')
        svg_parts.append('<style>line,path{stroke:#000;stroke-width:0.5;fill:none} text{font:10px monospace;fill:#333} .hidden{stroke:#999;stroke-dasharray:4,2;stroke-width:0.3} .title{font:bold 14px sans-serif} .dim{font:9px sans-serif;fill:#0066cc}</style>')
        svg_parts.append('<rect width="1200" height="900" fill="white" stroke="#ccc"/>')
        
        # Get bounding box for scaling
        bb = shape.val().BoundingBox()
        dims = {"L": round(bb.xlen, 1), "W": round(bb.ylen, 1), "H": round(bb.zlen, 1)}
        
        # Title block
        svg_parts.append('<rect x="10" y="850" width="1180" height="40" fill="#f0f0f0" stroke="#333"/>')
        svg_parts.append(f'<text x="20" y="875" class="title">Engineering Drawing — Build {build_id[:8]}</text>')
        svg_parts.append(f'<text x="600" y="875" class="dim">Dimensions: {dims["L"]} × {dims["W"]} × {dims["H"]} mm</text>')
        svg_parts.append(f'<text x="1050" y="875" class="dim">Scale: Fit</text>')
        
        view_configs = {
            "front": {"label": "FRONT VIEW", "x": 50, "y": 50, "w": 500, "h": 380, "dir": (0, -1, 0)},
            "top": {"label": "TOP VIEW", "x": 50, "y": 450, "w": 500, "h": 380, "dir": (0, 0, 1)},
            "right": {"label": "RIGHT VIEW", "x": 600, "y": 50, "w": 500, "h": 380, "dir": (1, 0, 0)},
            "iso": {"label": "ISOMETRIC VIEW", "x": 600, "y": 450, "w": 500, "h": 380, "dir": (1, -1, 1)},
        }
        
        for view_name in views:
            cfg = view_configs.get(view_name)
            if not cfg:
                continue
            
            # Draw view frame
            svg_parts.append(f'<rect x="{cfg["x"]}" y="{cfg["y"]}" width="{cfg["w"]}" height="{cfg["h"]}" fill="none" stroke="#ccc" stroke-width="0.5"/>')
            svg_parts.append(f'<text x="{cfg["x"] + 10}" y="{cfg["y"] + 20}" class="title">{cfg["label"]}</text>')
            
            try:
                # Use CadQuery SVG export for this view direction
                view_svg = exporters.exportShape(
                    shape,
                    "SVG",
                    opt={
                        "projectionDir": cfg["dir"],
                        "showHidden": True,
                        "width": cfg["w"] - 40,
                        "height": cfg["h"] - 40,
                    }
                )
                
                # Extract just the path/line elements from the generated SVG
                paths = re.findall(r'<(path|line|circle|ellipse|polygon|polyline)[^>]*/?>', view_svg)
                
                # Embed within positioned group
                svg_parts.append(f'<g transform="translate({cfg["x"] + 20},{cfg["y"] + 30})">')
                for p in paths:
                    svg_parts.append(f'<{p}>')
                svg_parts.append('</g>')
                
            except Exception as view_err:
                # Fallback: draw bounding box outline
                svg_parts.append(f'<g transform="translate({cfg["x"] + 20},{cfg["y"] + 30})">')
                svg_parts.append(f'<rect x="50" y="50" width="{cfg["w"] - 140}" height="{cfg["h"] - 100}" fill="none" stroke="#333" stroke-width="1"/>')
                svg_parts.append(f'<text x="{(cfg["w"] - 140) // 2}" y="{(cfg["h"] - 100) // 2}" text-anchor="middle" class="dim">View generation requires OCC visualization</text>')
                svg_parts.append('</g>')
        
        # Dimension annotations
        svg_parts.append(f'<text x="300" y="{view_configs["front"]["y"] + view_configs["front"]["h"] + 15}" text-anchor="middle" class="dim">↔ {dims["L"]} mm</text>')
        svg_parts.append(f'<text x="{view_configs["right"]["x"] + view_configs["right"]["w"] + 15}" y="240" class="dim" transform="rotate(90, {view_configs["right"]["x"] + view_configs["right"]["w"] + 15}, 240)">↕ {dims["H"]} mm</text>')
        
        svg_parts.append('</svg>')
        
        svg_content = '\n'.join(svg_parts)
        svg_path.write_text(svg_content, encoding="utf-8")
        
        return {
            "success": True,
            "svgFile": f"/exports/cad/{build_id}_drawing_{drawing_id}.svg",
            "dimensions": dims,
            "views": views,
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Drawing generation failed: {e}")


@app.get("/api/cache/check")
async def check_cache(request: Request, prompt: str):
    """Check if a prompt has a cached build result"""
    user_id = request.state.user.get("id") if getattr(request.state, "user", None) else None
    cached = _check_prompt_cache(prompt, user_id)
    if cached:
        return {"success": True, "cached": True, "result": cached}
    return {"success": True, "cached": False}



# ── File Upload & NLP Edit Endpoints ─────────────────────────────────────

@app.get("/api/upload/formats")
async def get_supported_formats():
    """Return list of supported upload formats"""
    return {"success": True, **cad_import_service.get_supported_formats()}

@app.post("/api/upload")
async def upload_cad_file(request: Request, file: UploadFile = File(...)):
    """
    Upload a CAD file for visualization and NLP editing.
    Supports STEP, STL, IGES, DXF, OBJ, 3MF, PLY, BRep, GLB, glTF.
    """
    _require_auth(request)
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file provided")

    ext = Path(file.filename).suffix.lower()
    if ext not in CAD_SUPPORTED_FORMATS:
        supported = ", ".join(sorted(CAD_SUPPORTED_FORMATS.keys()))
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported format '{ext}'. Supported: {supported}"
        )

    # Read file content
    file_bytes = await file.read()
    max_size_mb = 100
    if len(file_bytes) > max_size_mb * 1024 * 1024:
        raise HTTPException(
            status_code=413,
            detail=f"File too large. Maximum size is {max_size_mb} MB."
        )

    try:
        result = await cad_import_service.import_file(
            file_bytes=file_bytes,
            original_filename=file.filename,
        )
        print(f"📤 File uploaded: {file.filename} → {result['buildId']}")
        print(f"   Format: {result['format']} | BBox: {result.get('boundingBox', {})}")
        print(f"   Editable (NLP): {result['editable']}")
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Import failed: {str(e)}")


class NLPEditRequest(BaseModel):
    buildId: str
    prompt: str
    importCode: Optional[str] = None
    previousDesign: Optional[Dict[str, Any]] = None

@app.post("/api/upload/edit")
async def nlp_edit_uploaded_file(request: Request, body: NLPEditRequest):
    """
    Apply a natural language edit to an uploaded CAD file.
    Sends the import code + user prompt to Claude for code generation,
    then executes the modified CadQuery code.
    """
    _require_auth(request)
    # Build "previous design" with the import code as the starting point
    import_code = body.importCode or ""
    if not import_code and body.previousDesign:
        import_code = body.previousDesign.get("code", "")

    if not import_code:
        raise HTTPException(
            status_code=400,
            detail="No import code or previous design provided for editing."
        )

    # Send to Claude as a modification of the import code
    previous_design = {
        "code": import_code,
        "parameters": body.previousDesign.get("parameters", []) if body.previousDesign else [],
        "explanation": body.previousDesign.get("explanation", {}) if body.previousDesign else {},
    }

    ai_response = None
    try:
        ai_response = await claude_service.generate_design_from_prompt(
            prompt=body.prompt,
            previous_design=previous_design,
        )

        # Execute the AI-modified code
        cad_result = await parametric_cad_service.generate_parametric_cad(ai_response)

        return {
            "success": True,
            "buildId": cad_result["buildId"],
            "stlUrl": cad_result["stlFile"],
            "stepUrl": cad_result["stepFile"],
            "parametricScript": cad_result.get("parametricScript"),
            "parameters": cad_result.get("parameters"),
            "explanation": cad_result.get("explanation"),
            "design": {
                "parameters": ai_response.get("parameters", []),
                "code": ai_response.get("code", ""),
                "explanation": ai_response.get("explanation", {}),
            },
        }
    except (RuntimeError, ValueError) as cad_err:
        # Self-healing: try fixing once
        try:
            failed_code = ai_response.get("code", "") if ai_response else import_code
            fixed_response = await claude_service.fix_code_with_error(
                failed_code=failed_code,
                error_message=str(cad_err),
                original_prompt=body.prompt,
                attempt=1,
                max_retries=3,
            )
            cad_result = await parametric_cad_service.generate_parametric_cad(fixed_response)
            return {
                "success": True,
                "buildId": cad_result["buildId"],
                "stlUrl": cad_result["stlFile"],
                "stepUrl": cad_result["stepFile"],
                "parametricScript": cad_result.get("parametricScript"),
                "parameters": cad_result.get("parameters"),
                "explanation": cad_result.get("explanation"),
                "design": {
                    "parameters": fixed_response.get("parameters", []),
                    "code": fixed_response.get("code", ""),
                    "explanation": fixed_response.get("explanation", {}),
                },
                "healed": True,
            }
        except Exception as heal_err:
            raise HTTPException(
                status_code=500,
                detail=f"Edit failed after self-healing: {str(heal_err)}"
            )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"NLP edit failed: {str(e)}")


# Also serve uploaded files
@app.get("/exports/uploads/{filename}")
async def serve_upload_file(filename: str):
    """Serve uploaded source files"""
    safe_name = Path(filename).name
    file_path = (Path(settings.EXPORTS_DIR) / "uploads" / safe_name).resolve()
    if not str(file_path).startswith(str((Path(settings.EXPORTS_DIR) / "uploads").resolve())):
        raise HTTPException(status_code=400, detail="Invalid filename")
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(file_path)


# ── Project & History Endpoints (MySQL) ─────────────────────────────────

class ProjectCreateRequest(BaseModel):
    name: str = "Untitled Project"
    description: Optional[str] = None

class ProjectUpdateRequest(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None

class SaveMessageRequest(BaseModel):
    projectId: str
    role: str
    content: str
    buildResult: Optional[Dict[str, Any]] = None
    status: Optional[str] = None

@app.get("/api/projects")
async def list_projects(request: Request):
    """List all saved projects for the current user"""
    if not DB_AVAILABLE:
        return {"success": True, "projects": []}
    try:
        user_id = None
        if hasattr(request.state, 'user') and request.state.user:
            user_id = request.state.user.get("id")
        projects = database_service.list_projects(user_id=user_id)
        return {"success": True, "projects": projects}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/projects")
async def create_project(request: Request, body: ProjectCreateRequest):
    """Create a new project"""
    if not DB_AVAILABLE:
        raise HTTPException(status_code=503, detail="Database not available")
    try:
        user_id = None
        if hasattr(request.state, 'user') and request.state.user:
            user_id = request.state.user.get("id")
        project = database_service.create_project(name=body.name, description=body.description, user_id=user_id)
        return {"success": True, "project": project}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/projects/{project_id}")
async def get_project(request: Request, project_id: str):
    """Get project with all builds and chat messages"""
    _require_auth(request)
    if not DB_AVAILABLE:
        raise HTTPException(status_code=503, detail="Database not available")
    try:
        project = database_service.get_project(project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        return {"success": True, "project": project}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/api/projects/{project_id}")
async def update_project(request: Request, project_id: str, body: ProjectUpdateRequest):
    """Update project name or description"""
    _require_auth(request)
    if not DB_AVAILABLE:
        raise HTTPException(status_code=503, detail="Database not available")
    try:
        project = database_service.update_project(project_id, name=body.name, description=body.description)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        return {"success": True, "project": project}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/projects/{project_id}")
async def delete_project(request: Request, project_id: str):
    """Delete a project and all its builds/messages"""
    _require_auth(request)
    if not DB_AVAILABLE:
        raise HTTPException(status_code=503, detail="Database not available")
    try:
        deleted = database_service.delete_project(project_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="Project not found")
        return {"success": True, "message": "Project deleted"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/messages")
async def save_message(request: Request, body: SaveMessageRequest):
    """Save a chat message to a project"""
    _require_auth(request)
    if not DB_AVAILABLE:
        raise HTTPException(status_code=503, detail="Database not available")
    try:
        msg = database_service.save_chat_message(
            project_id=body.projectId,
            role=body.role,
            content=body.content,
            build_result=body.buildResult,
            status=body.status,
        )
        return {"success": True, "message": msg}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/history")
async def get_build_history(request: Request):
    """Get recent builds across all projects"""
    _require_auth(request)
    if not DB_AVAILABLE:
        return {"success": True, "builds": []}
    try:
        builds = database_service.get_all_builds(limit=50)
        return {"success": True, "builds": builds}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# File serving endpoint
@app.get("/exports/cad/{filename}")
async def serve_cad_file(filename: str):
    """Serve generated CAD files (STL, STEP, SVG, CSV, PY)"""
    # Reject obvious traversal / hidden / empty names / NUL bytes early
    if (
        not filename
        or filename.startswith(".")
        or "/" in filename
        or "\\" in filename
        or "\x00" in filename
        or "%" in filename  # reject percent-encoded payloads outright
        or len(filename) > 200
    ):
        raise HTTPException(status_code=400, detail="Invalid filename")
    safe_name = Path(filename).name
    # Allowlist by extension — anything else is not a CAD artifact we produce
    allowed_ext = {".stl", ".step", ".stp", ".svg", ".csv", ".py", ".glb"}
    if Path(safe_name).suffix.lower() not in allowed_ext:
        raise HTTPException(status_code=400, detail="Unsupported file type")
    file_path = (CAD_DIR / safe_name).resolve()
    try:
        file_path.relative_to(CAD_DIR.resolve())
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid filename")
    if not file_path.exists() or not file_path.is_file():
        raise HTTPException(status_code=404, detail="File not found")
    # Set proper media type based on extension
    suffix = file_path.suffix.lower()
    media_types = {
        ".stl": "application/octet-stream",
        ".step": "application/octet-stream",
        ".stp": "application/octet-stream",
        ".svg": "image/svg+xml",
        ".csv": "text/csv",
        ".py": "text/x-python",
        ".glb": "model/gltf-binary",
    }
    media_type = media_types.get(suffix, "application/octet-stream")
    return FileResponse(file_path, media_type=media_type)

# ═══════════════════════════════════════════════════════════════
# F36: Version History — Save, list, restore, compare design snapshots
# ═══════════════════════════════════════════════════════════════

class VersionSaveRequest(BaseModel):
    buildId: str
    label: Optional[str] = ""
    design: Optional[Dict[str, Any]] = None
    code: Optional[str] = None
    parameters: Optional[list] = None

class VersionRestoreRequest(BaseModel):
    buildId: str
    versionId: str

@app.post("/api/versions/save")
async def version_save(request: Request):
    """Save a version snapshot for a build"""
    _require_auth(request)
    try:
        body = await request.json()
        build_id = body.get("buildId", "")
        _validate_build_id(build_id)

        # Try to read the current parametric script for code
        code = body.get("code", "") or ""
        if not code:
            script_path = Path(CAD_DIR) / f"{build_id}_parametric.py"
            if script_path.exists():
                code = script_path.read_text(encoding="utf-8", errors="replace")

        # Use database if available
        if DB_AVAILABLE and database_service.is_available:
            existing = database_service.list_versions(build_id)
            label = body.get("label", "") or f"v{len(existing) + 1}"
            version = database_service.save_version(
                build_id=build_id,
                label=label,
                code=code,
                parameters=body.get("parameters"),
                explanation=body.get("design", {}).get("explanation") if isinstance(body.get("design"), dict) else body.get("design"),
                prompt=None,
            )
            total = len(existing) + 1
            return {"success": True, "versionId": version["id"], "totalVersions": total}
        else:
            # In-memory fallback
            if build_id not in _version_history:
                _version_history[build_id] = []

            version_id = str(uuid.uuid4())[:8]
            now = datetime.datetime.now().isoformat()

            snapshot = {
                "versionId": version_id,
                "timestamp": now,
                "label": body.get("label", "") or f"v{len(_version_history[build_id]) + 1}",
                "design": body.get("design"),
                "code": code,
                "parameters": body.get("parameters"),
            }

            _version_history[build_id].append(snapshot)

            if len(_version_history[build_id]) > 50:
                _version_history[build_id] = _version_history[build_id][-50:]

            return {"success": True, "versionId": version_id, "totalVersions": len(_version_history[build_id])}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/versions/{build_id}")
async def version_list(request: Request, build_id: str):
    """List all saved versions for a build"""
    _require_auth(request)
    if DB_AVAILABLE and database_service.is_available:
        db_versions = database_service.list_versions(build_id)
        return {
            "success": True,
            "buildId": build_id,
            "versions": [
                {"versionId": v["id"], "timestamp": v["created_at"], "label": v["label"],
                 "hasCode": bool(v.get("code")), "hasParameters": bool(v.get("parameters"))}
                for v in db_versions
            ],
            "count": len(db_versions),
        }
    else:
        versions = _version_history.get(build_id, [])
        return {
            "success": True,
            "buildId": build_id,
            "versions": [
                {"versionId": v["versionId"], "timestamp": v["timestamp"], "label": v["label"],
                 "hasCode": bool(v.get("code")), "hasParameters": bool(v.get("parameters"))}
                for v in versions
            ],
            "count": len(versions),
        }


@app.post("/api/versions/restore")
async def version_restore(request: Request):
    """Restore a previous version — re-execute its code to regenerate files"""
    _require_auth(request)
    body = await request.json()
    restore_build_id = body.get("buildId", "")
    restore_version_id = body.get("versionId", "")
    # Validate IDs to prevent path traversal
    import re as _re_ver
    if not _re_ver.match(r'^[a-zA-Z0-9_-]+$', restore_build_id or ''):
        raise HTTPException(status_code=400, detail="Invalid buildId format")
    if not _re_ver.match(r'^[a-zA-Z0-9_-]+$', restore_version_id or ''):
        raise HTTPException(status_code=400, detail="Invalid versionId format")
    try:
        target = None
        if DB_AVAILABLE and database_service.is_available:
            target = database_service.get_version(restore_version_id)
            if target:
                # Normalize keys to match in-memory format
                target = {
                    "versionId": target["id"],
                    "code": target.get("code", ""),
                    "parameters": target.get("parameters"),
                    "design": {"explanation": target.get("explanation", {})} if target.get("explanation") else None,
                }
        else:
            versions = _version_history.get(restore_build_id, [])
            target = next((v for v in versions if v["versionId"] == restore_version_id), None)

        if not target:
            raise HTTPException(status_code=404, detail="Version not found")

        code = target.get("code", "")
        if not code:
            raise HTTPException(status_code=400, detail="No code saved in this version")

        # Re-execute the code to regenerate the model
        new_build_id = f"{restore_build_id}_r{restore_version_id}"
        design_json = {
            "parameters": target.get("parameters", []),
            "code": code,
            "explanation": target.get("design", {}).get("explanation", {}) if target.get("design") else {},
        }

        cad_result = await parametric_cad_service.generate_parametric_cad(design_json, build_id=new_build_id)

        return {
            "success": True,
            "buildId": new_build_id,
            "stlFile": f"/exports/cad/{new_build_id}.stl",
            "stepFile": f"/exports/cad/{new_build_id}.step",
            "design": target.get("design"),
            "parameters": target.get("parameters"),
            "restoredFrom": restore_version_id,
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/versions/{build_id}/compare/{version_a}/{version_b}")
async def version_compare(request: Request, build_id: str, version_a: str, version_b: str):
    """Compare two versions — show parameter and code differences"""
    _require_auth(request)
    va = None
    vb = None

    if DB_AVAILABLE and database_service.is_available:
        va_raw = database_service.get_version(version_a)
        vb_raw = database_service.get_version(version_b)
        if va_raw:
            va = {"versionId": va_raw.get("id", version_a), "label": va_raw.get("label", ""), "timestamp": va_raw.get("created_at", ""),
                  "code": va_raw.get("code", ""), "parameters": va_raw.get("parameters")}
        if vb_raw:
            vb = {"versionId": vb_raw.get("id", version_b), "label": vb_raw.get("label", ""), "timestamp": vb_raw.get("created_at", ""),
                  "code": vb_raw.get("code", ""), "parameters": vb_raw.get("parameters")}
    else:
        versions = _version_history.get(build_id, [])
        va = next((v for v in versions if v["versionId"] == version_a), None)
        vb = next((v for v in versions if v["versionId"] == version_b), None)

    if not va or not vb:
        raise HTTPException(status_code=404, detail="Version(s) not found")

    # Compare parameters
    param_diffs = []
    params_a = {p["name"]: p for p in (va.get("parameters") or [])}
    params_b = {p["name"]: p for p in (vb.get("parameters") or [])}
    all_params = set(list(params_a.keys()) + list(params_b.keys()))
    for pname in sorted(all_params):
        pa = params_a.get(pname, {})
        pb = params_b.get(pname, {})
        if pa.get("default") != pb.get("default"):
            param_diffs.append({
                "name": pname,
                "valueA": pa.get("default"),
                "valueB": pb.get("default"),
            })

    # Code diff summary
    code_a = va.get("code", "")
    code_b = vb.get("code", "")
    lines_a = code_a.count("\n")
    lines_b = code_b.count("\n")

    return {
        "success": True,
        "versionA": {"versionId": version_a, "label": va["label"], "timestamp": va["timestamp"]},
        "versionB": {"versionId": version_b, "label": vb["label"], "timestamp": vb["timestamp"]},
        "parameterDiffs": param_diffs,
        "codeLinesA": lines_a,
        "codeLinesB": lines_b,
        "codeChanged": code_a != code_b,
    }


# ═══════════════════════════════════════════════════════════════
# F38: 3D Printer Slicing — Slicer settings and print estimation
# ═══════════════════════════════════════════════════════════════

SLICER_PRESETS = {
    "draft": {"layer_height": 0.3, "infill": 10, "shells": 2, "speed": 80, "supports": False, "quality": "Draft"},
    "normal": {"layer_height": 0.2, "infill": 20, "shells": 3, "speed": 60, "supports": False, "quality": "Normal"},
    "fine": {"layer_height": 0.12, "infill": 25, "shells": 4, "speed": 40, "supports": False, "quality": "Fine"},
    "ultra": {"layer_height": 0.08, "infill": 30, "shells": 5, "speed": 30, "supports": False, "quality": "Ultra Fine"},
    "strong": {"layer_height": 0.2, "infill": 60, "shells": 5, "speed": 50, "supports": False, "quality": "Strong"},
    "vase": {"layer_height": 0.2, "infill": 0, "shells": 1, "speed": 40, "supports": False, "quality": "Vase Mode"},
}

FILAMENT_DB = {
    "pla": {"name": "PLA", "temp_nozzle": 210, "temp_bed": 60, "density": 1.24, "cost_per_kg": 20},
    "abs": {"name": "ABS", "temp_nozzle": 240, "temp_bed": 100, "density": 1.05, "cost_per_kg": 22},
    "petg": {"name": "PETG", "temp_nozzle": 235, "temp_bed": 80, "density": 1.27, "cost_per_kg": 25},
    "tpu": {"name": "TPU", "temp_nozzle": 225, "temp_bed": 50, "density": 1.21, "cost_per_kg": 35},
    "nylon": {"name": "Nylon", "temp_nozzle": 260, "temp_bed": 80, "density": 1.15, "cost_per_kg": 40},
    "resin": {"name": "Resin", "temp_nozzle": 0, "temp_bed": 0, "density": 1.18, "cost_per_kg": 50},
}

class SliceRequest(BaseModel):
    buildId: str
    preset: Optional[str] = "normal"
    filament: Optional[str] = "pla"
    layerHeight: Optional[float] = None
    infill: Optional[int] = None
    shells: Optional[int] = None
    speed: Optional[int] = None
    supports: Optional[bool] = None
    nozzleDiameter: Optional[float] = 0.4
    bedSizeX: Optional[float] = 220
    bedSizeY: Optional[float] = 220
    bedSizeZ: Optional[float] = 250


@app.post("/api/slicer/estimate")
async def slicer_estimate(request: Request, body: SliceRequest):
    """Estimate print time, material usage, and cost for a build"""
    _require_auth(request)
    try:
        _validate_build_id(body.buildId)
        # Get model dimensions from STEP file
        step_path = Path(CAD_DIR) / f"{body.buildId}.step"
        stl_path = Path(CAD_DIR) / f"{body.buildId}.stl"

        # Get bounding box and volume
        volume_cm3 = 0.0
        bbox = {"x": 50, "y": 50, "z": 30}  # fallback

        if step_path.exists():
            try:
                import cadquery as cq
                shape = cq.importers.importStep(str(step_path))
                bb = shape.val().BoundingBox()
                bbox = {"x": round(bb.xlen, 1), "y": round(bb.ylen, 1), "z": round(bb.zlen, 1)}
                # Volume from OCC (mm³ → cm³)
                from OCP.GProp import GProp_GProps
                from OCP.BRepGProp import brepgprop
                props = GProp_GProps()
                brepgprop.VolumeProperties(shape.val().wrapped, props)
                volume_cm3 = abs(props.Mass()) / 1000.0
            except Exception:
                # Estimate from bbox
                volume_cm3 = (bbox["x"] * bbox["y"] * bbox["z"]) / 1000.0 * 0.3

        if volume_cm3 <= 0:
            volume_cm3 = (bbox["x"] * bbox["y"] * bbox["z"]) / 1000.0 * 0.3

        # Merge preset with overrides
        preset = SLICER_PRESETS.get(body.preset, SLICER_PRESETS["normal"]).copy()
        if body.layerHeight is not None:
            preset["layer_height"] = body.layerHeight
        if body.infill is not None:
            preset["infill"] = body.infill
        if body.shells is not None:
            preset["shells"] = body.shells
        if body.speed is not None:
            preset["speed"] = body.speed
        if body.supports is not None:
            preset["supports"] = body.supports

        filament = FILAMENT_DB.get(body.filament, FILAMENT_DB["pla"])

        # Estimate calculations
        layer_height_mm = preset["layer_height"]
        infill_pct = preset["infill"] / 100.0
        shells = preset["shells"]
        speed = preset["speed"]
        nozzle = body.nozzleDiameter

        # Total layers
        model_height = bbox["z"]
        total_layers = int(model_height / layer_height_mm) if layer_height_mm > 0 else 100

        # Material volume: shell volume + infill volume
        shell_volume = volume_cm3 * 0.4 * (shells / 3.0)
        infill_volume = volume_cm3 * 0.6 * infill_pct
        support_volume = volume_cm3 * 0.15 if preset["supports"] else 0
        total_volume_cm3 = shell_volume + infill_volume + support_volume

        # Weight
        weight_g = total_volume_cm3 * filament["density"]

        # Filament length (1.75mm diameter)
        filament_area_cm2 = 3.14159 * (0.175 / 2) ** 2
        filament_length_cm = total_volume_cm3 / filament_area_cm2 if filament_area_cm2 > 0 else 0
        filament_length_m = filament_length_cm / 100.0

        # Print time estimate (simplified)
        # Average extrusion path per layer
        avg_perimeter = 2 * (bbox["x"] + bbox["y"])
        perimeter_time_per_layer = (avg_perimeter * shells) / (speed * 60)  # seconds
        infill_time_per_layer = (bbox["x"] * bbox["y"] * infill_pct) / (speed * 60 * nozzle / 0.4)
        layer_time = perimeter_time_per_layer + infill_time_per_layer + 2  # +2s travel

        total_time_seconds = total_layers * layer_time
        # Add non-print time (heating, retraction, layer change)
        total_time_seconds *= 1.3
        total_time_seconds += 120  # heat-up time

        hours = int(total_time_seconds / 3600)
        minutes = int((total_time_seconds % 3600) / 60)

        # Cost
        cost = (weight_g / 1000.0) * filament["cost_per_kg"]

        # Bed fit check
        fits_bed = (bbox["x"] <= body.bedSizeX and
                    bbox["y"] <= body.bedSizeY and
                    bbox["z"] <= body.bedSizeZ)

        # Need supports heuristic
        needs_supports = False
        if bbox["z"] > bbox["x"] * 2 or bbox["z"] > bbox["y"] * 2:
            needs_supports = True

        return {
            "success": True,
            "buildId": body.buildId,
            "settings": {
                "layerHeight": preset["layer_height"],
                "infill": preset["infill"],
                "shells": preset["shells"],
                "speed": preset["speed"],
                "supports": preset["supports"],
                "quality": preset.get("quality", "Custom"),
                "filament": filament["name"],
                "nozzleDiameter": nozzle,
                "nozzleTemp": filament["temp_nozzle"],
                "bedTemp": filament["temp_bed"],
            },
            "estimate": {
                "printTimeFormatted": f"{hours}h {minutes}m" if hours > 0 else f"{minutes}m",
                "printTimeSeconds": int(total_time_seconds),
                "totalLayers": total_layers,
                "weightGrams": round(weight_g, 1),
                "filamentLengthM": round(filament_length_m, 1),
                "volumeCm3": round(total_volume_cm3, 2),
                "costEstimate": round(cost, 2),
                "currency": "USD",
            },
            "model": {
                "boundingBox": bbox,
                "fitsBed": fits_bed,
                "needsSupports": needs_supports,
            },
            "presets": list(SLICER_PRESETS.keys()),
            "filaments": list(FILAMENT_DB.keys()),
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/slicer/presets")
async def slicer_presets():
    """List available slicer presets and filament types"""
    return {
        "success": True,
        "presets": {k: {**v, "id": k} for k, v in SLICER_PRESETS.items()},
        "filaments": {k: {**v, "id": k} for k, v in FILAMENT_DB.items()},
    }


# ═══════════════════════════════════════════════════════════════
# F35: Real-time Collaboration — WebSocket rooms
# ═══════════════════════════════════════════════════════════════

@app.post("/api/collab/create")
async def collab_create_room(request: Request):
    """Create a new collaboration room"""
    _require_auth(request)
    body = await request.json()
    host_name = str(body.get("hostName", "Anonymous"))[:50].strip() or "Anonymous"
    # Sanitize: strip HTML tags to prevent XSS
    import re as _re_collab
    host_name = _re_collab.sub(r'<[^>]+>', '', host_name)
    scene_id = str(body.get("sceneId", ""))[:100]

    room_id = str(uuid.uuid4())[:8]
    _collab_rooms[room_id] = {
        "roomId": room_id,
        "host": host_name,
        "members": [{"name": host_name, "joinedAt": datetime.datetime.now().isoformat(), "isHost": True}],
        "sceneId": scene_id,
        "createdAt": datetime.datetime.now().isoformat(),
        "sceneState": None,
    }
    _collab_connections[room_id] = []

    return {"success": True, "roomId": room_id, "host": host_name}


@app.get("/api/collab/{room_id}")
async def collab_room_info(room_id: str):
    """Get room info"""
    room = _collab_rooms.get(room_id)
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")
    return {"success": True, "room": room}


@app.websocket("/ws/collab/{room_id}")
async def collab_websocket(websocket: WebSocket, room_id: str):
    """WebSocket endpoint for real-time collaboration"""
    # Verify room exists before accepting connection
    room = _collab_rooms.get(room_id)
    if not room:
        await websocket.close(code=4004, reason="Room not found")
        return

    # Check auth if required
    if settings.REQUIRE_AUTH:
        auth_header = websocket.headers.get("authorization", "")
        token = auth_header[7:] if auth_header.startswith("Bearer ") else websocket.query_params.get("token", "")
        payload = _decode_jwt_payload(token) if token else None
        if not payload:
            await websocket.close(code=4001, reason="Authentication required")
            return

    await websocket.accept()

    _collab_connections.setdefault(room_id, [])
    _collab_connections[room_id].append(websocket)
    member_name = f"User_{uuid.uuid4().hex[:6]}"

    try:
        # Send initial state
        await websocket.send_json({
            "type": "room_joined",
            "roomId": room_id,
            "memberName": member_name,
            "members": room["members"],
            "sceneState": room.get("sceneState"),
        })

        # Notify others
        for ws in _collab_connections[room_id]:
            if ws != websocket:
                try:
                    await ws.send_json({"type": "member_joined", "name": member_name})
                except Exception:
                    pass

        # Add member
        room["members"].append({"name": member_name, "joinedAt": datetime.datetime.now().isoformat(), "isHost": False})

        # Message loop
        while True:
            data = await websocket.receive_json()
            msg_type = data.get("type", "")

            if msg_type == "set_name":
                old_name = member_name
                import re as _re_ws
                member_name = _re_ws.sub(r'<[^>]+>', '', str(data.get("name", member_name))[:50].strip()) or old_name
                for m in room["members"]:
                    if m["name"] == old_name:
                        m["name"] = member_name
                # Broadcast name change
                for ws in _collab_connections[room_id]:
                    if ws != websocket:
                        try:
                            await ws.send_json({"type": "name_changed", "oldName": old_name, "newName": member_name})
                        except Exception:
                            pass

            elif msg_type == "cursor_move":
                # Broadcast cursor position
                for ws in _collab_connections[room_id]:
                    if ws != websocket:
                        try:
                            await ws.send_json({
                                "type": "cursor_update",
                                "name": member_name,
                                "position": data.get("position"),
                                "camera": data.get("camera"),
                            })
                        except Exception:
                            pass

            elif msg_type == "scene_update":
                # User updated scene (transform, add, delete)
                room["sceneState"] = data.get("sceneState")
                for ws in _collab_connections[room_id]:
                    if ws != websocket:
                        try:
                            await ws.send_json({
                                "type": "scene_sync",
                                "sceneState": data.get("sceneState"),
                                "updatedBy": member_name,
                            })
                        except Exception:
                            pass

            elif msg_type == "chat_message":
                import re as _re_chat
                safe_text = _re_chat.sub(r'<[^>]+>', '', str(data.get("text", ""))[:2000].strip())
                for ws in _collab_connections[room_id]:
                    if ws != websocket:
                        try:
                            await ws.send_json({
                                "type": "chat_message",
                                "from": member_name,
                                "text": safe_text,
                                "timestamp": datetime.datetime.now().isoformat(),
                            })
                        except Exception:
                            pass

    except WebSocketDisconnect:
        pass
    except Exception:
        pass
    finally:
        # Cleanup
        if room_id in _collab_connections and websocket in _collab_connections[room_id]:
            _collab_connections[room_id].remove(websocket)

        if room_id in _collab_rooms:
            room["members"] = [m for m in room["members"] if m["name"] != member_name]
            # Notify remaining
            for ws in _collab_connections.get(room_id, []):
                try:
                    await ws.send_json({"type": "member_left", "name": member_name})
                except Exception:
                    pass

            # Cleanup empty rooms
            if not _collab_connections.get(room_id):
                _collab_rooms.pop(room_id, None)
                _collab_connections.pop(room_id, None)



if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=3001,
        reload=True,
        log_level="info"
    )
