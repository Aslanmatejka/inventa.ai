from ..core.metadata import ExampleMetadata

metadata = ExampleMetadata(
    id="yoga_block",
    name="Yoga Block",
    category="fitness",
    keywords=["yoga", "block", "foam", "fitness", "exercise", "brick"],
    description="Rectangular yoga block with softly rounded edges and corners.",
    techniques=["guarded_fillet"],
    nominal_dimensions_mm={"length": 230.0, "width": 150.0, "height": 75.0},
    difficulty="easy",
)

code = '''import cadquery as cq

length = 230.0
width = 150.0
height = 75.0

body = cq.Workplane("XY").box(length, width, height, centered=(True, True, False))
try:
    body = body.edges().fillet(12.0)
except Exception:
    pass

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
