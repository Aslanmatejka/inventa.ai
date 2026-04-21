from ..core.metadata import ExampleMetadata

metadata = ExampleMetadata(
    id="tape_measure",
    name="Tape Measure",
    category="tool",
    keywords=["tape", "measure", "measuring", "tape measure", "reel", "tool"],
    description="Pocket tape measure housing with belt clip and tape slot.",
    techniques=["guarded_fillet", "boolean_cut"],
    nominal_dimensions_mm={"width": 80.0, "height": 85.0, "depth": 40.0},
    difficulty="easy",
)

code = '''import cadquery as cq

w = 80.0
h = 85.0
d = 40.0

body = cq.Workplane("XY").box(w, d, h, centered=(True, True, False))
try:
    body = body.edges("|Y").fillet(12.0)
except Exception:
    pass
try:
    body = body.edges("|X or |Z").fillet(3.0)
except Exception:
    pass

# Tape slot (front face)
slot = (cq.Workplane("XZ").workplane(offset=-d/2 - 1)
        .center(0, 10).rect(28, 2.5).extrude(5))
body = body.cut(slot)

# Belt clip on back
clip = (cq.Workplane("XZ").workplane(offset=d/2)
        .center(0, h/2 - 15).rect(24, 50).extrude(6))
body = body.union(clip)

# Side button
btn = (cq.Workplane("YZ").workplane(offset=w/2 - 1)
       .center(0, 18).circle(7).extrude(4))
body = body.union(btn)

result = body

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
