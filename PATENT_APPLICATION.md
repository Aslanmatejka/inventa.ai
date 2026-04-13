# PATENT APPLICATION

## SYSTEM AND METHOD FOR AUTOMATED GENERATION OF THREE-DIMENSIONAL COMPUTER-AIDED DESIGN MODELS FROM NATURAL LANGUAGE INPUT WITH SELF-HEALING CODE SYNTHESIS AND PARAMETRIC REBUILD

---

## CROSS-REFERENCE TO RELATED APPLICATIONS

This application claims priority to the subject matter described herein. No prior applications have been filed.

---

## FIELD OF THE INVENTION

The present invention relates generally to the field of computer-aided design (CAD) and, more specifically, to a system and method for converting natural language descriptions into parametric three-dimensional solid models using large language model (LLM)-based code synthesis, multi-phase self-healing error correction, product knowledge injection, automated code completeness analysis, and real-time parametric manipulation through a web-based three-dimensional visualization interface.

---

## BACKGROUND OF THE INVENTION

### Problem Statement

Computer-aided design (CAD) software has long been a cornerstone of engineering and manufacturing. However, traditional CAD tools require specialized training, mastery of complex graphical user interfaces, and deep understanding of solid modeling kernels. This creates a significant barrier to entry for inventors, designers, entrepreneurs, and non-technical stakeholders who have product ideas but lack CAD proficiency.

Existing approaches to lowering the CAD barrier include:

1. **Template-based parametric generators** — constrained to predefined product families with fixed topologies.
2. **Sketch-to-3D systems** — require the user to draw 2D sketches, still demanding spatial reasoning skill.
3. **Generative AI image systems** — produce visual renderings (meshes, point clouds, or NeRF volumes) that are not solid models and cannot be directly manufactured, exported to industry-standard formats (STEP, IGES), or parametrically edited.
4. **Direct LLM code generation** — raw language model outputs frequently contain geometric errors, API misuse, degenerate solids, and crash-inducing operations, with no mechanism for automatic correction.

None of the prior art provides an end-to-end system that (a) accepts unconstrained natural language prompts, (b) synthesizes executable parametric solid-modeling code, (c) automatically detects and repairs geometric failures through graduated self-healing, (d) enforces feature completeness against a curated product knowledge base, and (e) delivers real-time parametric adjustment without further AI invocation.

### Objects of the Invention

It is therefore a primary object of the present invention to provide a system and method that converts unconstrained natural language descriptions into manufacturable, parametric three-dimensional CAD models.

It is a further object to provide a multi-phase self-healing mechanism that automatically classifies and repairs geometric code failures with escalating repair strategies.

It is a further object to provide a product knowledge injection system that augments the LLM with real-world dimensional data, visual construction recipes, and categorical feature checklists to ensure physically plausible outputs.

It is a further object to provide a code completeness analysis engine that programmatically detects missing product features and triggers iterative design enhancement.

It is a further object to provide a parametric rebuild system that enables real-time geometry regeneration from parameter slider inputs without requiring any further LLM invocation.

It is a further object to provide a code safety sandboxing system that validates AI-generated code against a strict allowlist before execution.

---

## SUMMARY OF THE INVENTION

The present invention is an integrated platform, referred to herein as "inventa.AI," comprising a backend server, an AI code synthesis service, a parametric CAD execution engine, a product knowledge subsystem, and a browser-based three-dimensional visualization client. The system operates according to the following novel pipeline:

1. **Natural Language Input** — A user submits a free-form textual description of a desired product (e.g., "a protective case for iPhone 15 Pro with camera cutout and button openings").

2. **Product Knowledge Lookup** — The system consults a curated product library containing 98+ product templates with real-world dimensions (e.g., iPhone dimensions, standard screw sizes, bearing specifications) and a visual knowledge base containing 34 product-category construction recipes with axis assignments, feature position maps, and workplane-to-face mappings.

3. **LLM-Based Parametric Code Synthesis** — A large language model (Claude, GPT, or equivalent) generates a structured JSON response containing: (a) a list of user-adjustable parameters with default, minimum, maximum values and units; (b) executable CadQuery Python code defining the complete solid model; and (c) a human-readable design explanation. The LLM is guided by a system prompt exceeding 145,000 characters that encodes coordinate system conventions, feature placement recipes, CadQuery API patterns, common-mistake avoidance rules, and a slot2D/cylinder axis mapping reference.

4. **Code Safety Validation** — Before execution, the generated code passes through an allowlist-based import validator that permits only `cadquery`, `math`, `numpy`, `copy`, and `cq_warehouse` imports, blocks 30+ forbidden modules and function calls (including `eval`, `exec`, `open`, `__import__`, `subprocess`, `os`, `sys`), and detects Python dunder escape patterns (`__builtins__`, `__subclasses__`).

5. **Preprocessing Pipeline** — The validated code passes through a five-step ordered transformation pipeline: (i) stripping invalid `centered=` arguments from non-`.box()` calls; (ii) replacing zero-dimension geometry with safe minimums; (iii) auto-assigning the `result` variable if the LLM omitted it; (iv) injecting `min()` radius guards on all fillet/chamfer calls to clamp them to 25% of the smallest dimension; and (v) wrapping unprotected fillet/chamfer calls in `try/except` blocks.

6. **Sandboxed Execution and Ground-Plane Enforcement** — The preprocessed code is executed within an isolated Python namespace via `exec()`. After execution, the resulting solid model is automatically translated so its bounding-box bottom aligns with Z=0 (the ground plane convention), ensuring consistent orientation regardless of how the LLM constructed the geometry.

7. **Code Completeness Analysis** — A programmatic analyzer inspects the generated code against product-specific feature checklists (e.g., a phone case must have camera cutout, USB-C port, button openings, speaker holes). If missing features are detected, the code is automatically sent back to the LLM for targeted enhancement, with up to two iterative enhancement passes.

8. **Multi-Phase Self-Healing** — If the CadQuery execution engine raises a geometric error, the system classifies the error into one of 16 categories and initiates a graduated healing process with five escalating phases over up to 15 attempts: (i) Targeted fix — repair only the failing line, reduce fillet radii by 30%; (ii) Conservative — reduce radii by 60%, wrap operations in try/except; (iii) Aggressive — strip all fillets/chamfers/shells, replace lofts with extrusions; (iv) Rewrite — rebuild the failing section using only safe primitives; (v) Nuclear — rebuild the entire model from scratch using only boxes and cylinders.

9. **Multi-Format Export** — Successful geometry is exported to STEP (industry-standard editable CAD), STL (3D printing), and a self-contained parametric Python script.

10. **Parametric Rebuild Without AI** — The exported parametric script uses exact comment markers (`# GEOMETRY GENERATION` and `# EXPORT`) that the rebuild engine parses to extract and re-execute only the geometry section with updated parameter values. Frontend slider changes trigger this path, producing instant geometry updates with no LLM cost.

11. **Real-Time 3D Visualization** — The browser client renders the STL model in a WebGL-based Three.js scene with orbit controls, lighting, grid, and per-product instance management, supporting multi-product workspace canvases.

12. **Server-Sent Events Streaming** — The build pipeline streams step-by-step progress events (product lookup → AI synthesis → completeness check → CadQuery execution → export) to the frontend via SSE, providing real-time visibility into each phase including self-healing attempts.

---

## DETAILED DESCRIPTION OF THE INVENTION

### 1. System Architecture

The system comprises the following interconnected components:

**1.1 Backend Server** — A FastAPI (Python) web server operating on a configurable port (default 3001) that exposes RESTful API endpoints for build requests, parametric rebuilds, project management, file serving, real-time collaboration, and health monitoring. The server implements CORS middleware, rate limiting (via `slowapi`), JWT-based authentication middleware (for Supabase integration), and request/response logging.

**1.2 AI Code Synthesis Service (ClaudeService)** — A unified LLM integration layer that routes requests to either the Anthropic Claude API or OpenAI GPT API based on model identifier prefix. The service implements:

- **Adaptive Token Allocation** — A complexity detection algorithm that classifies prompts as "high," "medium," or "standard" based on keyword matching against two curated keyword sets (38 high-complexity keywords, 12 medium-complexity keywords) and word-count thresholds (>80 words = high, >40 words = medium). High-complexity prompts receive 16,384 max tokens and 0.25 temperature; standard prompts use default settings.

- **Streaming with Retry** — Both Anthropic and OpenAI completions use streaming APIs with exponential backoff retry policies: rate-limit errors (10s × attempt), overloaded errors (8s × attempt), and network errors (2s × attempt), each up to 3–5 attempts.

- **Dual System Prompts** — A full design system prompt (~145,000+ characters) for new designs, and a lightweight edit system prompt (~2,000 characters) for modifications that instructs the LLM to edit existing code rather than regenerate from scratch.

- **Multi-Provider Routing** — A single `_stream_completion()` method inspects the model identifier and dispatches to `_stream_anthropic()` or `_stream_openai()`, converting message formats as needed (Anthropic content blocks → OpenAI string messages; reasoning model parameter adjustments).

**1.3 Parametric CAD Execution Engine (ParametricCADService)** — The core geometry engine that:

- Validates code safety via allowlist enforcement.
- Applies the five-step preprocessing pipeline.
- Executes code in an isolated namespace with CadQuery, math, numpy, and optionally cq_warehouse (parametric fasteners, bearings, sprockets, threads) pre-loaded.
- Grounds the result to Z=0.
- Detects and resolves multi-solid results by retaining the largest solid by volume.
- Computes quality metrics (volume, bounding box, dimensional ratios, feature counts) and generates a 1–10 quality score with actionable improvement suggestions.
- Exports to STEP and STL with fallback tolerance relaxation for complex geometry.
- Generates self-contained parametric Python scripts with embedded parameter definitions and exact comment markers for the rebuild system.

**1.4 Product Knowledge Subsystem** — Two complementary knowledge sources:

- **Product Library** (~2,400 lines, 98+ templates) — A structured database of real-world product specifications including keywords, names, categories, physical dimensions, features, and notes. Queried by keyword matching against the user's prompt.

- **Product Visual Knowledge** (~1,700 lines, 34 categories) — Per-category dictionaries containing: (a) `visual_profile` — multi-angle verbal descriptions of what the product looks like; (b) `build_strategy` — step-by-step CadQuery construction recipes with explicit axis assignments, workplane selections, and feature positions; (c) `recognition_features` — the 3–5 features whose absence makes a model unrecognizable; (d) `position_map` — exact face/axis/coordinate mappings for every feature.

**1.5 Browser-Based 3D Visualization Client** — A React 18 application using `@react-three/fiber` (React Three Fiber) and `@react-three/drei` for Three.js integration, comprising:

- **MultiProductCanvas** — A WebGL canvas supporting multiple product instances with independent transforms, selection, and material assignment.
- **ParameterPanel** — Dynamic slider UI generated from the parameter list, dispatching `POST /api/rebuild` requests.
- **PromptInput** — Tri-mode input (Agent, Ask, Plan) with SSE streaming progress display.
- **ExportPanel** — Download controls for STL, STEP, and parametric Python scripts.
- **ProjectBrowser** — Supabase-backed project listing and build history.
- **useBuild Hook** — Centralized build orchestration logic with SSE event parsing, progress calculation, and scene management.

**1.6 Persistence Layer** — A pluggable storage architecture with graceful degradation:

- **Supabase (PostgreSQL)** — Primary database for projects, builds, user accounts. Activated only when `SUPABASE_URL` and `SUPABASE_ANON_KEY` are configured.
- **Amazon S3** — Optional cloud storage for sharing builds. Activated only when AWS credentials and `boto3` are present.
- **MySQL** — Optional alternative database. Activated only when `pymysql` and `sqlalchemy` are present.
- **GLB Export** — Optional WebGL-optimized format. Activated only when `trimesh` is present.

Each optional dependency uses a `try/except ImportError` pattern, allowing the system to operate with zero external services beyond the LLM API.

---

### 2. Natural Language to CAD Pipeline (Detailed Flow)

#### 2.1 Request Ingestion

The frontend submits a `POST /api/build/stream` request containing:

```json
{
  "prompt": "a protective case for iPhone 15 Pro with camera cutout",
  "previousDesign": null | { "code": "...", "parameters": [...] },
  "projectId": "optional-uuid",
  "model": "claude-opus-4-6"
}
```

The server determines whether the request is a new design or a modification based on the presence of `previousDesign` with non-empty `code`.

#### 2.2 Prompt Cache Check

For new designs (non-modifications), a SHA-256 hash of the normalized prompt is computed. If a matching cached result exists and its output files are still present on disk, the cached result is returned immediately via SSE, bypassing all AI and geometry computation. The cache is bounded to 100 entries with FIFO eviction.

#### 2.3 Complexity Detection and Adaptive Parameters

The prompt is classified by the `_detect_complexity()` method:

| Condition                                             | Classification | Max Tokens | Temperature |
| ----------------------------------------------------- | -------------- | ---------- | ----------- |
| Word count > 80, or matches high-complexity keyword   | High           | 16,384     | 0.25        |
| Word count > 40, or matches medium-complexity keyword | Medium         | 12,288     | default     |
| Otherwise                                             | Standard       | default    | default     |

The 38 high-complexity keywords include: "detailed," "professional," "realistic," "engineering," "mechanical," "assembly," "multi-part," "threaded," "geared," "hinged," "interlocking," "mechanism," among others. The 12 medium-complexity keywords include: "case," "enclosure," "bracket," "mount," "stand," "holder," among others.

#### 2.4 Product Knowledge Injection

The `product_lookup()` function searches the product library by matching prompt keywords against each template's keyword list. Matching templates provide real-world dimensions (e.g., iPhone 15 Pro: 146.6 × 70.6 × 8.25 mm), feature lists, and construction notes that are injected into the LLM prompt.

The `get_visual_knowledge()` function retrieves the category-level visual knowledge (visual_profile, build_strategy, recognition_features, position_map) and formats it as a structured text block appended to the system prompt.

#### 2.5 LLM Code Synthesis

The system prompt (145,000+ characters) contains the following major sections:

- **Coordinate System Convention** — Z-up, Z=0 ground plane, `centered=(True,True,False)` for main body boxes.
- **Feature Placement Recipe** — Explicit workplane-to-face mappings (e.g., "For features on ±X side faces, use `cq.Workplane('YZ')`").
- **slot2D/Cylinder Axis Mapping Table** — Critical reference: on "YZ" plane, `slot2D(a, b)` puts `a` along Y-axis and `b` along Z-axis; extrusion is along X-axis; cylinder axis is X-axis.
- **Product-Category Build Strategies** — Merged from the visual knowledge base.
- **Shape Variety Rules** — Mandate (e.g., "phone cases shall have ZERO `.box()` cutters").
- **Common Mistake Prevention** — Explicit wrong-vs-right examples for the most frequent LLM errors.
- **CadQuery API Selector Reference** — Face selectors (`'>Z'`, `'<Y'`), edge selectors (`'|Z'`, `'%Circle'`), combination syntax.
- **Self-Contained iPhone Case Example** — A complete ~150-line CadQuery iPhone case script demonstrating every convention.

The LLM returns a raw JSON object (no Markdown fences):

```json
{
  "parameters": [
    { "name": "width", "default": 75.0, "min": 60, "max": 100, "unit": "mm" }
  ],
  "code": "import cadquery as cq\n...\nresult = body",
  "explanation": {
    "design_intent": "...",
    "features_created": "..."
  }
}
```

Any Markdown fencing or extraneous text is stripped by the `_extract_json_from_response()` method using regex.

#### 2.6 Code Safety Validation

The `_validate_code_safety()` method enforces:

- **Import Allowlist** — Only `cadquery`, `cq`, `math`, `copy`, `cq_warehouse`, `numpy`, `np` are permitted. All `import X` and `from X import Y` statements are parsed via regex; any unlisted root module raises `ValueError`.
- **Forbidden Call Detection** — 12 forbidden function patterns (e.g., `eval(`, `exec(`, `open(`, `__import__(`, `getattr(`, `compile(`) are detected by substring matching.
- **Dunder Escape Detection** — Patterns like `__builtins__`, `__class__`, `__subclasses__`, `__bases__`, `__mro__` are blocked.
- **Forbidden Module Blocklist** — 17 dangerous modules (e.g., `os`, `sys`, `subprocess`, `socket`, `pickle`, `ctypes`) are explicitly blocked in import statements.
- **CadQuery Import Requirement** — Code must import `cadquery` or `cq_warehouse`.

#### 2.7 Five-Step Preprocessing Pipeline

Each step is a pure string-to-string transformation. The order is critical — later steps depend on earlier transformations:

**Step 1: `_strip_centered_from_non_box()`** — Removes `centered=` keyword arguments from `.extrude()`, `.rect()`, `.circle()`, and `.cylinder()` calls. Only `.box()` supports `centered=` in CadQuery; using it elsewhere causes runtime crashes.

**Step 2: `_fix_zero_dimensions()`** — Replaces `.extrude(0)` and `.extrude(0.0)` with `.extrude(0.1)` using regex substitution, preventing degenerate zero-thickness geometry.

**Step 3: `_ensure_result_assignment()`** — If the code lacks a `result = ...` assignment, scans for the last variable assigned from a set of 30+ common body-variable names (e.g., `body`, `case`, `housing`, `model`, `phone`, `bracket`) and appends `result = <variable>`.

**Step 4: `_clamp_fillet_radii()`** — Injects a `_auto_fillet_max = min(L, W, H) * 0.25` computation based on detected box dimensions, then wraps every `.fillet(r)` call in `min(r, _auto_fillet_max)`, preventing fillet radii from exceeding 25% of the smallest model dimension.

**Step 5: `_wrap_fillets_in_try_except()`** — Detects assignment statements containing `.fillet()` or `.chamfer()` that are not already inside `try/except` blocks, and wraps them:

```python
try:
    body = body.edges('|Z').fillet(5)
except:
    pass  # Auto-skip: fillet/chamfer too large for edge geometry
```

This is the critical safety net that prevents fillet crashes (the #1 CadQuery failure mode) from halting the entire build.

#### 2.8 Sandboxed Execution

Code is executed via Python's `exec()` within an isolated `namespace` dictionary containing:

- `cadquery` and `cq` (CadQuery library)
- `math` (standard math module)
- `copy` and `deepcopy` (object copying)
- `numpy` and `np` (if installed)
- All `cq_warehouse` parametric part classes (Nut, Screw, Washer, Bearing, Sprocket, Chain, Thread variants — 25+ classes)
- Parameter defaults (injected as top-level namespace variables)

No `__builtins__`, no filesystem access, no network access, no subprocess creation.

#### 2.9 Post-Execution Processing

**Ground-Plane Enforcement (`_ground_result()`)** — After all geometry operations complete, the method computes the bounding box of the finished model and translates the entire assembly by `(0, 0, -z_min)` so the bottom face sits exactly at Z=0. This is performed on the completed geometry (after all boolean cuts, fillets, and unions), ensuring perfect feature alignment regardless of how the LLM positioned the initial body.

**Multi-Solid Resolution (`_fix_multi_solid()`)** — If boolean operations inadvertently sever the solid into multiple disconnected bodies, the method enumerates all solids and retains only the one with the largest volume, recovering gracefully from topology errors.

**Quality Assessment (`_validate_output_quality()`)** — Computes volume, bounding box dimensions, dimensional ratios, and feature counts, producing a 1–10 quality score with categorized warnings and improvement suggestions.

#### 2.10 Code Completeness Analysis

The `analyze_code_completeness()` method performs programmatic inspection of the generated code without executing it:

- Counts geometric operations: cuts, unions, fillets, chamfers, shells, translates, cylinders, slot2Ds, holes.
- Classifies the product type from the prompt (phone_case, drone, laptop, game_controller, etc.).
- Evaluates against product-specific feature checklists. For example, a phone case must have:
  - At least 3 cut operations (camera, USB-C, buttons)
  - At least 1 shell operation
  - At least 1 translate (feature positioning)
  - Camera cutout presence
  - USB-C port presence
  - Button cutouts
  - Speaker holes
- Detects shape-variety violations (e.g., zero round cutters on an electronics product).
- Returns a structured analysis: `is_complete`, `missing_features[]`, `total_features`, `product_type`, `metrics`.

If the analysis finds missing features, the `enhance_incomplete_design()` method sends the code back to the LLM with specific instructions for each missing feature, including per-product-type shape variety guidance (e.g., "phone cases shall use `.slot2D()` for ports and `.cylinder()` for speaker holes, NEVER `.box()` cutters"). Up to two enhancement passes are performed automatically.

#### 2.11 16-Category Error Classification

When CadQuery execution fails, the error message is classified into one of 16 categories, each with a targeted repair strategy:

| Category                | Detection Keywords                | Targeted Fix Strategy                                            |
| ----------------------- | --------------------------------- | ---------------------------------------------------------------- |
| GEOMETRY_FILLET_CHAMFER | "fillet", "chamfer", "brep_api"   | Remove `%Circle` selectors, wrap in try/except, reduce radii 60% |
| GEOMETRY_SHELL          | "shell"                           | Reduce wall thickness, switch to manual cavity subtraction       |
| SKETCH_NOT_CLOSED       | "wire is not closed"              | Add `.close()` before sweep operations                           |
| SELECTOR_FAILED         | "selector", "no matching"         | Use broader selectors, fall back to `.transformed()` positioning |
| CURVE_TANGENT           | "tangent", "spline", "derivative" | Replace splines with linear segments                             |
| REVOLVE_AXIS            | "null vector", "revolve"          | Ensure profile stays on one side of revolve axis                 |
| MATH_ERROR              | "division by zero", "math domain" | Add safe guards: `max(value, 0.1)`                               |
| LOFT_FAILED             | "loft", "cross-section"           | Switch to extrude + taper with boolean unions                    |
| BOOLEAN_FAILED          | "boolean", "cut", "overlap"       | Increase cutter size by 1–2mm per direction                      |
| WRONG_PARAMETER         | "unexpected keyword", "centered"  | Remove `centered=` from non-`.box()` calls                       |
| SWEEP_FAILED            | "sweep", "pipe"                   | Reduce profile size, fillet path corners                         |
| WORKPLANE_STACK         | "stack", "pending wires"          | Clear pending operations before new workplanes                   |
| OCC_KERNEL_ERROR        | "OCC", "BRep"                     | General geometry simplification                                  |
| ATTRIBUTE_ERROR         | "has no attribute"                | Fix CadQuery API usage                                           |
| TYPE_ERROR              | "type error"                      | Fix variable type mismatches                                     |
| EMPTY_RESULT            | "empty", "no solid"               | Ensure geometry produces a valid solid                           |
| NAME_ERROR              | "name error", "not defined"       | Fix undefined variable references                                |
| GENERAL                 | (fallback)                        | Progressive simplification                                       |

#### 2.12 Five-Phase Graduated Self-Healing

The self-healing system escalates repair aggressiveness over up to 15 attempts:

**Phase 1 — Targeted (attempt 1):** The classified error and targeted fix instructions are sent to the LLM with the instruction to fix only the failing line/operation and reduce fillet/chamfer radii by 30%.

**Phase 2 — Conservative (attempts 2–3):** Instruct the LLM to reduce all radii by 60%, wrap all fillet/chamfer operations in try/except, and simplify any spline constructions.

**Phase 3 — Aggressive (attempts 4–5):** Instruct the LLM to strip all fillets, chamfers, and shell operations entirely, replace loft operations with simple extrusions, and reduce the model to basic boolean operations.

**Phase 4 — Rewrite (attempts 6–7):** Instruct the LLM to rewrite the failing section of code from scratch using only safe primitive operations (box, cylinder, extrude, cut, union).

**Phase 5 — Nuclear (attempts 8+):** Instruct the LLM to rebuild the entire model from scratch using only boxes and cylinders, abandoning all complex geometry, to produce a working (if simplified) representation of the requested product.

Each phase sends the current (failed) code, the error message, the error classification, the phase-specific repair instructions, and the original user prompt back to the LLM.

#### 2.13 Parametric Script Generation and Marker-Based Rebuild

The parametric script follows this structure:

```python
# ═══════════════════════════════════════════════════════════════
# PARAMETERS
# ═══════════════════════════════════════════════════════════════
width = 75.0   # mm (min: 60, max: 100)
depth = 12.0   # mm (min: 8, max: 20)
...

# ═══════════════════════════════════════════════════════════════
# GEOMETRY GENERATION
# ═══════════════════════════════════════════════════════════════
import cadquery as cq
body = cq.Workplane("XY").box(width, depth, height, centered=(True,True,False))
...
result = body

# ═══════════════════════════════════════════════════════════════
# EXPORT
# ═══════════════════════════════════════════════════════════════
```

The `rebuild_with_parameters()` method:

1. Locates the parametric script file by build ID.
2. Reads the script content.
3. Uses `str.find()` on the exact marker strings `"# GEOMETRY GENERATION"` and `"# EXPORT"` to extract only the geometry code section.
4. Coerces all incoming parameter values to `float` (handling frontend string inputs).
5. Injects the updated parameter values into the execution namespace.
6. Applies the identical five-step preprocessing pipeline.
7. Executes the geometry section via `exec()`.
8. Grounds the result and exports new STEP/STL files.

This achieves instant geometry regeneration with zero LLM cost.

#### 2.14 Streaming Architecture

The SSE (Server-Sent Events) stream delivers structured JSON events:

```
data: {"step": 1, "message": "Searching product library...", "status": "active"}
data: {"step": 1, "message": "Product library checked", "status": "done"}
data: {"step": 2, "message": "Designing with Claude AI...", "status": "active"}
data: {"step": 2, "message": "AI design complete", "status": "done"}
data: {"step": 3, "message": "Checking design completeness...", "status": "active"}
data: {"step": 4, "message": "Building 3D geometry...", "status": "active"}
data: {"step": 4, "message": "🔧 Self-healing — attempt 2...", "status": "active", "healing": {...}}
data: {"step": 5, "message": "Files exported", "status": "done"}
data: {"step": 6, "message": "Build complete!", "status": "complete", "result": {...}}
```

The frontend `useBuild` hook maps steps to progress percentages (step 1 → 10%, step 2 → 40%, step 3 → 55%, step 4 → 75%, step 5 → 90%, step 6 → 100%) and renders a real-time progress indicator.

#### 2.15 Modification Flow (Iterative Design Editing)

When a user requests a modification to an existing design:

1. The frontend sends the full `previousDesign` object including the current CadQuery code, parameters, and explanation.
2. The AI service uses a lightweight edit system prompt (~2KB vs ~145KB for new designs).
3. The LLM receives both the existing code and the modification instruction, editing only the relevant portions.
4. The same preprocessing pipeline, safety validation, and self-healing mechanisms apply.
5. The result replaces the current design in the frontend state, and a new version entry is added to the version history.

#### 2.16 Slot2D Axis Mapping System

A critical innovation for correct feature orientation on 3D models. The system encodes and enforces the following CadQuery workplane semantics:

| Workplane | `slot2D(a, b)`           | `a` maps to | `b` maps to | Extrusion Axis | Cylinder Axis |
| --------- | ------------------------ | ----------- | ----------- | -------------- | ------------- |
| "XY"      | `slot2D(X_span, Y_span)` | X axis      | Y axis      | Z              | Z             |
| "XZ"      | `slot2D(X_span, Z_span)` | X axis      | Z axis      | Y              | Y             |
| "YZ"      | `slot2D(Y_span, Z_span)` | Y axis      | Z axis      | X              | X             |

This mapping is critical for correct button orientation on phones and wearables: a vertical button on the ±X side face requires `cq.Workplane("YZ").slot2D(depth, height)` where `depth` (small, Y-axis) comes first and `height` (tall, Z-axis) comes second. Reversing the parameters produces a horizontal slit.

---

### 3. PCB Design Integration

The system includes an optional PCB (Printed Circuit Board) design service that:

1. Accepts a `pcb_spec` object from the LLM containing component list, board dimensions, and routing requirements.
2. Generates a 3D PCB model with placed components.
3. Exports KiCad-compatible `.kicad_pcb` files.
4. Integrates the PCB model with the enclosure geometry for unified CAD export.

---

### 4. Collaboration and Version Control

The system supports:

- **Version History** — Each build is versioned with a unique version ID, timestamp, label, and complete state snapshot (design, code, parameters).
- **Real-Time Collaboration** — WebSocket-based collaboration rooms where multiple users can view and manipulate a shared 3D scene.
- **Project Persistence** — Builds are saved to Supabase with project-level organization, enabling build history browsing and project restoration.

---

## CLAIMS

### Independent Claims

**Claim 1.** A computer-implemented method for generating a three-dimensional parametric solid model from a natural language description, the method comprising:

(a) receiving, at a server, a natural language prompt describing a desired physical product;

(b) consulting a product knowledge base comprising (i) a product library containing templates with real-world dimensions for a plurality of product categories, and (ii) a visual knowledge base containing per-category construction recipes with axis assignments, workplane-to-face mappings, and feature position maps;

(c) transmitting the natural language prompt, matched product knowledge, and a system prompt encoding coordinate system conventions and CAD API patterns to a large language model;

(d) receiving from the large language model a structured response comprising a list of user-adjustable parameters with value ranges, executable parametric solid-modeling code, and a design explanation;

(e) validating the executable code against an import allowlist and a forbidden-operation blocklist;

(f) applying an ordered preprocessing pipeline to the validated code, the pipeline comprising at least: stripping invalid keyword arguments from non-applicable API calls, replacing zero-dimension geometry with safe minimums, ensuring result variable assignment, and injecting radius-clamping guards on fillet and chamfer operations;

(g) executing the preprocessed code in a sandboxed namespace to produce a solid model;

(h) translating the solid model so that its bounding-box bottom aligns with a ground plane at Z=0;

(i) exporting the solid model to at least one industry-standard CAD format; and

(j) transmitting the exported model and parameter list to a client for display and parametric manipulation.

**Claim 2.** A computer-implemented method for self-healing geometric code failures during automated CAD model generation, the method comprising:

(a) receiving executable solid-modeling code generated by a large language model;

(b) executing the code in a sandboxed environment and detecting a runtime geometric error;

(c) classifying the error into one of a plurality of predefined error categories based on keyword analysis of the error message;

(d) determining a healing phase based on the current attempt number within a maximum attempt limit, wherein the healing phases escalate in aggressiveness from targeted single-line repair through progressive simplification to complete model reconstruction;

(e) transmitting the failed code, classified error, and phase-specific repair instructions to the large language model to obtain repaired code; and

(f) repeating steps (b) through (e) with progressively more aggressive healing phases until execution succeeds or the maximum attempt limit is reached.

**Claim 3.** A computer-implemented method for parametric rebuild of a three-dimensional solid model without invoking a large language model, the method comprising:

(a) storing a parametric script containing comment-delimited sections including at least a parameter section and a geometry generation section, wherein the sections are delimited by exact string markers;

(b) receiving updated parameter values from a client interface;

(c) parsing the parametric script to extract the geometry generation section using string search on the exact markers;

(d) injecting the updated parameter values into a sandboxed execution namespace;

(e) applying a preprocessing pipeline to the geometry code;

(f) executing the preprocessed geometry code in the sandboxed namespace to produce an updated solid model; and

(g) exporting the updated model and transmitting it to the client without any large language model invocation.

**Claim 4.** A system for converting natural language descriptions to three-dimensional parametric solid models, the system comprising:

(a) a backend server configured to receive natural language prompts via HTTP API endpoints;

(b) a product knowledge subsystem comprising a product library with real-world dimensional templates and a visual knowledge base with per-category construction recipes including axis assignments and feature position maps;

(c) an AI code synthesis service configured to transmit prompts augmented with product knowledge to a large language model and receive structured JSON responses containing parametric code;

(d) a code safety validator configured to enforce an import allowlist and detect forbidden operations;

(e) a preprocessing engine configured to apply an ordered pipeline of code transformations including API argument correction, zero-dimension repair, result assignment, fillet radius clamping, and fillet try/except wrapping;

(f) a sandboxed execution engine configured to execute preprocessed code in an isolated namespace and enforce ground-plane alignment;

(g) a self-healing engine configured to classify geometric errors into categories and escalate repair strategies across multiple phases;

(h) a completeness analyzer configured to evaluate generated code against product-specific feature checklists and trigger iterative enhancement;

(i) a parametric rebuild engine configured to update geometry from parameter changes without LLM invocation using marker-delimited script parsing;

(j) an export engine configured to generate STEP and STL files; and

(k) a browser-based three-dimensional visualization client configured to render the exported model and provide parametric slider controls.

### Dependent Claims

**Claim 5.** The method of Claim 1, wherein the system prompt transmitted to the large language model exceeds 100,000 characters and encodes a slot2D/cylinder axis mapping table specifying the relationship between workplane selection and the geometric axes to which slot2D parameters map.

**Claim 6.** The method of Claim 1, further comprising:

programmatically analyzing the generated code against a product-specific feature checklist to identify missing features; and

if missing features are detected, transmitting the code back to the large language model with specific instructions for each missing feature, including per-product shape variety guidance.

**Claim 7.** The method of Claim 6, wherein the feature checklist analysis is performed up to two iterative passes, each pass re-analyzing the enhanced code and triggering further enhancement if features remain missing.

**Claim 8.** The method of Claim 2, wherein the plurality of predefined error categories comprises at least: GEOMETRY_FILLET_CHAMFER, GEOMETRY_SHELL, SKETCH_NOT_CLOSED, SELECTOR_FAILED, CURVE_TANGENT, REVOLVE_AXIS, MATH_ERROR, LOFT_FAILED, BOOLEAN_FAILED, WRONG_PARAMETER, SWEEP_FAILED, and GENERAL.

**Claim 9.** The method of Claim 2, wherein the healing phases comprise:

a first phase applying a targeted fix to the failing line with a 30% reduction in fillet radii;

a second phase applying conservative fixes including 60% radius reduction and try/except wrapping;

a third phase aggressively stripping all fillet, chamfer, and shell operations;

a fourth phase rewriting the failing section using only safe primitive operations; and

a fifth phase rebuilding the entire model from scratch using only box and cylinder primitives.

**Claim 10.** The method of Claim 1, wherein the preprocessing pipeline further comprises wrapping all fillet and chamfer assignment statements in try/except blocks that silently skip the operation upon failure, such that the model is always producible even when individual cosmetic operations fail.

**Claim 11.** The method of Claim 1, further comprising detecting that the solid model contains multiple disconnected solids and retaining only the solid with the largest volume.

**Claim 12.** The method of Claim 3, wherein the exact string markers comprise Unicode box-drawing characters forming a visually distinct comment block that is parseable by `str.find()`.

**Claim 13.** The method of Claim 1, further comprising:

computing a SHA-256 hash of the normalized natural language prompt;

looking up the hash in a bounded cache; and

if a cache hit is found and the corresponding output files exist, returning the cached result without invoking the large language model or executing any geometry code.

**Claim 14.** The method of Claim 1, wherein transmitting the exported model to the client comprises streaming Server-Sent Events (SSE) with structured JSON payloads reporting step-by-step progress through each pipeline phase including product knowledge lookup, AI synthesis, completeness checking, geometry execution, self-healing attempts, and file export.

**Claim 15.** The system of Claim 4, wherein the AI code synthesis service is configured to route requests to multiple LLM providers including at least Anthropic and OpenAI based on a model identifier prefix, converting message formats between provider-specific APIs through a unified streaming interface.

**Claim 16.** The system of Claim 4, wherein the AI code synthesis service implements adaptive token allocation that classifies prompt complexity based on keyword matching and word count, allocating higher token limits and lower temperature values to high-complexity prompts.

**Claim 17.** The system of Claim 4, further comprising a PCB design service configured to generate printed circuit board models and KiCad-compatible files that integrate with enclosure geometry.

**Claim 18.** The system of Claim 4, wherein the persistence layer implements graceful degradation such that each external service — database, object storage, format conversion — activates only when its corresponding software package and credentials are present, and the system operates with full core functionality when none are configured.

**Claim 19.** The method of Claim 1, wherein the sandboxed namespace pre-loads parametric mechanical part classes including fasteners, bearings, sprockets, chains, and thread profiles, enabling the large language model to specify standard mechanical components by class name and parameters.

**Claim 20.** The method of Claim 1, further comprising:

detecting that the natural language prompt is a modification request by the presence of a previous design object containing existing parametric code;

using a lightweight edit system prompt substantially smaller than the full design system prompt; and

instructing the large language model to modify only the relevant portions of the existing code.

---

## ABSTRACT

A system and method for converting natural language descriptions into parametric three-dimensional solid models. A user submits a free-form text prompt describing a desired product. The system consults a product knowledge base of real-world dimensions and per-category construction recipes, then transmits the augmented prompt to a large language model that generates structured JSON containing user-adjustable parameters and executable CadQuery solid-modeling code. The code passes through import-allowlist safety validation, a five-step preprocessing pipeline (API correction, zero-dimension repair, result assignment, fillet radius clamping, fillet try/except wrapping), and sandboxed execution. A post-execution ground-plane enforcer aligns the model to Z=0. A 16-category error classifier feeds a five-phase graduated self-healing system that escalates from targeted single-line repair through complete model reconstruction over up to 15 attempts. A programmatic completeness analyzer evaluates code against product-specific feature checklists and triggers iterative LLM enhancement. Generated parametric scripts use comment markers enabling instant geometry rebuilds from slider input without further LLM invocation. The system streams step-by-step progress via SSE to a browser-based Three.js visualization client supporting multi-product workspaces, parametric manipulation, and multi-format CAD export (STEP, STL).

---

## DRAWINGS DESCRIPTION

_(Formal patent drawings would be prepared by a patent illustrator. The following describes the required figures.)_

**FIG. 1** — System architecture diagram showing the client, backend server, AI service, CAD engine, product knowledge base, and export pipeline.

**FIG. 2** — Data flow diagram of the complete natural-language-to-CAD pipeline from prompt ingestion through product lookup, LLM code synthesis, safety validation, preprocessing, execution, ground-plane enforcement, completeness analysis, and export.

**FIG. 3** — Flowchart of the five-phase graduated self-healing system showing error classification, phase determination, repair strategy selection, and escalation logic.

**FIG. 4** — Detail of the five-step preprocessing pipeline showing each transformation stage and its input/output.

**FIG. 5** — Diagram of the parametric rebuild system showing marker-based script parsing, parameter injection, and geometryregeneration without LLM invocation.

**FIG. 6** — Slot2D axis mapping reference showing the relationship between workplane selection (XY, XZ, YZ) and the geometric axes to which slot2D parameters and cylinder axes map.

**FIG. 7** — Code completeness analysis flow showing product-type classification, feature checklist evaluation, and iterative enhancement passes.

**FIG. 8** — SSE streaming timeline showing the sequence of events from build request through each pipeline phase to final result delivery.

**FIG. 9** — Screenshot of the browser-based 3D visualization interface showing the rendered model, parameter panel with sliders, prompt input, and export controls.

**FIG. 10** — Error classification decision tree mapping error message keywords to the 16 predefined categories.

---

## INVENTOR(S)

_(To be completed by the applicant.)_

---

## ASSIGNEE

_(To be completed by the applicant.)_

---

## PRIORITY DATE

_(Date of first filing — to be completed by the applicant.)_

---

_This patent application was generated based on the inventa.AI platform source code. An intellectual property attorney should review and refine this document before filing with any patent office. Specific formatting, drawings, and oath/declaration requirements vary by jurisdiction (USPTO, EPO, WIPO, etc.)._
