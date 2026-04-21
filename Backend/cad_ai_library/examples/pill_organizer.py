from ..core.metadata import ExampleMetadata

metadata = ExampleMetadata(
    id="pill_organizer",
    name="Weekly Pill Organizer",
    category="medical",
    keywords=["pill", "organizer", "medicine", "weekly", "tablet", "compartment"],
    description="7-compartment weekly pill organizer with labeled dividers.",
    techniques=["shell_cavity", "guarded_fillet"],
    nominal_dimensions_mm={"length": 175.0, "width": 35.0, "height": 22.0, "wall": 2.0},
    difficulty="easy",
)

code = '''import cadquery as cq

length = 175.0
width = 35.0
height = 22.0
wall = 2.0
compartments = 7

body = cq.Workplane("XY").box(length, width, height, centered=(True, True, False))
try:
    body = body.edges("|Z").fillet(3.0)
except Exception:
    pass

# Inner pocket
pocket = (
    cq.Workplane("XY", origin=(0, 0, wall))
    .box(length - 2 * wall, width - 2 * wall, height - wall + 0.1,
         centered=(True, True, False))
)
body = body.cut(pocket)

# Dividers between compartments
cell = (length - 2 * wall) / compartments
for i in range(1, compartments):
    x = -length / 2.0 + wall + cell * i
    div = (
        cq.Workplane("XY", origin=(x - 0.5, 0, wall))
        .box(1.0, width - 2 * wall, height - wall - 2, centered=(False, True, False))
    )
    body = body.union(div)

result = body
'''
