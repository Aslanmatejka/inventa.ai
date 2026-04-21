from ..core.metadata import ExampleMetadata

metadata = ExampleMetadata(
    id="aquarium_tank",
    name="Glass Aquarium Tank",
    category="aquarium",
    keywords=["aquarium", "fish", "tank", "glass", "pet", "terrarium"],
    description="Rectangular glass aquarium tank with hollow interior and top opening.",
    techniques=["shell_cavity"],
    nominal_dimensions_mm={"length": 600.0, "width": 300.0, "height": 360.0, "wall": 6.0},
    difficulty="easy",
)

code = '''import cadquery as cq

length = 600.0
width = 300.0
height = 360.0
wall = 6.0

outer = cq.Workplane("XY").box(length, width, height, centered=(True, True, False))
inner = (
    cq.Workplane("XY", origin=(0, 0, wall))
    .box(length - 2 * wall, width - 2 * wall, height, centered=(True, True, False))
)
body = outer.cut(inner)

# Top rim band (small reinforcement)
rim = (
    cq.Workplane("XY", origin=(0, 0, height - 5))
    .box(length, width, 5, centered=(True, True, False))
)
rim_hole = (
    cq.Workplane("XY", origin=(0, 0, height - 6))
    .box(length - 2 * wall - 6, width - 2 * wall - 6, 7, centered=(True, True, False))
)
rim = rim.cut(rim_hole)
body = body.union(rim)

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
