from ..core.metadata import ExampleMetadata

metadata = ExampleMetadata(
    id="tray",
    name="Serving Tray",
    category="container",
    keywords=["tray", "serving", "platter", "catchall", "flat"],
    description="Rectangular tray with raised lip and filleted inner corners.",
    techniques=["shell_cavity", "guarded_fillet", "grounding"],
    nominal_dimensions_mm={"length": 300.0, "width": 200.0, "height": 25.0, "wall": 4.0},
    difficulty="easy",
)

code = '''import cadquery as cq

length = 300.0
width = 200.0
height = 25.0
wall = 4.0
rim_fillet = 3.0

body = cq.Workplane("XY").box(length, width, height, centered=(True, True, False))

# Outer edge fillet for comfort
try:
    body = body.edges("|Z").fillet(min(8.0, width * 0.08))
except Exception:
    pass

# Hollow out
body = body.faces(">Z").shell(-wall)

# Soften the top rim
try:
    body = body.edges(">Z").fillet(min(rim_fillet, wall * 0.45))
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
