from ..core.metadata import ExampleMetadata

metadata = ExampleMetadata(
    id="pen_holder",
    name="Pen Holder",
    category="organizer",
    keywords=["pen", "pencil", "holder", "cup", "desk", "office", "stationery"],
    description="Cylindrical pen holder with weighted base and inner cavity.",
    techniques=["shell_cavity", "guarded_fillet"],
    nominal_dimensions_mm={"diameter": 80.0, "height": 100.0, "wall": 3.0},
    difficulty="easy",
)

code = '''import cadquery as cq

diameter = 80.0
height = 100.0
wall = 3.0
base_thick = 6.0

body = cq.Workplane("XY").circle(diameter / 2.0).extrude(height)

# Soften top edge
try:
    body = body.edges(">Z").fillet(min(2.0, wall * 0.45))
except Exception:
    pass

# Inner cavity (keep base_thick at bottom)
cavity = (
    cq.Workplane("XY", origin=(0, 0, base_thick))
    .circle(diameter / 2.0 - wall)
    .extrude(height - base_thick + 1)
)
body = body.cut(cavity)

result = body
'''
