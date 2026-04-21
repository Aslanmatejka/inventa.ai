from ..core.metadata import ExampleMetadata

metadata = ExampleMetadata(
    id="clip_board",
    name="Clipboard",
    category="accessory",
    keywords=["clipboard", "board", "office", "stationery", "A4"],
    description="A4 clipboard base plate with two mounting holes for the clip.",
    techniques=["guarded_fillet", "cbore_hole"],
    nominal_dimensions_mm={"length": 310.0, "width": 225.0, "thickness": 4.0},
    difficulty="easy",
)

code = '''import cadquery as cq

length = 310.0
width = 225.0
thick = 4.0

body = cq.Workplane("XY").box(length, width, thick, centered=(True, True, False))
try:
    body = body.edges("|Z").fillet(6.0)
except Exception:
    pass
try:
    body = body.edges(">Z or <Z").fillet(0.8)
except Exception:
    pass

# Hang hole near top edge
body = (
    body.faces(">Z").workplane()
    .center(0, width / 2.0 - 12.0)
    .hole(6.0)
)

# Two rivet holes for the clip
body = (
    body.faces(">Z").workplane()
    .pushPoints([(-30.0, width / 2.0 - 30.0), (30.0, width / 2.0 - 30.0)])
    .hole(3.2)
)

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
