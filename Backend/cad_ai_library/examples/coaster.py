from ..core.metadata import ExampleMetadata

metadata = ExampleMetadata(
    id="coaster",
    name="Drink Coaster",
    category="accessory",
    keywords=["coaster", "drink", "cup", "mat", "pad"],
    description="Round coaster with shallow recess and grip ring on bottom.",
    techniques=["guarded_fillet", "shell_cavity"],
    nominal_dimensions_mm={"diameter": 95.0, "thickness": 6.0, "recess_depth": 1.2},
    difficulty="easy",
)

code = '''import cadquery as cq

diameter = 95.0
thick = 6.0
recess_depth = 1.2
lip = 3.0

body = cq.Workplane("XY").circle(diameter / 2.0).extrude(thick)

# Top recess
recess = (
    cq.Workplane("XY", origin=(0, 0, thick - recess_depth))
    .circle(diameter / 2.0 - lip)
    .extrude(recess_depth + 0.1)
)
body = body.cut(recess)

# Bottom grip groove
groove = (
    cq.Workplane("XY")
    .circle(diameter / 2.0 - lip - 4.0)
    .circle(diameter / 2.0 - lip - 6.0)
    .extrude(0.8)
)
body = body.cut(groove)

try:
    body = body.edges(">Z or <Z").fillet(min(1.0, thick * 0.15))
except Exception:
    pass

result = body
'''
