from ..core.metadata import ExampleMetadata

metadata = ExampleMetadata(
    id="soap_dish",
    name="Soap Dish",
    category="container",
    keywords=["soap", "dish", "bathroom", "shower", "drain"],
    description="Rectangular soap dish with raised ribs and drainage slots.",
    techniques=["shell_cavity", "guarded_fillet"],
    nominal_dimensions_mm={"length": 120.0, "width": 80.0, "height": 20.0, "wall": 3.0},
    difficulty="easy",
)

code = '''import cadquery as cq

length = 120.0
width = 80.0
height = 20.0
wall = 3.0
rib_count = 5
rib_w = 4.0

body = cq.Workplane("XY").box(length, width, height, centered=(True, True, False))
try:
    body = body.edges("|Z").fillet(min(6.0, width * 0.08))
except Exception:
    pass
body = body.faces(">Z").shell(-wall)

# Raised ribs on the floor (to lift the soap)
for i in range(rib_count):
    y = -width / 2.0 + wall + (width - 2 * wall) * (i + 0.5) / rib_count
    rib = (
        cq.Workplane("XY", origin=(0, y, wall))
        .rect(length - 2 * wall - 4, rib_w)
        .extrude(2.0)
    )
    body = body.union(rib)

# Drain slots on the floor between ribs
for i in range(rib_count + 1):
    y = -width / 2.0 + wall + (width - 2 * wall) * i / rib_count
    slot = (
        cq.Workplane("XY", origin=(0, y, -0.1))
        .rect(length - 2 * wall - 20, 1.5)
        .extrude(wall + 0.3)
    )
    body = body.cut(slot)

result = body
'''
