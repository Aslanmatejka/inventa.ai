# CAD AI Builder — Complete Project Documentation

## Table of Contents

1. [Goal & Purpose](#goal--purpose)
2. [How It Works (High-Level)](#how-it-works-high-level)
3. [Technology Stack](#technology-stack)
4. [Architecture Overview](#architecture-overview)
5. [Development Phases](#development-phases)
   - [Phase 1: Foundation](#phase-1-foundation--backend-api--cad-engine)
   - [Phase 2: AI Prompt Engineering](#phase-2-ai-prompt-engineering--parametric-code-generation)
   - [Phase 3: Quality Enforcement](#phase-3-quality-enforcement--design-completeness)
   - [Phase 4: Frontend & Visualization](#phase-4-frontend--visualization--interactive-parameters)
   - [Phase 5: Token Optimization & Upload Improvements](#phase-5-token-optimization--upload-improvements)
   - [Phase 6: PCB Electronics Integration](#phase-6-pcb-electronics-integration)
6. [Core Systems Deep Dive](#core-systems-deep-dive)
7. [Data Flow Walkthrough](#data-flow-walkthrough)
8. [File Structure & Key Files](#file-structure--key-files)
9. [API Endpoints Summary](#api-endpoints-summary)
10. [Setup & Running](#setup--running)
11. [Current State & Future Roadmap](#current-state--future-roadmap)

---

## Goal & Purpose

**CAD AI Builder** is a full-stack, AI-powered platform that turns plain English descriptions into production-quality 3D CAD models — instantly, in a browser.

### The Problem It Solves

Traditional CAD design requires:

- Expensive software licenses (SolidWorks, Fusion 360, etc.)
- Months or years of training to use CAD tools
- Manual dimensioning and feature placement
- Repetitive work for common product types

### The Solution

Type a sentence like _"iPhone 15 Pro case with camera cutout and USB-C port"_ and within seconds:

- A fully parametric 3D model appears in the browser
- Every dimension is adjustable via sliders (no AI call needed to tweak)
- Download STL for 3D printing or STEP for professional CAD editing
- Continue refining with follow-up natural language commands

### Who It's For

- **Makers & hobbyists** — rapid prototyping without CAD expertise
- **Engineers** — quickly scaffold designs then export STEP for refinement
- **Product designers** — test form factors before committing to full CAD
- **Educators** — teach parametric design concepts interactively
- **Anyone** who can describe a physical object in words but can't use CAD software

### Key Differentiators

| Feature            | CAD AI Builder                                   | Traditional CAD   | Other AI Tools           |
| ------------------ | ------------------------------------------------ | ----------------- | ------------------------ |
| Input method       | Natural language                                 | Manual modeling   | Text prompts             |
| Output format      | STEP + STL + parametric Python                   | Native formats    | Usually STL only         |
| Parametric editing | Real-time sliders (no AI cost)                   | Manual parameters | Not available            |
| Self-healing       | Infinite retry with 5 escalating strategies      | Manual debugging  | Fails or returns error   |
| Product knowledge  | 98+ product templates with real-world dimensions | None built-in     | Generic only             |
| PCB integration    | Full electronics design → KiCad + enclosure      | Separate tools    | Not available            |
| Iterative editing  | Edit existing models with language               | Manual edits      | Regenerates from scratch |

---

## How It Works (High-Level)

```
┌──────────────────────────────────────────────────────────────────┐
│  User types: "Create a drone frame with camera mount"            │
└──────────────────────┬───────────────────────────────────────────┘
                       │
                       ▼
┌──────────────────────────────────────────────────────────────────┐
│  1. PRODUCT LIBRARY SEARCH                                       │
│     Matches against 98+ templates for real-world dimensions      │
│     e.g., "drone" → motor spacing, arm width, camera mount size  │
└──────────────────────┬───────────────────────────────────────────┘
                       │
                       ▼
┌──────────────────────────────────────────────────────────────────┐
│  2. AI DESIGN GENERATION (Claude)                                │
│     ~3000-line system prompt teaches Claude how to write          │
│     CadQuery Python code with proper selectors, parameters,      │
│     and real-world proportions                                   │
│     Output: { parameters: [...], code: "...", explanation: {} }  │
└──────────────────────┬───────────────────────────────────────────┘
                       │
                       ▼
┌──────────────────────────────────────────────────────────────────┐
│  3. COMPLETENESS CHECK                                           │
│     AI self-critiques: "Is the camera mount actually there?"     │
│     If incomplete → sends back for targeted enhancement          │
└──────────────────────┬───────────────────────────────────────────┘
                       │
                       ▼
┌──────────────────────────────────────────────────────────────────┐
│  4. CODE EXECUTION (CadQuery + 7-transform pipeline)             │
│     Safety validation → preprocessing → exec() in sandbox       │
│     If error → SELF-HEALING (infinite loop, 5 phases)            │
│     - Phase 1: Fix the crashing line                             │
│     - Phase 2-3: Reduce complexity                               │
│     - Phase 4-5: Strip advanced features                         │
│     - Phase 6-7: Rewrite failing section                         │
│     - Phase 8+: Rebuild from scratch with primitives              │
└──────────────────────┬───────────────────────────────────────────┘
                       │
                       ▼
┌──────────────────────────────────────────────────────────────────┐
│  5. FILE EXPORT                                                  │
│     .step (editable CAD) + .stl (3D printable) + .py (script)   │
└──────────────────────┬───────────────────────────────────────────┘
                       │
                       ▼
┌──────────────────────────────────────────────────────────────────┐
│  6. BROWSER DISPLAY                                              │
│     Three.js renders the STL in a 3D viewer                      │
│     Parameter sliders appear for every dimension                 │
│     Export buttons for all file formats                          │
└──────────────────────────────────────────────────────────────────┘
```

---

## Technology Stack

### Backend

| Component        | Technology                    | Purpose                             |
| ---------------- | ----------------------------- | ----------------------------------- |
| Web framework    | FastAPI (Python)              | Async HTTP + SSE streaming          |
| ASGI server      | Uvicorn                       | Production-grade async server       |
| CAD engine       | CadQuery 2.6+                 | Solid geometry (OpenCASCADE kernel) |
| Parametric parts | cq_warehouse                  | Fasteners, bearings, gears          |
| AI / LLM         | Claude Opus (Anthropic)       | Natural language → CadQuery code    |
| Mesh import      | trimesh (optional)            | STL/OBJ/3MF/PLY/GLB handling        |
| Config           | pydantic-settings             | Environment variable management     |
| Database         | MySQL + SQLAlchemy (optional) | Project/build persistence           |
| Task queue       | Celery + Redis (optional)     | Async job processing                |
| Cloud storage    | boto3 / S3 (optional)         | Model sharing via URLs              |

### Frontend

| Component        | Technology                    | Purpose                            |
| ---------------- | ----------------------------- | ---------------------------------- |
| UI framework     | React 18.2                    | Component-based interface          |
| State management | useReducer + Context          | Centralized app state (25 actions) |
| 3D rendering     | Three.js + @react-three/fiber | WebGL model viewer                 |
| 3D helpers       | @react-three/drei             | Orbit controls, lighting           |
| Build streaming  | Native fetch + ReadableStream | SSE for real-time progress         |
| File upload      | XMLHttpRequest                | Progress tracking                  |
| Build tooling    | Create React App (Webpack 5)  | Development & bundling             |

### PCB System

| Component         | Technology                            | Purpose                       |
| ----------------- | ------------------------------------- | ----------------------------- |
| File format       | KiCad S-expression (.kicad_pcb)       | Industry-standard PCB output  |
| 3D modeling       | CadQuery (same engine)                | PCB board as 3D geometry      |
| Component library | Custom (50 components, 13 categories) | Footprint & dimension data    |
| Approach          | Zero external dependencies            | Generates KiCad text directly |

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                        BROWSER  (port 3000)                         │
│                                                                     │
│   ┌─────────────────┐   resize   ┌──────────────────────────────┐  │
│   │   CHAT PANEL    │◄──handle──►│      3D PREVIEW PANEL        │  │
│   │                 │            │                              │  │
│   │  • Messages     │            │  ┌────────────────────────┐  │  │
│   │  • Build steps  │            │  │  Three.js WebGL Canvas │  │  │
│   │  • Healing log  │            │  │  (STL via STLLoader)   │  │  │
│   │  • File upload  │            │  └────────────────────────┘  │  │
│   │  • Prompt input │            │  ┌──────────┐ ┌───────────┐  │  │
│   │                 │            │  │ Parameter│ │  Export    │  │  │
│   │                 │            │  │ Sliders  │ │  Panel    │  │  │
│   │                 │            │  └──────────┘ └───────────┘  │  │
│   │                 │            │  ┌────────────────────────┐  │  │
│   │                 │            │  │  PCB Panel (optional)  │  │  │
│   │                 │            │  └────────────────────────┘  │  │
│   └─────────────────┘            └──────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
                │  SSE stream / REST API calls  │
                ▼                               ▼
┌─────────────────────────────────────────────────────────────────────┐
│                     FastAPI  (port 3001)                            │
│                                                                     │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │  SERVICES LAYER                                              │   │
│  │                                                              │   │
│  │  claude_service          → AI prompt engineering, streaming  │   │
│  │  parametric_cad_service  → Code safety, 7-transform, exec() │   │
│  │  pcb_design_service      → KiCad generation, 3D board model │   │
│  │  cad_import_service      → File upload & format conversion   │   │
│  │  product_library         → 98+ product templates             │   │
│  │  product_visual_knowledge→ Category-specific build guides    │   │
│  │  pcb_component_library   → 50 electronic components         │   │
│  │  database_service        → MySQL persistence (optional)      │   │
│  │  s3_service              → Cloud sharing (optional)          │   │
│  │  glb_service             → STL→GLB conversion (optional)     │   │
│  └──────────────────────────────────────────────────────────────┘   │
│                                                                     │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │  OUTPUT                                                      │   │
│  │  exports/cad/   → .step, .stl, _parametric.py               │   │
│  │  exports/pcb/   → .kicad_pcb files                          │   │
│  │  exports/uploads/→ uploaded source files                     │   │
│  └──────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Development Phases

### Phase 1: Foundation — Backend API & CAD Engine

**Goal**: Build the core backend that can receive text prompts and produce 3D CAD files.

**What was built**:

1. **FastAPI application** (`main.py`) — HTTP server on port 3001 with CORS, middleware, and routing
2. **Claude AI integration** (`claude_service.py`) — Connects to Anthropic's API, sends user prompts with a system prompt, receives design JSON
3. **CadQuery geometry engine** (`cadquery_service.py`) — Takes AI-generated design descriptions and produces STEP/STL geometry
4. **Configuration** (`config.py`) — Pydantic-settings based config loading from `.env` files
5. **Design validation** (`validator.py`) — Pydantic schemas for type safety, constraint validation (wall thickness ≥ 1.5mm)
6. **Startup script** (`start.py`) — Sets UTF-8 encoding, launches Uvicorn with hot reload

**API endpoints created**:

- `POST /api/build` — Single-shot CAD generation
- `POST /api/chat` — Conversational design refinement
- `GET /exports/cad/{filename}` — File downloads
- `GET /` — Health check

**Outcome**: A working backend that takes "Create a 50x30x20mm box" → produces STEP + STL files.

---

### Phase 2: AI Prompt Engineering & Parametric Code Generation

**Goal**: Make the AI output executable, parametric CadQuery Python code instead of abstract design descriptions.

**What changed**:

1. **New service**: `parametric_cad_service.py` — The core code execution engine that:
   - Validates code safety (allowlist of imports, forbidden calls)
   - Executes AI-generated CadQuery code in a sandboxed `exec()` namespace
   - Exports STEP + STL + standalone parametric Python scripts

2. **Enhanced Claude system prompt** — Trained Claude to output:

   ```json
   {
     "parameters": [
       {
         "name": "length",
         "default": 50.0,
         "min": 1,
         "max": 2000,
         "unit": "mm"
       }
     ],
     "code": "import cadquery as cq\nresult = cq.Workplane('XY').box(length, width, height)",
     "explanation": { "design_intent": "...", "selector_choices": "..." }
   }
   ```

3. **Selector enforcement** — AI required to use explicit CadQuery selectors (`>Z`, `<X`, `|Y`) instead of ambiguous calls

4. **Knowledge injection** — System prompt includes CadQuery cheat sheet, face/edge selectors, best practices

**Key design decisions**:

- Parameters as named variables at the top of every script
- All dimensions parametric (no hardcoded numbers)
- Code safety: only `cadquery`, `math`, `copy`, `numpy` imports allowed
- Forbidden: `eval()`, `exec()`, `open()`, `__import__()`, `os`, `sys`, `subprocess`

**Outcome**: AI generates real, executable Python code with adjustable parameters.

---

### Phase 3: Quality Enforcement & Design Completeness

**Goal**: Fix two critical issues — (1) AI producing oversimplified designs missing essential features, (2) AI regenerating from scratch instead of modifying existing code.

**The problem**:

- "Build a modern drone" → produced a simple box frame without motor mounts, camera, or battery bay
- "Build a phone case" → produced a rounded rectangle without charging port, speakers, or camera cutout
- "Add a hole to the side" → entire design regenerated from scratch (destroying prior work)

**What was built**:

1. **Mandatory Pre-Flight Audit** — A section in the system prompt that forces Claude to verify essential components before returning. Uses product-specific checklists:
   - **Drone**: Must have 4 motor mount arms, camera mount, central body, motor screw holes, battery compartment
   - **Phone case**: Must have charging port, speaker grille, camera cutout, 3+ button cutouts, screen lip
   - **Building**: Must have windows on 2+ walls, door with frame, actual roof

2. **Absolute Modification Rules** — Five non-negotiable rules for edits:
   - Code must contain ALL lines from previous code
   - Line count = previous + 5 to 40 new lines
   - First/last 10 lines must match previous exactly
   - All old parameters preserved
   - All existing features preserved

3. **Visual enforcement tactics** — Used impossible-to-miss formatting:
   - Solid block characters (`█████`) creating visual walls
   - Stop signs (`🛑`) and red circles (`🔴`)
   - FAILURE/REJECTION language ("If you don't do this, your response FAILS")

**Outcome**: Dramatically improved design completeness and modification preservation.

---

### Phase 4: Frontend & Visualization — Interactive Parameters

**Goal**: Build the complete browser interface with 3D viewer, parameter sliders, export panel, and live build streaming.

**What was built**:

1. **React 18 frontend** (`client/`) — Full single-page app with:
   - Resizable split-panel layout (chat + 3D preview)
   - Mobile responsive design (tabs below 968px)
   - Undo/redo (20-step history, Ctrl+Z / Ctrl+Shift+Z)
   - Build progress bar with elapsed time counter

2. **Three.js 3D viewer** (`MultiProductCanvas.jsx`) — WebGL rendering with:
   - STL loading via Three.js STLLoader
   - Orbit controls (rotate, pan, zoom)
   - Auto-fit camera to model bounds
   - Multi-model support (scenes)
   - Empty-state animation (floating icons), loading animation (rotating cube)

3. **Parameter sliders** (`ParameterPanel.jsx`) — Auto-generated from AI parameters:
   - Range slider for every dimension
   - Real-time value display with units
   - "Update 3D Model" button → `POST /api/rebuild` (no AI call, < 2 seconds)

4. **Export panel** (`ExportPanel.jsx`) — Download buttons for STEP, STL, parametric Python script

5. **SSE streaming** — 6-step progress events streamed live as the model is built

6. **State management** (`AppContext.jsx`) — `useReducer` with 25 actions:
   - `BUILD_START` / `BUILD_PROGRESS` / `BUILD_COMPLETE`
   - `TOGGLE_CHAT_COLLAPSED` / `TOGGLE_PREVIEW_COLLAPSED`
   - `SET_UPLOADED_FILE` / `UNDO` / `REDO` / `RESET_WORKSPACE`

7. **Build hook** (`useBuild.js`) — Custom React hook encapsulating:
   - SSE stream consumption and event parsing
   - Scene management (create/add products)
   - NLP edit flow for uploaded files
   - Self-healing event forwarding to UI

8. **Additional backend features**:
   - `POST /api/rebuild` — Parameter-only rebuild endpoint
   - Celery async task queue (optional, for heavy workloads)
   - S3 upload/download for model sharing (optional)
   - GLB export via trimesh (optional, optimized for Three.js)
   - Mesh statistics endpoint

**Outcome**: Complete browser-based CAD design environment with live 3D preview and interactive parameter tuning.

---

### Phase 5: Token Optimization & Upload Improvements

**Goal**: Reduce AI token consumption on edits/fixes (saving cost), and make uploaded CAD files fully editable through natural language.

**What was built**:

1. **Three-tier prompt system** (massive cost reduction):

   | Prompt             | Size           | Used for                       |
   | ------------------ | -------------- | ------------------------------ |
   | Full system prompt | ~35,000 tokens | New designs from scratch       |
   | Edit prompt        | ~460 tokens    | Modifying existing designs     |
   | Fix prompt         | ~330 tokens    | Self-healing error corrections |

   **How it works**: `generate_design_from_prompt()` auto-detects whether the request is a new build or a modification. Modifications skip the massive 3000-line system prompt and use a lightweight edit prompt instead, reducing API costs by ~98-99%.

2. **CAD file upload improvements**:
   - All mesh formats (STL, OBJ, 3MF, PLY, GLB) made editable via language
   - Upload edits routed through the same SSE streaming pipeline as normal builds
   - "NLP editable" badge in prompt bar when an uploaded file is active
   - Improved FileUpload component UI with drag-and-drop

3. **Upload editing flow**:
   ```
   Upload STEP/STL → 3D viewer shows model → Type "add mounting holes"
   → AI receives imported geometry code → Generates modified CadQuery code
   → New model replaces old → Chain further edits
   ```

**Outcome**: 98-99% token savings on edits, and uploaded files are now first-class citizens for NLP editing.

---

### Phase 6: PCB Electronics Integration

**Goal**: Enable full product design — not just mechanical enclosures, but also the electronics (PCB) that go inside them, with automatic enclosure generation that accounts for connectors, displays, and mounting.

**What was built**:

1. **PCB component library** (`pcb_component_library.py`, ~630 lines):
   - 50 electronic components across 13 categories
   - Categories: Audio, Connector, Display, LED, MCU, MCU_Module, Motor, Passive, Power, RF, Relay, Sensor, Switch
   - Each component has: body dimensions (x/y/z), pin count, pitch, mounting type, keepout zones
   - Special fields: `edge_mount` flag, `mating_face` dimensions, `display_area`
   - Board presets: Arduino Uno, Raspberry Pi HAT, Credit Card size
   - Search & lookup functions

2. **PCB design service** (`pcb_design_service.py`, ~600 lines):

   | Method                         | Purpose                                                          |
   | ------------------------------ | ---------------------------------------------------------------- |
   | `generate_pcb_from_spec()`     | Main entry: PCB spec JSON → KiCad file + 3D model + enclosure    |
   | `_generate_kicad_pcb()`        | Writes KiCad S-expression format with layers, footprints, traces |
   | `_generate_3d_model()`         | CadQuery board substrate + component bodies + mounting holes     |
   | `_generate_enclosure_spec()`   | Analyzes edge-mount components for cutout positions              |
   | `_generate_enclosure_code()`   | CadQuery code for matched enclosure with cutouts                 |
   | `get_pcb_system_prompt()`      | ~5835 char prompt supplement for Claude                          |
   | `get_pcb_detection_keywords()` | 29 keywords for auto-detecting PCB requests                      |

3. **AI integration**:
   - Claude auto-detects PCB requests (29 keyword triggers: "circuit board", "ESP32", "PCB", etc.)
   - PCB system prompt appended with component reference table
   - AI generates `pcb_spec` JSON with board dimensions, component placements, trace connections
   - Max tokens raised to 16384 for PCB designs

4. **Build pipeline integration** (step 2.5 in main build stream):

   ```
   AI returns pcb_spec → PCBDesignService generates:
     • KiCad .kicad_pcb file (S-expression format)
     • 3D STL/STEP of the populated board
     • Enclosure CadQuery code with connector cutouts & mounting posts
   → All bundled into final SSE result as pcbResult
   ```

5. **Frontend PCB panel** (`PCBPanel.jsx`):
   - Board dimensions display (width/height/thickness/corner radius)
   - Component list with reference designators and side badges (top/bottom)
   - Enclosure cutout information
   - Download buttons for KiCad, STEP, and STL files

6. **API endpoints**:
   - `GET /api/pcb/components?q=&category=` — Search component library
   - `GET /api/pcb/components/{id}` — Component detail
   - `GET /api/pcb/categories` — List all 13 categories
   - `POST /api/pcb/build/stream` — Dedicated PCB SSE build
   - `POST /api/pcb/enclosure` — Generate enclosure for existing PCB
   - `GET /exports/pcb/{filename}` — Serve KiCad files

**Key design decision**: Zero external dependencies. KiCad files are generated as plain text S-expressions — no KiCad installation, pcbnew, or skidl required. The PCB is simultaneously represented as CadQuery 3D geometry using the same engine as mechanical parts.

**Outcome**: Users can describe an electronics product in natural language and receive both the PCB design (KiCad format) and a matched mechanical enclosure with proper cutouts for USB ports, displays, buttons, etc.

---

## Core Systems Deep Dive

### Self-Healing Engine

The platform **never gives up** on a build. When CadQuery raises an error, the system classifies it and retries:

**18 error categories**: `GEOMETRY_FILLET_CHAMFER`, `GEOMETRY_SHELL`, `SKETCH_NOT_CLOSED`, `SELECTOR_FAILED`, `CURVE_TANGENT`, `REVOLVE_AXIS`, `MATH_ERROR`, `LOFT_FAILED`, `BOOLEAN_FAILED`, `WRONG_PARAMETER`, `SWEEP_FAILED`, `WORKPLANE_STACK`, `OCC_KERNEL_ERROR`, `ATTRIBUTE_ERROR`, `TYPE_ERROR`, `EMPTY_RESULT`, `NAME_ERROR`, `GENERAL`

**Five healing phases** (escalating):

| Phase        | Attempts | Strategy                                                         |
| ------------ | -------- | ---------------------------------------------------------------- |
| Targeted     | 1        | Fix only the crashing line, reduce fillet radii 30%              |
| Conservative | 2-3      | Reduce radii 60%, wrap in try/except, simplify splines           |
| Aggressive   | 4-5      | Strip all fillets/chamfers/shells, replace lofts with extrusions |
| Rewrite      | 6-7      | Rewrite the failing section using only safe primitives           |
| Nuclear      | 8+       | Rebuild entire model from scratch with boxes & cylinders only    |

Live SSE events show the user which healing phase is active during the build.

### 7-Step Code Preprocessing Pipeline

Before executing AI-generated code, it passes through 7 transforms (in this exact order):

| #   | Transform                        | Purpose                                               |
| --- | -------------------------------- | ----------------------------------------------------- |
| 1   | `_strip_centered_from_non_box()` | Remove `centered=` from methods that don't support it |
| 2   | `_ensure_box_grounding()`        | Add `centered=(True,True,False)` so Z=0 is ground     |
| 3   | `_fix_zero_dimensions()`         | Replace `.extrude(0)` with `.extrude(0.1)`            |
| 4   | `_fix_negative_z_positions()`    | Warn/clamp features below Z=0                         |
| 5   | `_ensure_result_assignment()`    | Auto-add `result = body` if AI forgot                 |
| 6   | `_clamp_fillet_radii()`          | Inject guards (15% of smallest dimension)             |
| 7   | `_wrap_fillets_in_try_except()`  | Wrap `.fillet()` / `.chamfer()` in try/except         |

**Critical**: This pipeline runs identically in both `_execute_cadquery_code()` (initial build) AND `rebuild_with_parameters()` (slider rebuilds).

### Code Safety System

AI-generated code runs in `exec()`, so safety is essential:

**Allowed imports**: `cadquery`, `cq`, `math`, `copy`, `cq_warehouse`, `numpy`, `np`

**Forbidden calls**: `eval(`, `exec(`, `open(`, `__import__(`, `file(`

**Forbidden modules**: `os`, `sys`, `subprocess`, `shutil`, `pathlib`, `socket`, `http`, `urllib`, `requests`, `importlib`, `ctypes`, `pickle`

**Triple-update rule**: Adding a new allowed import requires updating THREE places:

1. `allowed_imports` set in `_validate_code_safety()`
2. `namespace` dict in `_execute_cadquery_code()`
3. `namespace` dict in `rebuild_with_parameters()`

### Product Knowledge Base

Two knowledge systems feed into the AI:

1. **Product Library** (`product_library.py`, ~2400 lines) — 98+ real-world product templates:

   ```python
   {
     "keywords": ["iphone 15 pro"],
     "name": "iPhone 15 Pro",
     "category": "phone_case",
     "dimensions": {"length": 159.9, "width": 76.7, "height": 8.25},
     "features": ["Dynamic Island", "USB-C port", "triple camera"],
     "notes": "Titanium frame. Camera island 37×30mm at top-left."
   }
   ```

2. **Visual Knowledge** (`product_visual_knowledge.py`, ~1700 lines) — Per-category build guides:
   - `visual_profile` — proportions, profile shape, key visual characteristics
   - `build_strategy` — mandatory CadQuery operations (e.g., `.revolve()` for mugs)
   - `recognition_features` — what distinguishes this category
   - `position_map` — where specific features are located

### Prompt Caching

Identical prompts return instantly via an in-memory SHA-256 cache — no AI call needed for repeated requests.

### Streaming Architecture

The build uses Server-Sent Events (SSE) with 6 progress steps:

| Step | Event              | Description                                |
| ---- | ------------------ | ------------------------------------------ |
| 1    | Product search     | Matching against product library           |
| 2    | AI generation      | Claude generating CadQuery code            |
| 2.5  | PCB processing     | (if electronics detected) KiCad + 3D board |
| 3    | Completeness check | AI self-critique and enhancement           |
| 4    | CadQuery execution | Geometry building + self-healing if needed |
| 5    | File export        | STEP + STL + parametric script saved       |
| 6    | Complete           | Full result with all URLs and metadata     |

---

## Data Flow Walkthrough

### New Build Flow

```
User: "Create an IoT sensor enclosure with ESP32 and OLED display"
  │
  ├─► Frontend: App.jsx dispatches BUILD_START
  │   useBuild.js opens SSE connection to POST /api/build/stream
  │
  ├─► Backend: main.py receives request
  │   ├─ Step 1: Search product_library for "IoT sensor enclosure"
  │   ├─ Step 2: claude_service.generate_design_from_prompt()
  │   │   ├─ Detects "ESP32" + "OLED" → is_pcb = true
  │   │   ├─ Loads full system prompt (~35K tokens) + PCB supplement (~5835 chars)
  │   │   ├─ Streams response via client.messages.stream()
  │   │   └─ Returns { parameters, code, explanation, pcb_spec }
  │   │
  │   ├─ Step 2.5: pcb_design_service.generate_pcb_from_spec(pcb_spec)
  │   │   ├─ Generates KiCad .kicad_pcb file
  │   │   ├─ Generates 3D CadQuery model of populated board
  │   │   ├─ Generates enclosure code with cutouts
  │   │   └─ Exports PCB STL/STEP
  │   │
  │   ├─ Step 3: analyze_code_completeness()
  │   │   └─ If incomplete → enhance_incomplete_design() (sends back to AI)
  │   │
  │   ├─ Step 4: parametric_cad_service.generate_parametric_cad()
  │   │   ├─ _validate_code_safety() → pass/fail
  │   │   ├─ 7-step preprocessing pipeline
  │   │   ├─ exec() in sandboxed namespace
  │   │   └─ If error → self-healing loop (infinite retries)
  │   │
  │   ├─ Step 5: Export .step + .stl + _parametric.py
  │   │
  │   └─ Step 6: Return complete result via SSE
  │
  └─► Frontend: useBuild.js processes SSE events
      ├─ Updates progress bar at each step
      ├─ Loads STL into Three.js viewer
      ├─ Renders parameter sliders
      ├─ Shows PCB panel (if pcbResult present)
      └─ Pushes to undo history
```

### Modification Flow

```
User: "Make it 10mm taller and add ventilation slots"
  │
  ├─► Frontend: Sends previousDesign { code, parameters, explanation }
  │
  ├─► Backend: claude_service detects previousDesign → edit mode
  │   ├─ Uses lightweight edit prompt (~460 tokens instead of ~35K)
  │   ├─ AI receives previous code and modifies it (adding lines, not replacing)
  │   └─ Returns modified { parameters, code, explanation }
  │
  └─► Same execution pipeline (steps 3-6)
```

### Parameter Slider Flow

```
User: Drags "height" slider from 40mm → 55mm
  │
  ├─► Frontend: POST /api/rebuild { buildId, parameters: { height: 55 } }
  │
  ├─► Backend: parametric_cad_service.rebuild_with_parameters()
  │   ├─ Loads saved {buildId}_parametric.py
  │   ├─ Finds GEOMETRY section between markers
  │   ├─ Replaces parameter values
  │   ├─ Runs same 7-transform pipeline
  │   ├─ exec() with new values
  │   └─ Re-exports STL/STEP (overwrites same buildId)
  │
  └─► Frontend: Reloads STL in viewer (< 2 seconds, NO AI call)
```

---

## File Structure & Key Files

```
Cad-ai-builder/
│
├── Backend/
│   ├── main.py                         # FastAPI app, all routes (~1470 lines)
│   ├── start.py                        # Startup: UTF-8 encoding, launches Uvicorn
│   ├── config.py                       # Pydantic-settings config from .env
│   ├── tasks.py                        # Celery task definitions (optional)
│   ├── validator.py                    # Pydantic schemas, constraint validation
│   ├── requirements.txt               # Core Python dependencies
│   ├── requirements-phase4.txt        # Optional deps (Celery, boto3, trimesh)
│   │
│   └── services/
│       ├── __init__.py                 # Service singletons & availability flags
│       ├── claude_service.py           # AI engine (~5230 lines)
│       │   ├── _get_design_system_prompt()  # ~35K token full prompt
│       │   ├── _get_edit_system_prompt()    # ~460 token edit prompt
│       │   ├── _get_fix_system_prompt()     # ~330 token fix prompt
│       │   ├── generate_design_from_prompt() # Main entry, auto-detects edit vs new
│       │   ├── fix_code_with_error()        # Self-healing with 5 phases
│       │   ├── analyze_code_completeness()  # Self-critique
│       │   ├── enhance_incomplete_design()  # Targeted enhancement
│       │   └── _detect_pcb_request()        # 29-keyword PCB detection
│       │
│       ├── parametric_cad_service.py   # Code execution engine (~1050 lines)
│       │   ├── generate_parametric_cad()    # Full pipeline entry
│       │   ├── _validate_code_safety()      # Import/call allowlist
│       │   ├── _execute_cadquery_code()     # 7-transform + exec()
│       │   ├── rebuild_with_parameters()    # Slider rebuild (no AI)
│       │   └── 7 preprocessing methods
│       │
│       ├── pcb_component_library.py    # 50 components, 13 categories (~630 lines)
│       ├── pcb_design_service.py       # KiCad gen, 3D board, enclosure (~600 lines)
│       ├── cad_import_service.py       # File upload & format conversion
│       ├── cadquery_service.py         # Legacy geometry service
│       ├── product_library.py          # 98+ product templates (~2400 lines)
│       ├── product_visual_knowledge.py # Category build guides (~1700 lines)
│       ├── database_service.py         # MySQL ORM (optional)
│       ├── s3_service.py               # S3 sharing (optional)
│       └── glb_service.py              # STL→GLB conversion (optional)
│
├── client/
│   ├── package.json
│   └── src/
│       ├── index.js                    # React entry, wraps with AppProvider
│       ├── App.jsx                     # Layout shell (~700 lines)
│       ├── App.css                     # Full layout CSS (~900 lines)
│       ├── api.js                      # All API calls (~468 lines)
│       ├── ErrorBoundary.jsx           # React error boundary
│       │
│       ├── context/
│       │   └── AppContext.jsx          # useReducer store, 25 actions (~253 lines)
│       │
│       ├── hooks/
│       │   └── useBuild.js             # Build logic, SSE, scene management (~520 lines)
│       │
│       └── components/
│           ├── MultiProductCanvas.jsx  # Three.js 3D viewer
│           ├── ParameterPanel.jsx      # Dimension sliders
│           ├── ExportPanel.jsx         # Download buttons
│           ├── PromptInput.jsx         # Text input with upload badge
│           ├── FileUpload.jsx          # Drag-and-drop upload zone
│           ├── ProjectBrowser.jsx      # Saved projects (MySQL)
│           ├── PCBPanel.jsx            # PCB design results display
│           └── *.css                   # Co-located CSS per component
│
├── exports/
│   ├── cad/                            # Generated .step .stl _parametric.py
│   ├── pcb/                            # Generated .kicad_pcb files
│   └── uploads/                        # Uploaded source files
│
├── .env                                # API keys (not committed)
├── test_phase32.py                     # Tests: parametric CAD pipeline
├── test_completeness.py                # Tests: code completeness analysis
├── test_drone_types.py                 # Tests: drone detection
├── test_phone_case_analyzer.py         # Tests: phone case analysis
├── test_shape_quality.py               # Tests: shape quality metrics
└── test_cq_warehouse.py               # Tests: cq_warehouse integration
```

---

## API Endpoints Summary

### Build & Design

| Method | Endpoint            | Description                               |
| ------ | ------------------- | ----------------------------------------- |
| `POST` | `/api/build/stream` | Stream a new build via SSE (6 steps)      |
| `POST` | `/api/build`        | Synchronous build (waits for result)      |
| `POST` | `/api/rebuild`      | Rebuild with new parameter values (no AI) |

### File Upload

| Method | Endpoint              | Description                         |
| ------ | --------------------- | ----------------------------------- |
| `POST` | `/api/upload`         | Upload CAD file (STEP/STL/OBJ/etc.) |
| `POST` | `/api/upload/edit`    | NLP edit an uploaded file           |
| `GET`  | `/api/upload/formats` | List supported formats              |

### PCB Electronics

| Method | Endpoint                   | Description                         |
| ------ | -------------------------- | ----------------------------------- |
| `GET`  | `/api/pcb/components`      | Search component library            |
| `GET`  | `/api/pcb/components/{id}` | Get component details               |
| `GET`  | `/api/pcb/categories`      | List all 13 categories              |
| `POST` | `/api/pcb/build/stream`    | Dedicated PCB build via SSE         |
| `POST` | `/api/pcb/enclosure`       | Generate enclosure for existing PCB |

### Scene Management

| Method   | Endpoint                            | Description                    |
| -------- | ----------------------------------- | ------------------------------ |
| `POST`   | `/api/scene/create`                 | Create multi-product scene     |
| `GET`    | `/api/scene/{id}`                   | Get scene with products        |
| `POST`   | `/api/scene/{id}/add-product`       | Add product to scene           |
| `PUT`    | `/api/scene/product/{id}/transform` | Update position/rotation/scale |
| `POST`   | `/api/scene/product/{id}/duplicate` | Duplicate with offset          |
| `DELETE` | `/api/scene/product/{id}`           | Remove from scene              |

### Projects & History (MySQL required)

| Method   | Endpoint             | Description             |
| -------- | -------------------- | ----------------------- |
| `GET`    | `/api/projects`      | List saved projects     |
| `POST`   | `/api/projects`      | Create project          |
| `GET`    | `/api/projects/{id}` | Get project with builds |
| `DELETE` | `/api/projects/{id}` | Delete project          |

### Files & Utilities

| Method | Endpoint                  | Description                  |
| ------ | ------------------------- | ---------------------------- |
| `GET`  | `/exports/cad/{filename}` | Download generated CAD files |
| `GET`  | `/exports/pcb/{filename}` | Download KiCad files         |
| `GET`  | `/`                       | Health check                 |
| `GET`  | `/api/health`             | Detailed service status      |
| `GET`  | `/api/cache/check`        | Check prompt cache           |
| `POST` | `/api/convert/glb`        | STL → GLB conversion         |

---

## Setup & Running

### Prerequisites

| Requirement       | Version | Required      |
| ----------------- | ------- | ------------- |
| Python            | 3.10+   | Yes           |
| Node.js           | 18+     | Yes           |
| Anthropic API key | —       | Yes           |
| MySQL             | 8.0+    | No (optional) |
| Redis             | 7+      | No (optional) |

### Installation

```bash
# 1. Clone
git clone https://github.com/Aslanmatejka/Cad-ai-builder.git
cd Cad-ai-builder

# 2. Python dependencies
pip install -r Backend/requirements.txt

# 3. Environment (create .env at project root)
echo "ANTHROPIC_API_KEY=sk-ant-api03-your-key-here" > .env

# 4. Frontend dependencies
cd client && npm install && cd ..
```

### Running

```powershell
# Terminal 1 — Backend (port 3001)
cd Backend
python start.py

# Terminal 2 — Frontend (port 3000)
cd client
npm start
```

### Verify

- Backend health: `GET http://localhost:3001/` → `{"status": "healthy"}`
- API docs: `http://localhost:3001/docs`
- Frontend: `http://localhost:3000` (opens automatically)

### Environment Variables

Only `ANTHROPIC_API_KEY` is required. All others are optional:

| Variable            | Default                  | Purpose                     |
| ------------------- | ------------------------ | --------------------------- |
| `ANTHROPIC_API_KEY` | —                        | Claude AI access (required) |
| `AI_MODEL_NAME`     | `claude-opus-4-20250514` | Claude model selection      |
| `AI_MAX_TOKENS`     | `16384`                  | Max tokens per AI response  |
| `AI_TEMPERATURE`    | `0.3`                    | AI creativity (0.0–1.0)     |
| `PORT`              | `3001`                   | Backend port                |
| `DB_PASSWORD`       | —                        | MySQL password (enables DB) |
| `AWS_ACCESS_KEY_ID` | —                        | S3 sharing                  |
| `REDIS_URL`         | —                        | Celery task queue           |

---

## Current State & Future Roadmap

### What Works Today

- Full natural language → 3D model pipeline
- 98+ product templates with real-world dimensions
- Self-healing engine that never fails (5 escalating strategies)
- Parametric sliders for instant tweaks (no AI cost)
- STEP + STL + Python script export
- CAD file upload and NLP editing (STEP, IGES, BRep, DXF, meshes)
- PCB electronics integration (KiCad output + matched enclosures)
- Iterative modifications that preserve existing work
- Token-optimized prompts (98-99% savings on edits)
- Mobile-responsive UI with undo/redo

### Optional Features (enabled by adding credentials/packages)

- MySQL persistence for projects and chat history
- S3 cloud sharing with presigned URLs
- GLB export (optimized for web)
- Celery async tasks for concurrent users

### Future Roadmap

- Multi-model assembly with constraint solving
- Real-time collaboration (WebSocket session sharing)
- Version history (git-like branching for designs)
- Material & finish metadata for manufacturing
- Direct 3D printer slicing integration
- BOM generation from cq_warehouse usage
- 2D engineering drawing export (DXF/PDF)
- PCB trace routing visualization
- Component placement drag-and-drop UI
- Visual PCB board preview (2D top-down view)

---

_Last updated: March 2026_
_License: MIT © Aslanmatejka_
