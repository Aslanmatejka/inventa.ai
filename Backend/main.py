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

from fastapi import FastAPI, HTTPException, BackgroundTasks, Request, UploadFile, File, Form, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
import os
from pathlib import Path
import uuid
import time
import json
import asyncio
import hashlib
import datetime

# Import services
from services import (
    claude_service, 
    cadquery_service, 
    parametric_cad_service, 
    database_service,
    DB_IMPORT_OK,
    s3_service, 
    S3_AVAILABLE,
    glb_service,
    GLB_AVAILABLE,
    cad_import_service,
    CAD_SUPPORTED_FORMATS,
    pcb_design_service,
    pcb_search_components,
    pcb_get_component,
    pcb_list_categories,
    PCB_COMPONENTS,
)
from config import settings

print("\n" + "="*60)
print("🚀 BACKEND STARTING UP")
print("="*60)
print(f"Services loaded successfully:")
print(f"  - Claude Service: {claude_service is not None}")
print(f"  - CadQuery Service: {cadquery_service is not None}")
print(f"  - Parametric CAD Service: {parametric_cad_service is not None}")
print(f"  - S3 Available: {S3_AVAILABLE}")
print(f"  - GLB Available: {GLB_AVAILABLE}")

# Initialize Supabase database
DB_AVAILABLE = False
try:
    if not DB_IMPORT_OK:
        print(f"  - Supabase Database: ⚠️  'supabase' package not installed — storage disabled")
    elif settings.SUPABASE_URL and settings.SUPABASE_ANON_KEY:
        database_service.initialize(
            supabase_url=settings.SUPABASE_URL,
            supabase_key=settings.SUPABASE_ANON_KEY,
        )
        DB_AVAILABLE = True
        print(f"  - Supabase Database: ✅ Connected to {settings.SUPABASE_URL}")
    else:
        print(f"  - Supabase Database: ⚠️  Missing SUPABASE_URL or SUPABASE_ANON_KEY in .env — storage disabled")
except Exception as db_err:
    print(f"  - Supabase Database: ❌ Connection failed: {db_err}")
    print(f"    Check your Supabase credentials in .env")

print("="*60 + "\n")

# Import Celery tasks (optional - only if Celery is installed)
try:
    from tasks import generate_cad_async, rebuild_async
    CELERY_AVAILABLE = True
except ImportError:
    CELERY_AVAILABLE = False
    print("⚠️  Celery not available - using synchronous processing")

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

def _prompt_hash(prompt: str) -> str:
    """Generate a deterministic hash for a prompt (new designs only)."""
    return hashlib.sha256(prompt.strip().lower().encode()).hexdigest()[:16]

def _check_prompt_cache(prompt: str) -> dict | None:
    """Return cached result if the same prompt was built before."""
    h = _prompt_hash(prompt)
    cached = _prompt_cache.get(h)
    if not cached:
        return None
    # Verify files still exist
    stl_path = cached.get("stlFile", "")
    if stl_path:
        full_path = os.path.join(os.path.dirname(__file__), stl_path.lstrip("/"))
        if not os.path.exists(full_path):
            del _prompt_cache[h]
            return None
    return cached

def _store_prompt_cache(prompt: str, result: dict):
    """Cache a successful build result keyed by prompt hash."""
    h = _prompt_hash(prompt)
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
_cors_origins = [o.strip() for o in settings.CORS_ORIGINS.split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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

# ── Auth middleware — extract Supabase JWT user info ────────────────────
# Parses the Authorization header if present and attaches user info
# to request.state.user. When REQUIRE_AUTH=true in .env, write endpoints
# will reject unauthenticated requests with 401.
import base64

def _decode_jwt_payload(token: str) -> dict | None:
    """Decode a JWT payload without verification (Supabase RLS handles real checks)."""
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
    prompt: str
    previousDesign: Optional[Dict[str, Any]] = None
    projectId: Optional[str] = None
    model: Optional[str] = None
    mode: Optional[str] = "agent"  # 'agent' | 'ask' | 'plan'

class AskRequest(BaseModel):
    prompt: str
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

# ── Available AI Models ───────────────────────────────────────────────
AVAILABLE_MODELS = [
    # ── Anthropic Claude ──
    {
        "id": "claude-opus-4-6",
        "name": "Claude Opus 4.6",
        "provider": "Anthropic",
        "description": "Latest & most powerful — complex multi-part designs",
        "tier": "flagship",
    },
    {
        "id": "claude-opus-4-20250514",
        "name": "Claude Opus 4",
        "provider": "Anthropic",
        "description": "Proven flagship — reliable for any design task",
        "tier": "flagship",
    },
    {
        "id": "claude-sonnet-4-6",
        "name": "Claude Sonnet 4.6",
        "provider": "Anthropic",
        "description": "Fast & highly capable — great for iterative design",
        "tier": "standard",
    },
    {
        "id": "claude-sonnet-4-20250514",
        "name": "Claude Sonnet 4",
        "provider": "Anthropic",
        "description": "Balanced speed and quality",
        "tier": "standard",
    },
    # ── OpenAI GPT (2026) ──
    {
        "id": "gpt-4.1-2025-04-14",
        "name": "GPT-4.1",
        "provider": "OpenAI",
        "description": "Flagship GPT — strong coding & long context",
        "tier": "flagship",
    },
    {
        "id": "gpt-4.1-mini-2025-04-14",
        "name": "GPT-4.1 Mini",
        "provider": "OpenAI",
        "description": "Fast & affordable with great code output",
        "tier": "standard",
    },
    {
        "id": "gpt-4.1-nano-2025-04-14",
        "name": "GPT-4.1 Nano",
        "provider": "OpenAI",
        "description": "Ultra-fast — quick prototyping and simple shapes",
        "tier": "fast",
    },
]

@app.get("/api/models")
async def list_models():
    """Return available AI models, filtered by which API keys are configured"""
    available = []
    for m in AVAILABLE_MODELS:
        if m["provider"] == "Anthropic" and settings.ANTHROPIC_API_KEY:
            available.append(m)
        elif m["provider"] == "OpenAI" and settings.OPENAI_API_KEY:
            available.append(m)
    return {
        "models": available,
        "default": settings.AI_MODEL_NAME,
    }


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
            active_model = body.model or settings.AI_MODEL_NAME

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

            answer = claude_service._stream_completion(
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
            active_model = body.model or settings.AI_MODEL_NAME

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

            answer = claude_service._stream_completion(
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
                import re
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
async def chat_with_engineer(request: ChatRequest):
    """
    Conversational interface for refining CAD designs
    Claude guides the user through design parameters
    """
    try:
        result = await claude_service.chat_about_design(
            message=request.message,
            conversation_history=request.conversationHistory,
            current_design=request.currentDesign
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
async def build_product(request: BuildRequest):
    """
    Single-shot CAD generation from natural language prompt
    Phase 2: Claude -> Parametric Code Schema -> CadQuery Execution -> STEP/STL
    """
    print(f"\n{'='*60}")
    print(f"🔨 BUILD REQUEST RECEIVED")
    print(f"{'='*60}")
    print(f"Prompt: {request.prompt}")
    print(f"Has previous design: {request.previousDesign is not None}")
    print(f"{'='*60}\n")
    
    last_error = None
    ai_response = None
    
    try:
        # Step 1: Claude generates parametric code schema
        print("📡 Step 1: Calling Claude AI for design generation...")
        ai_response = await claude_service.generate_design_from_prompt(
            prompt=request.prompt,
            previous_design=request.previousDesign
        )
        print(f"✅ Claude AI response received")
        print(f"Response keys: {list(ai_response.keys())}")
        
        # Step 2: Execute parametric CadQuery code (self-healing with retry cap)
        attempt = 0
        while attempt < MAX_SELF_HEALING_ATTEMPTS:
            attempt += 1
            try:
                print(f"\n🔧 Step 2 (attempt {attempt}): Generating CAD model with CadQuery...")
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
                    original_prompt=request.prompt,
                    attempt=attempt,
                    max_retries=MAX_SELF_HEALING_ATTEMPTS
                )
                print(f"✅ Claude fix response received")
        
    except Exception as e:
        import traceback
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
                import datetime
                f.write(f"\n{'='*60}\n")
                f.write(f"[{datetime.datetime.now()}] /api/build error\n")
                f.write(f"Prompt: {request.prompt}\n")
                f.write(f"Error: {str(e)}\n")
                f.write(error_details)
                f.write(f"{'='*60}\n")
        except Exception as log_err:
            print(f"⚠️ Failed to write error log: {log_err}")
        
        raise HTTPException(status_code=500, detail=str(e))

# ── Streaming build endpoint (SSE) ──────────────────────────────────────
MAX_SELF_HEALING_ATTEMPTS = 15  # hard cap on infinite self-healing loop

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
    async def event_generator():
        def sse(data: dict) -> str:
            return f"data: {json.dumps(data)}\n\n"

        last_error = None
        ai_response = None
        attempt = 0
        is_modification = body.previousDesign is not None and bool(body.previousDesign)
        has_previous_code = is_modification and bool(body.previousDesign.get("code", ""))

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
                cached = _check_prompt_cache(body.prompt)
                if cached:
                    print(f"⚡ Prompt cache HIT — skipping AI")
                    yield sse({"step": 1, "message": "Cache hit — reusing previous build", "status": "done"})
                    yield sse({"step": 2, "message": "Skipped (cached)", "status": "done"})
                    yield sse({"step": 3, "message": "Skipped (cached)", "status": "done"})
                    yield sse({"step": 4, "message": "Skipped (cached)", "status": "done"})
                    yield sse({"step": 5, "message": "Skipped (cached)", "status": "done"})
                    yield sse({"step": 6, "message": "Build complete! (cached)", "status": "complete", "result": cached})
                    return

            # Step 1: Searching product library
            yield sse({"step": 1, "message": "Searching product library for real-world dimensions and reference specs...", "status": "active", "detail": "Checking our database of 98+ product templates for matching measurements."})
            await asyncio.sleep(0.05)  # allow flush

            # Detect complexity for adaptive behavior
            complexity = claude_service._detect_complexity(body.prompt)
            complexity_labels = {"high": "Professional", "medium": "Detailed", "standard": "Standard"}
            complexity_label = complexity_labels.get(complexity, "Standard")

            # Step 2: Analyzing prompt with AI
            yield sse({"step": 1, "message": f"Product library checked — {complexity_label} complexity detected", "status": "done"})
            if is_modification:
                step2_msg = "Modifying your design — reading previous code and applying your changes..."
                step2_detail = "Claude is editing the existing CadQuery code to add/change only what you asked for."
            else:
                step2_msg = "Designing your product with Claude AI..."
                step2_detail = "Claude is analyzing your description, selecting dimensions, and writing parametric CadQuery code."
            yield sse({"step": 2, "message": step2_msg, "status": "active", "detail": step2_detail})

            ai_response = await claude_service.generate_design_from_prompt(
                prompt=body.prompt,
                previous_design=body.previousDesign,
                model_override=body.model
            )

            yield sse({"step": 2, "message": "AI design complete", "status": "done"})

            # ── PCB Processing (if AI returned pcb_spec) ──
            pcb_result_data = None
            pcb_spec = ai_response.get("pcb_spec")
            if pcb_spec:
                yield sse({"step": 2.5, "message": "🔌 Generating PCB layout and KiCad files...", "status": "active",
                           "detail": "Creating PCB 3D model, KiCad .kicad_pcb file, and enclosure integration specs."})
                try:
                    pcb_build_id = f"{ai_response.get('buildId', str(uuid.uuid4()))}_pcb"
                    pcb_result_data = await pcb_design_service.generate_pcb_from_spec(
                        pcb_spec, build_id=pcb_build_id
                    )
                    yield sse({"step": 2.5, "message": f"PCB generated — {len(pcb_spec.get('components', []))} components",
                               "status": "done", "pcbResult": pcb_result_data})
                except Exception as pcb_err:
                    print(f"⚠️ PCB generation failed: {pcb_err}")
                    yield sse({"step": 2.5, "message": f"PCB generation warning: {str(pcb_err)[:100]}",
                               "status": "info", "detail": "Continuing with enclosure-only build."})

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
                
                if not analysis["is_complete"]:
                    missing_summary = ", ".join(analysis["missing_features"][:4])
                    yield sse({"step": 3, "message": f"Found {len(analysis['missing_features'])} missing features — enhancing design...", "status": "active", "detail": f"Missing: {missing_summary}. Sending back to AI for targeted enhancement."})
                    
                    for mf in analysis["missing_features"]:
                        print(f"     • {mf}")
                    
                    # FIRST enhancement pass
                    ai_response = await claude_service.enhance_incomplete_design(ai_response, body.prompt, analysis)
                    
                    # Re-check after first enhancement
                    enhanced_code = ai_response.get("code", "")
                    if enhanced_code:
                        re_analysis = claude_service.analyze_code_completeness(enhanced_code, body.prompt)
                        code_lines = enhanced_code.count("\n") + 1
                        param_count = len(ai_response.get("parameters", []))
                        print(f"\n📊 Post-enhancement #1: features={re_analysis['total_features']}, complete={'✅' if re_analysis['is_complete'] else '⚠️'}")
                        
                        # SECOND enhancement pass if still incomplete (auto-healing for quality)
                        if not re_analysis["is_complete"] and len(re_analysis["missing_features"]) > 0:
                            remaining = ", ".join(re_analysis["missing_features"][:3])
                            yield sse({"step": 3, "message": f"Still missing {len(re_analysis['missing_features'])} features — second pass...", "status": "active", "detail": f"Remaining: {remaining}. Running targeted fix."})
                            print(f"\n🔁 SECOND ENHANCEMENT PASS — still missing:")
                            for mf in re_analysis["missing_features"]:
                                print(f"     • {mf}")
                            
                            ai_response = await claude_service.enhance_incomplete_design(ai_response, body.prompt, re_analysis)
                            final_code = ai_response.get("code", "")
                            if final_code:
                                final_analysis = claude_service.analyze_code_completeness(final_code, body.prompt)
                                code_lines = final_code.count("\n") + 1
                                param_count = len(ai_response.get("parameters", []))
                                print(f"\n📊 Post-enhancement #2: features={final_analysis['total_features']}, complete={'✅' if final_analysis['is_complete'] else '⚠️'}")
                    
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
            while attempt < MAX_SELF_HEALING_ATTEMPTS:
                attempt += 1

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
                                proj = database_service.create_project(name=project_name)
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
                                "pcb_spec": ai_response.get("pcb_spec"),
                            },
                            "projectId": saved_project_id,
                            "healingAttempts": attempt - 1 if attempt > 1 else 0,
                            "pcbResult": pcb_result_data,
                            "isPCB": pcb_result_data is not None,
                            "success": True
                        }
                    })

                    # Store in prompt cache (new designs only)
                    if not is_modification:
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
                        })

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
            import traceback
            error_details = traceback.format_exc()
            print(f"\n{'='*60}\n❌ ERROR in /api/build/stream\n{'='*60}")
            print(error_details)

            try:
                log_path = Path(EXPORTS_DIR) / "error_log.txt"
                with open(log_path, "a", encoding="utf-8") as f:
                    import datetime
                    f.write(f"\n{'='*60}\n[{datetime.datetime.now()}] /api/build/stream error\n")
                    f.write(f"Prompt: {body.prompt}\nError: {str(e)}\n{error_details}\n{'='*60}\n")
            except Exception as log_err:
                print(f"⚠️ Failed to write error log: {log_err}")

            yield sse({"step": -1, "message": str(e), "status": "fatal"})

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
    )

@app.post("/api/rebuild")
async def rebuild_with_parameters(request: RebuildRequest):
    """
    Phase 4: Re-execute existing parametric script with new parameter values
    NO AI CALL - just re-runs Python code with updated parameters
    """
    try:
        result = await parametric_cad_service.rebuild_with_parameters(
            build_id=request.buildId,
            updated_parameters=request.parameters
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
async def upload_to_s3(request: Dict[str, str]):
    """
    Phase 4: Upload build to S3 for sharing and caching
    """
    if not S3_AVAILABLE:
        raise HTTPException(
            status_code=501,
            detail="S3 not configured. Set AWS credentials in .env"
        )
    
    try:
        build_id = request.get("buildId")
        if not build_id:
            raise HTTPException(status_code=400, detail="buildId required")
        
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
async def convert_to_glb(request: Dict[str, Any]):
    """
    Phase 4: Convert STL/STEP to GLB format for optimized web rendering
    """
    if not GLB_AVAILABLE:
        raise HTTPException(
            status_code=501,
            detail="GLB conversion not available. Install trimesh: pip install trimesh"
        )
    
    try:
        build_id = request.get("buildId")
        source_format = request.get("sourceFormat", "stl")  # "stl" or "step"
        optimize = request.get("optimize", True)
        
        if not build_id:
            raise HTTPException(status_code=400, detail="buildId required")
        
        if source_format == "stl":
            glb_url = await glb_service.convert_stl_to_glb(build_id, optimize=optimize)
        elif source_format == "step":
            quality = request.get("quality", "medium")
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
async def get_mesh_stats(build_id: str, file_type: str = "stl"):
    """
    Phase 4: Get mesh statistics (vertices, faces, volume, etc.)
    """
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
async def create_scene(body: dict = None):
    """Create a new scene for managing multiple products"""
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
async def get_scene(scene_id: str):
    """Get scene details with all products"""
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
async def add_product_to_scene(scene_id: str, product: dict):
    """Add a product to the scene"""
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
async def update_product_transform(instance_id: str, transform: dict):
    """Update a product's position/rotation/scale in the scene"""
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
async def duplicate_product(instance_id: str, options: dict = None):
    """Duplicate a product in the scene with an offset"""
    original = _products.get(instance_id)
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
async def delete_product_from_scene(instance_id: str):
    """Remove a product from the scene"""
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
async def assemble_products(scene_id: str, assembly: dict):
    """Group products into an assembly"""
    assembly_id = str(uuid.uuid4())
    return {
        "success": True,
        "assembly": {
            "assemblyId": assembly_id,
            "name": assembly.get("name", "Assembly"),
            "parentInstanceId": assembly.get("parentInstanceId"),
            "childInstanceIds": assembly.get("childInstanceIds", []),
            "sceneId": scene_id
        }
    }

@app.delete("/api/scene/assembly/{assembly_id}")
async def disassemble_products(assembly_id: str):
    """Break an assembly back into individual products"""
    return {"success": True, "disassembled": assembly_id}


# ── Assembly STEP Export (F34) ───────────────────────────────────────
@app.post("/api/scene/export-assembly")
async def export_assembly_step(body: dict):
    """
    Merge multiple scene products into a single assembly STEP file.
    Expects { "buildIds": ["id1", "id2", ...], "name": "My Assembly" }
    Each buildId must have a .step file in exports/cad/.
    """
    import cadquery as cq

    build_ids = body.get("buildIds", [])
    assembly_name = body.get("name", "Assembly")

    if not build_ids:
        raise HTTPException(status_code=400, detail="No buildIds provided")

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
async def set_material(build_id: str, body: dict):
    """
    Assign material metadata to a build.
    Expects { "materialId": "aluminum", "color": "#C0C0C0", "finish": "brushed", "notes": "..." }
    """
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
    ("pro", "monthly"): settings.STRIPE_PRO_PRICE_MONTHLY if hasattr(settings, 'STRIPE_PRO_PRICE_MONTHLY') else None,
    ("pro", "yearly"): settings.STRIPE_PRO_PRICE_YEARLY if hasattr(settings, 'STRIPE_PRO_PRICE_YEARLY') else None,
    ("enterprise", "monthly"): settings.STRIPE_ENT_PRICE_MONTHLY if hasattr(settings, 'STRIPE_ENT_PRICE_MONTHLY') else None,
    ("enterprise", "yearly"): settings.STRIPE_ENT_PRICE_YEARLY if hasattr(settings, 'STRIPE_ENT_PRICE_YEARLY') else None,
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
        if settings.STRIPE_WEBHOOK_SECRET:
            event = _stripe_mod.Webhook.construct_event(payload, sig_header, settings.STRIPE_WEBHOOK_SECRET)
        else:
            event = _stripe_mod.Event.construct_from(json.loads(payload), _stripe_mod.api_key)
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
async def generate_bom(body: dict):
    """
    Generate a Bill of Materials from scene products.
    Expects { "items": [{ "buildId": "...", "name": "...", "quantity": 1 }] }
    Returns structured BOM data (JSON + CSV download).
    """
    items = body.get("items", [])
    if not items:
        raise HTTPException(status_code=400, detail="No items provided")
    
    bom_rows = []
    for idx, item in enumerate(items, 1):
        bid = item.get("buildId", "")
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
async def export_2d_drawing(body: dict):
    """
    Generate 2D engineering drawing projections from a STEP model.
    Expects { "buildId": "...", "views": ["front", "top", "right", "iso"] }
    Returns SVG drawing file.
    """
    import cadquery as cq

    build_id = body.get("buildId", "")
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
                import re
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
async def check_cache(prompt: str):
    """Check if a prompt has a cached build result"""
    cached = _check_prompt_cache(prompt)
    if cached:
        return {"success": True, "cached": True, "result": cached}
    return {"success": True, "cached": False}



# ── File Upload & NLP Edit Endpoints ─────────────────────────────────────

@app.get("/api/upload/formats")
async def get_supported_formats():
    """Return list of supported upload formats"""
    return {"success": True, **cad_import_service.get_supported_formats()}

@app.post("/api/upload")
async def upload_cad_file(file: UploadFile = File(...)):
    """
    Upload a CAD file for visualization and NLP editing.
    Supports STEP, STL, IGES, DXF, OBJ, 3MF, PLY, BRep, GLB, glTF.
    """
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
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Import failed: {str(e)}")


class NLPEditRequest(BaseModel):
    buildId: str
    prompt: str
    importCode: Optional[str] = None
    previousDesign: Optional[Dict[str, Any]] = None

@app.post("/api/upload/edit")
async def nlp_edit_uploaded_file(request: NLPEditRequest):
    """
    Apply a natural language edit to an uploaded CAD file.
    Sends the import code + user prompt to Claude for code generation,
    then executes the modified CadQuery code.
    """
    # Build "previous design" with the import code as the starting point
    import_code = request.importCode or ""
    if not import_code and request.previousDesign:
        import_code = request.previousDesign.get("code", "")

    if not import_code:
        raise HTTPException(
            status_code=400,
            detail="No import code or previous design provided for editing."
        )

    # Send to Claude as a modification of the import code
    previous_design = {
        "code": import_code,
        "parameters": request.previousDesign.get("parameters", []) if request.previousDesign else [],
        "explanation": request.previousDesign.get("explanation", {}) if request.previousDesign else {},
    }

    ai_response = None
    try:
        ai_response = await claude_service.generate_design_from_prompt(
            prompt=request.prompt,
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
                original_prompt=request.prompt,
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
async def list_projects():
    """List all saved projects"""
    if not DB_AVAILABLE:
        return {"success": True, "projects": []}
    try:
        projects = database_service.list_projects()
        return {"success": True, "projects": projects}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/projects")
async def create_project(request: ProjectCreateRequest):
    """Create a new project"""
    if not DB_AVAILABLE:
        raise HTTPException(status_code=503, detail="Database not available")
    try:
        project = database_service.create_project(name=request.name, description=request.description)
        return {"success": True, "project": project}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/projects/{project_id}")
async def get_project(project_id: str):
    """Get project with all builds and chat messages"""
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
async def update_project(project_id: str, request: ProjectUpdateRequest):
    """Update project name or description"""
    if not DB_AVAILABLE:
        raise HTTPException(status_code=503, detail="Database not available")
    try:
        project = database_service.update_project(project_id, name=request.name, description=request.description)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        return {"success": True, "project": project}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/projects/{project_id}")
async def delete_project(project_id: str):
    """Delete a project and all its builds/messages"""
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
async def save_message(request: SaveMessageRequest):
    """Save a chat message to a project"""
    if not DB_AVAILABLE:
        raise HTTPException(status_code=503, detail="Database not available")
    try:
        msg = database_service.save_chat_message(
            project_id=request.projectId,
            role=request.role,
            content=request.content,
            build_result=request.buildResult,
            status=request.status,
        )
        return {"success": True, "message": msg}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/history")
async def get_build_history():
    """Get recent builds across all projects"""
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
    """Serve generated CAD files (STL, STEP)"""
    safe_name = Path(filename).name
    file_path = (CAD_DIR / safe_name).resolve()
    if not str(file_path).startswith(str(CAD_DIR.resolve())):
        raise HTTPException(status_code=400, detail="Invalid filename")
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(file_path)

# Serve generated PCB files (KiCad .kicad_pcb)
@app.get("/exports/pcb/{filename}")
async def serve_pcb_file(filename: str):
    """Serve generated PCB files"""
    safe_name = Path(filename).name
    file_path = (Path(settings.EXPORTS_DIR) / "pcb" / safe_name).resolve()
    if not str(file_path).startswith(str((Path(settings.EXPORTS_DIR) / "pcb").resolve())):
        raise HTTPException(status_code=400, detail="Invalid filename")
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="PCB file not found")
    return FileResponse(file_path, media_type="application/octet-stream", filename=safe_name)


# ═══════════════════════════════════════════════════════════════════════════
# PCB DESIGN ENDPOINTS
# ═══════════════════════════════════════════════════════════════════════════

class PCBBuildRequest(BaseModel):
    prompt: str
    buildId: Optional[str] = None
    previousDesign: Optional[Dict[str, Any]] = None

class PCBEnclosureRequest(BaseModel):
    pcbResult: Dict[str, Any]
    style: Optional[str] = "rounded"
    wallThickness: Optional[float] = 2.0
    clearance: Optional[float] = 1.0

@app.get("/api/pcb/components")
async def pcb_component_search(q: str = "", category: str = ""):
    """Search PCB component library"""
    if category:
        from services.pcb_component_library import get_components_by_category
        comps = get_components_by_category(category)
        return {"success": True, "components": comps}
    if q:
        comps = pcb_search_components(q)
        return {"success": True, "components": comps}
    # Return all components grouped by category
    from services.pcb_component_library import COMPONENTS
    return {"success": True, "components": COMPONENTS}

@app.get("/api/pcb/components/{component_id}")
async def pcb_component_detail(component_id: str):
    """Get details for a specific PCB component"""
    comp = pcb_get_component(component_id)
    if not comp:
        raise HTTPException(status_code=404, detail=f"Component '{component_id}' not found")
    return {"success": True, "component": comp}

@app.get("/api/pcb/categories")
async def pcb_categories():
    """List all PCB component categories"""
    cats = pcb_list_categories()
    return {"success": True, "categories": cats}

@app.post("/api/pcb/build/stream")
async def pcb_build_stream(request: Request):
    """
    Build a PCB + enclosure from natural language (SSE streaming).
    Flow:
      1. Claude generates pcb_spec + enclosure CadQuery code
      2. PCB service creates KiCad file + 3D model
      3. Enclosure code is executed by parametric_cad_service
      4. Both files are returned
    """
    try:
        body = await request.json()
        prompt = body.get("prompt", "")
        build_id = body.get("buildId", str(uuid.uuid4()))
        previous_design = body.get("previousDesign")

        if not prompt:
            raise HTTPException(status_code=400, detail="Prompt is required")

        async def event_stream():
            try:
                # Step 1: AI Design
                yield f"data: {json.dumps({'step': 1, 'status': 'designing', 'message': 'Designing PCB layout and enclosure...'})}\n\n"

                design_json = await claude_service.generate_design_from_prompt(
                    prompt, previous_design
                )

                yield f"data: {json.dumps({'step': 2, 'status': 'ai_complete', 'message': 'AI design complete'})}\n\n"

                pcb_result = None
                pcb_spec = design_json.get("pcb_spec")

                # Step 2: Generate PCB if spec provided
                if pcb_spec:
                    yield f"data: {json.dumps({'step': 3, 'status': 'pcb_generating', 'message': 'Generating PCB layout and KiCad files...'})}\n\n"

                    pcb_result = await pcb_design_service.generate_pcb_from_spec(
                        pcb_spec, build_id=f"{build_id}_pcb"
                    )

                    yield f"data: {json.dumps({'step': 3, 'status': 'pcb_complete', 'message': 'PCB generated', 'pcbResult': pcb_result})}\n\n"

                # Step 3: Execute enclosure CadQuery code
                code = design_json.get("code", "")
                if code:
                    yield f"data: {json.dumps({'step': 4, 'status': 'building', 'message': 'Building enclosure 3D model...'})}\n\n"

                    cad_result = await parametric_cad_service.generate_parametric_cad(
                        design_json, build_id=build_id
                    )

                    if cad_result.get("success"):
                        stl_url = f"/exports/cad/{build_id}.stl"
                        step_url = f"/exports/cad/{build_id}.step"

                        final_result = {
                            "step": 5,
                            "status": "complete",
                            "message": "PCB + Enclosure build complete!",
                            "design": design_json,
                            "stlFile": stl_url,
                            "stepFile": step_url,
                            "buildId": build_id,
                            "pcbResult": pcb_result,
                            "isPCB": True,
                        }
                        yield f"data: {json.dumps(final_result)}\n\n"
                    else:
                        # Self-healing loop (like main build stream)
                        error_msg = cad_result.get("error", "Unknown CadQuery error")
                        yield f"data: {json.dumps({'step': 4, 'status': 'fixing', 'message': f'Fixing enclosure: {error_msg[:100]}'})}\n\n"

                        attempt = 1
                        while True:
                            try:
                                fixed_json = await claude_service.fix_code_with_error(
                                    code, error_msg, prompt, attempt, 999
                                )
                                code = fixed_json.get("code", code)
                                design_json["code"] = code

                                cad_result = await parametric_cad_service.generate_parametric_cad(
                                    fixed_json, build_id=build_id
                                )

                                if cad_result.get("success"):
                                    stl_url = f"/exports/cad/{build_id}.stl"
                                    step_url = f"/exports/cad/{build_id}.step"
                                    final_result = {
                                        "step": 5,
                                        "status": "complete",
                                        "message": f"Build complete (fixed on attempt {attempt})",
                                        "design": design_json,
                                        "stlFile": stl_url,
                                        "stepFile": step_url,
                                        "buildId": build_id,
                                        "pcbResult": pcb_result,
                                        "isPCB": True,
                                    }
                                    yield f"data: {json.dumps(final_result)}\n\n"
                                    break

                                error_msg = cad_result.get("error", "Unknown error")
                                attempt += 1
                                yield f"data: {json.dumps({'step': 4, 'status': 'fixing', 'message': f'Fix attempt {attempt}: {error_msg[:80]}'})}\n\n"

                            except Exception as fix_err:
                                yield f"data: {json.dumps({'step': 5, 'status': 'error', 'message': str(fix_err)})}\n\n"
                                break
                elif pcb_result:
                    # PCB only (no enclosure code generated)
                    final_result = {
                        "step": 5,
                        "status": "complete",
                        "message": "PCB design complete!",
                        "design": design_json,
                        "stlFile": pcb_result.get("stlFile", ""),
                        "stepFile": pcb_result.get("stepFile", ""),
                        "buildId": build_id,
                        "pcbResult": pcb_result,
                        "isPCB": True,
                    }
                    yield f"data: {json.dumps(final_result)}\n\n"
                else:
                    yield f"data: {json.dumps({'step': 5, 'status': 'error', 'message': 'No code or PCB spec returned by AI'})}\n\n"

            except Exception as e:
                yield f"data: {json.dumps({'step': 5, 'status': 'error', 'message': str(e)})}\n\n"

        return StreamingResponse(event_stream(), media_type="text/event-stream")

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/pcb/enclosure")
async def pcb_generate_enclosure(request: PCBEnclosureRequest):
    """Generate an enclosure for an existing PCB design"""
    try:
        enclosure = pcb_design_service.generate_enclosure_for_pcb(
            pcb_result=request.pcbResult,
            enclosure_style=request.style,
            wall_thickness=request.wallThickness,
            clearance=request.clearance,
        )
        return {"success": True, "enclosure": enclosure}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


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
async def version_save(request: VersionSaveRequest):
    """Save a version snapshot for a build"""
    try:
        build_id = request.buildId

        # Try to read the current parametric script for code
        code = request.code or ""
        if not code:
            script_path = Path(CAD_DIR) / f"{build_id}_parametric.py"
            if script_path.exists():
                code = script_path.read_text(encoding="utf-8", errors="replace")

        # Use database if available
        if DB_AVAILABLE and database_service.is_available:
            existing = database_service.list_versions(build_id)
            label = request.label or f"v{len(existing) + 1}"
            version = database_service.save_version(
                build_id=build_id,
                label=label,
                code=code,
                parameters=request.parameters,
                explanation=request.design,
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
                "label": request.label or f"v{len(_version_history[build_id]) + 1}",
                "design": request.design,
                "code": code,
                "parameters": request.parameters,
            }

            _version_history[build_id].append(snapshot)

            if len(_version_history[build_id]) > 50:
                _version_history[build_id] = _version_history[build_id][-50:]

            return {"success": True, "versionId": version_id, "totalVersions": len(_version_history[build_id])}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/versions/{build_id}")
async def version_list(build_id: str):
    """List all saved versions for a build"""
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
async def version_restore(request: VersionRestoreRequest):
    """Restore a previous version — re-execute its code to regenerate files"""
    try:
        target = None
        if DB_AVAILABLE and database_service.is_available:
            target = database_service.get_version(request.versionId)
            if target:
                # Normalize keys to match in-memory format
                target = {
                    "versionId": target["id"],
                    "code": target.get("code", ""),
                    "parameters": target.get("parameters"),
                    "design": {"explanation": target.get("explanation", {})} if target.get("explanation") else None,
                }
        else:
            versions = _version_history.get(request.buildId, [])
            target = next((v for v in versions if v["versionId"] == request.versionId), None)

        if not target:
            raise HTTPException(status_code=404, detail="Version not found")

        code = target.get("code", "")
        if not code:
            raise HTTPException(status_code=400, detail="No code saved in this version")

        # Re-execute the code to regenerate the model
        new_build_id = f"{request.buildId}_r{request.versionId}"
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
            "restoredFrom": request.versionId,
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/versions/{build_id}/compare/{version_a}/{version_b}")
async def version_compare(build_id: str, version_a: str, version_b: str):
    """Compare two versions — show parameter and code differences"""
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
async def slicer_estimate(request: SliceRequest):
    """Estimate print time, material usage, and cost for a build"""
    try:
        # Get model dimensions from STEP file
        step_path = Path(CAD_DIR) / f"{request.buildId}.step"
        stl_path = Path(CAD_DIR) / f"{request.buildId}.stl"

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
        preset = SLICER_PRESETS.get(request.preset, SLICER_PRESETS["normal"]).copy()
        if request.layerHeight is not None:
            preset["layer_height"] = request.layerHeight
        if request.infill is not None:
            preset["infill"] = request.infill
        if request.shells is not None:
            preset["shells"] = request.shells
        if request.speed is not None:
            preset["speed"] = request.speed
        if request.supports is not None:
            preset["supports"] = request.supports

        filament = FILAMENT_DB.get(request.filament, FILAMENT_DB["pla"])

        # Estimate calculations
        layer_height_mm = preset["layer_height"]
        infill_pct = preset["infill"] / 100.0
        shells = preset["shells"]
        speed = preset["speed"]
        nozzle = request.nozzleDiameter

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
        fits_bed = (bbox["x"] <= request.bedSizeX and
                    bbox["y"] <= request.bedSizeY and
                    bbox["z"] <= request.bedSizeZ)

        # Need supports heuristic
        needs_supports = False
        if bbox["z"] > bbox["x"] * 2 or bbox["z"] > bbox["y"] * 2:
            needs_supports = True

        return {
            "success": True,
            "buildId": request.buildId,
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
    body = await request.json()
    host_name = body.get("hostName", "Anonymous")
    scene_id = body.get("sceneId", "")

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
    await websocket.accept()

    room = _collab_rooms.get(room_id)
    if not room:
        await websocket.send_json({"type": "error", "message": "Room not found"})
        await websocket.close()
        return

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
                member_name = data.get("name", member_name)
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
                for ws in _collab_connections[room_id]:
                    if ws != websocket:
                        try:
                            await ws.send_json({
                                "type": "chat_message",
                                "from": member_name,
                                "text": data.get("text", ""),
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


# ═══════════════════════════════════════════════════════════════
# F41: PCB Trace Routing — Manhattan auto-routing and visualization
# ═══════════════════════════════════════════════════════════════

class TraceRouteRequest(BaseModel):
    boardWidth: float = 100
    boardHeight: float = 80
    components: list = []       # [{ id, x, y, width, height, pads: [{ id, x, y, net }] }]
    nets: Optional[list] = None # [{ name, pads: [componentId.padId, ...] }]
    traceWidth: Optional[float] = 0.25
    clearance: Optional[float] = 0.2
    gridSize: Optional[float] = 0.5


@app.post("/api/pcb/route")
async def pcb_route_traces(request: TraceRouteRequest):
    """Auto-route copper traces between PCB component pads using Manhattan routing"""
    try:
        board_w = request.boardWidth
        board_h = request.boardHeight
        trace_width = request.traceWidth or 0.25
        clearance = request.clearance or 0.2
        grid = request.gridSize or 0.5

        components = request.components
        nets = request.nets or []

        # Build pad lookup: "compId.padId" -> absolute (x, y)
        pad_positions = {}
        for comp in components:
            cx, cy = comp.get("x", 0), comp.get("y", 0)
            for pad in comp.get("pads", []):
                key = f"{comp['id']}.{pad['id']}"
                pad_positions[key] = (cx + pad.get("x", 0), cy + pad.get("y", 0))

        # If nets not provided, try to infer from pad 'net' fields
        if not nets:
            net_map = {}
            for comp in components:
                for pad in comp.get("pads", []):
                    net_name = pad.get("net")
                    if net_name:
                        key = f"{comp['id']}.{pad['id']}"
                        net_map.setdefault(net_name, []).append(key)
            nets = [{"name": n, "pads": pads} for n, pads in net_map.items()]

        # Manhattan routing with simple obstacle avoidance
        all_traces = []
        occupied_segments = []

        for net in nets:
            net_name = net["name"]
            pad_keys = net.get("pads", [])
            if len(pad_keys) < 2:
                continue

            # Connect pads in sequence (star from first pad)
            for i in range(1, len(pad_keys)):
                start_key = pad_keys[0]
                end_key = pad_keys[i]

                start = pad_positions.get(start_key)
                end = pad_positions.get(end_key)
                if not start or not end:
                    continue

                # Manhattan route: go horizontal first, then vertical (L-shaped)
                sx, sy = start
                ex, ey = end

                # Snap to grid
                sx = round(sx / grid) * grid
                sy = round(sy / grid) * grid
                ex = round(ex / grid) * grid
                ey = round(ey / grid) * grid

                # Simple L-route with mid-point
                mid_x = ex
                mid_y = sy

                # Check if direct L-route collides with components
                # Try alternate route: vertical first, then horizontal
                route_a = [
                    {"x": sx, "y": sy},
                    {"x": mid_x, "y": mid_y},
                    {"x": ex, "y": ey},
                ]

                # Alternative: horizontal then vertical with offset
                alt_mid_x = sx
                alt_mid_y = ey
                route_b = [
                    {"x": sx, "y": sy},
                    {"x": alt_mid_x, "y": alt_mid_y},
                    {"x": ex, "y": ey},
                ]

                # Pick route that doesn't overlap existing traces (simplified)
                route = route_a
                seg_key_a = f"{sx},{sy}-{mid_x},{mid_y}"
                if seg_key_a in occupied_segments:
                    route = route_b

                # Remove redundant points (collinear)
                clean_route = [route[0]]
                for j in range(1, len(route)):
                    if route[j]["x"] != clean_route[-1]["x"] or route[j]["y"] != clean_route[-1]["y"]:
                        clean_route.append(route[j])

                # Record segments
                for j in range(len(clean_route) - 1):
                    seg = f"{clean_route[j]['x']},{clean_route[j]['y']}-{clean_route[j+1]['x']},{clean_route[j+1]['y']}"
                    occupied_segments.append(seg)

                all_traces.append({
                    "net": net_name,
                    "fromPad": start_key,
                    "toPad": end_key,
                    "points": clean_route,
                    "width": trace_width,
                    "layer": "F.Cu",
                })

        # Generate SVG representation
        svg_width = board_w * 4
        svg_height = board_h * 4
        scale = 4

        svg_parts = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {svg_width} {svg_height}" width="{svg_width}" height="{svg_height}">']
        svg_parts.append(f'<rect width="{svg_width}" height="{svg_height}" fill="#1a5c1a" rx="4"/>')

        # Draw traces
        trace_colors = ["#ff4444", "#4444ff", "#ffaa00", "#44ff44", "#ff44ff", "#44ffff", "#ffff44", "#ff8844"]
        for idx, trace in enumerate(all_traces):
            color = trace_colors[idx % len(trace_colors)]
            points_str = " ".join(f"{p['x']*scale},{p['y']*scale}" for p in trace["points"])
            svg_parts.append(f'<polyline points="{points_str}" stroke="{color}" stroke-width="{trace_width*scale}" fill="none" stroke-linecap="round" stroke-linejoin="round" opacity="0.9"/>')

        # Draw component outlines
        for comp in components:
            cx = comp.get("x", 0) * scale
            cy = comp.get("y", 0) * scale
            cw = comp.get("width", 10) * scale
            ch = comp.get("height", 10) * scale
            svg_parts.append(f'<rect x="{cx - cw/2}" y="{cy - ch/2}" width="{cw}" height="{ch}" fill="none" stroke="#aaa" stroke-width="1"/>')
            svg_parts.append(f'<text x="{cx}" y="{cy}" text-anchor="middle" dominant-baseline="middle" fill="#ccc" font-size="{max(8, min(12, cw/5))}">{comp.get("id","")}</text>')

            # Draw pads
            for pad in comp.get("pads", []):
                px = (comp.get("x", 0) + pad.get("x", 0)) * scale
                py = (comp.get("y", 0) + pad.get("y", 0)) * scale
                svg_parts.append(f'<circle cx="{px}" cy="{py}" r="{2*scale}" fill="#c0c0c0" stroke="#888" stroke-width="0.5"/>')

        svg_parts.append('</svg>')
        svg_content = "\n".join(svg_parts)

        return {
            "success": True,
            "traces": all_traces,
            "traceCount": len(all_traces),
            "netCount": len(nets),
            "svg": svg_content,
            "boardSize": {"width": board_w, "height": board_h},
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=3001,
        reload=True,
        log_level="info"
    )
