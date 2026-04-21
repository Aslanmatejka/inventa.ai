"""
CadQuery Reliability Doctrine
Distilled from real failure modes observed in production builds.

This module provides a single injectable text block that gets added to the
Claude system prompt on every design request. Each rule is derived from
an actual bug that caused a model to fail silently (negative volume, collapsed
solid, floating parts, etc.) — NOT theoretical guidelines.

Keep this file small and high-signal. Every sentence should save a build.
"""


CADQUERY_DOCTRINE = """
═══════════════════════════════════════════════════════════════════════
 CADQUERY RELIABILITY DOCTRINE — MANDATORY RULES
═══════════════════════════════════════════════════════════════════════
These rules are distilled from real production failures. Violating any
of them produces silent degenerate geometry (negative volume, collapsed
solid, floating parts) that will be REJECTED by the degenerate-geometry
validator and you'll have to rebuild.

━━━ RULE 1 — REVOLVE PROFILES MUST STAY ON ONE SIDE OF THE AXIS ━━━
When you .revolve() a wire around (0,0,0)→(0,1,0), the profile MUST
live entirely in X ≥ 0. A single point at X < 0 produces inverted
normals and NEGATIVE VOLUME.

✅ SAFE revolve profile (all X ≥ 0, closes at axis):
    cq.Workplane("XZ").moveTo(0, 0).lineTo(R, 0).lineTo(R, H) \\
        .lineTo(0, H).close().revolve(360, (0,0,0), (0,1,0))

❌ NEVER: spline control points that cross X = 0.
❌ NEVER: a profile that self-intersects (check you don't go backwards).
❌ AVOID: .spline() inside a .revolve() profile unless you MUST — splines
   silently self-intersect on tight curves. Prefer .threePointArc(),
   .radiusArc(), or a chain of .lineTo() approximations.

━━━ RULE 2 — PREFER SIMPLE PRIMITIVES FOR BODIES ━━━
For any request, start with the SIMPLEST shape that matches:
  • Cylindrical body  → .cylinder(h, r) or .circle(r).extrude(h)
  • Box / case        → .box(x, y, z, centered=(True, True, False))
  • Tapered cylinder  → .circle(r1).workplane(offset=h).circle(r2).loft()
  • Sphere / dome     → .sphere(r)
Only reach for .revolve() with a custom profile when tapered cylinders
and spheres cannot express the shape. Only reach for .sweep() with a
custom path for clearly swept features (handles, pipes, cables).

━━━ RULE 3 — THREADS: USE SIMPLE RINGS, NOT HELIX SWEEPS ━━━
Real helical threads via .makeHelix() + .sweep() crash or produce
degenerate geometry ~40% of the time. For any threaded feature
(bottle cap, lid, screw boss, etc.) use one of these instead:
  (a) A plain cylindrical boss with matching inner cavity on the mating
      part (friction fit or snap-fit).
  (b) A few horizontal rings (.cylinder(thickness, r_outer) cut by
      .cylinder(thickness, r_inner)) stacked at pitch spacing — this
      LOOKS like a thread in render without the helix failure mode.
Never generate .makeHelix() sweeps unless the user explicitly says
"functional thread" or "printable thread".

━━━ RULE 4 — SWEEP PATHS MUST CONNECT TO THE PROFILE ━━━
A .sweep() needs the profile plane to be PERPENDICULAR to the path
start tangent AND the profile center must sit on the path start point.
If they don't align, the sweep produces a floating sliver 50mm away.

✅ For a handle: define the path in XZ (top_r, z_high) → arc → (top_r, z_low)
   and the profile on YZ centered at (top_r, z_high) with .circle(r).
❌ NEVER translate the result of .sweep() by more than a few mm — if
   you feel you need a translate, your profile was in the wrong place.

━━━ RULE 5 — EVERY .cut() MUST SUBTRACT LESS THAN THE BODY ━━━
A cutter wider/taller than the remaining body will erase everything.
Before every .cut(cutter) compute:
    cutter volume ≤ 0.35 × body volume
If the cutter is deep or wide, it is probably a MISTAKE — replace
with a shallower/narrower version.

━━━ RULE 6 — EVERY .union() PART MUST OVERLAP THE BODY ━━━
Two solids with a tiny gap (even 0.01mm) union into two disconnected
solids — the model FAILS the multi-solid check. Make the joining part
penetrate the body by ≥0.5mm:
    handle_attachment_x = body_radius - 0.5   # penetrate inward
    NOT body_radius + 0.5                     # gap!

━━━ RULE 7 — FILLETS: ALWAYS GUARDED, ALWAYS LAST ━━━
Every .fillet()/.chamfer() MUST be wrapped in try/except. Place fillets
AFTER all .cut()/.union() operations, NEVER before .shell().
    try:
        body = body.edges("|Z").fillet(min(r, smallest_dim * 0.15))
    except Exception:
        pass

━━━ RULE 8 — SHELL IS FINAL ━━━
.shell() is VERY fragile. It must be the LAST body operation before
you add external fillets. Never shell a body that already has fillets
on the face you're shelling. Never shell after a union with a thin part.

━━━ RULE 9 — DO NOT CHAIN MORE THAN 3 BOOLEANS ON A SPLINE BODY ━━━
A body created from .revolve() of a .spline() profile is fragile.
Every additional .cut() or .union() increases the chance of collapse.
If you need many features on a curved body, create the curved body
with LOFT between circles (far more robust) instead of SPLINE revolve.

━━━ RULE 10 — ALWAYS ASSIGN `result` AND VERIFY DIMENSIONS ━━━
The last line MUST be `result = <your_body>`. The final bounding box
should be within 20% of the largest declared parameter. Example:
    body_height = 240.0  →  expect bbox z ≈ 240.0 (±48mm)
If your model uses body_height=240 but your bbox will be ~10mm, you
have a bug — rebuild before returning.
═══════════════════════════════════════════════════════════════════════
"""


def get_doctrine() -> str:
    """Return the reliability doctrine as an injectable prompt block."""
    return CADQUERY_DOCTRINE
