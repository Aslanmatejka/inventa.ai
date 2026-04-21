from ..core.metadata import ExampleMetadata

metadata = ExampleMetadata(
    id="cochlear_implant",
    name="Cochlear Implant Processor",
    category="prosthetic",
    keywords=["cochlear", "implant", "hearing", "hearing aid", "deaf", "sound processor", "behind the ear", "bte", "audiology", "prosthetic"],
    description="Behind-the-ear cochlear implant sound processor with earhook and magnetic transmitter coil.",
    techniques=["boolean_union", "guarded_fillet"],
    nominal_dimensions_mm={"body_length": 45.0, "body_width": 12.0, "body_height": 28.0},
    difficulty="medium",
)

code = '''import cadquery as cq

# BTE processor body (rounded bean shape behind ear)
body_pts = [
    (0, 0), (8, -4), (36, -2), (44, 4), (46, 14),
    (40, 24), (24, 30), (8, 28), (0, 22),
]
body = (cq.Workplane("XZ").polyline(body_pts).close().extrude(12))
try:
    body = body.edges("|Y").fillet(3.0)
except Exception:
    pass

# Battery door end (raised rim)
batt = (cq.Workplane("YZ").workplane(offset=44)
        .center(6, 14).rect(10, 22).extrude(2))
body = body.union(batt)

# Microphone port dots
for y in [18, 22]:
    mic = (cq.Workplane("YZ").workplane(offset=30)
           .center(6, y).circle(1.2).extrude(1))
    body = body.cut(mic)

# Ear hook (curved tube from front of body down and around)
hook_pts = [(0, 15), (-6, 10), (-14, 2), (-22, -8), (-24, -20), (-18, -30)]
hook = (cq.Workplane("XZ").polyline(hook_pts).close()
        .extrude(6).translate((0, 3, 0)))
try:
    hook = hook.edges("|Y").fillet(2.5)
except Exception:
    pass

# Transmitter coil (external magnetic puck, connected via thin cable)
coil = (cq.Workplane("XY").workplane(offset=45)
        .center(-25, 40).circle(16).extrude(6))
coil_inner = (cq.Workplane("XY").workplane(offset=47)
              .center(-25, 40).circle(6).extrude(4))
coil = coil.cut(coil_inner)

# Thin cable linking body to coil (long thin box)
cable = (cq.Workplane("XY").workplane(offset=10)
         .center(-10, 30).box(32, 2, 2, centered=(True, True, False)))

full = body.union(hook).union(coil).union(cable)

try:
    full = full.edges("|Y").fillet(0.8)
except Exception:
    pass

result = full

# --- Modern finishing pass (guarded) ---
try:
    result = result.edges("|Z").fillet(1.2)
except Exception:
    pass
try:
    result = result.faces(">Z").edges().chamfer(0.5)
except Exception:
    pass
try:
    result = result.faces("<Z").edges().fillet(0.8)
except Exception:
    pass
'''
