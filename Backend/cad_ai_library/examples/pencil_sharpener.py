from ..core.metadata import ExampleMetadata

metadata = ExampleMetadata(
    id="pencil_sharpener",
    name="Pencil Sharpener",
    category="stationery",
    keywords=["pencil", "sharpener", "stationery", "school", "office"],
    description="Classic single-hole pencil sharpener block with conical pencil bore and blade slot.",
    techniques=["loft_frustum", "guarded_fillet"],
    nominal_dimensions_mm={"length": 28.0, "width": 18.0, "height": 12.0},
    difficulty="easy",
)

code = '''import cadquery as cq

length = 28.0
width = 18.0
height = 12.0

body = cq.Workplane("XY").box(length, width, height, centered=(True, True, False))
try:
    body = body.edges("|Z").fillet(2.5)
except Exception:
    pass
try:
    body = body.edges(">Z").fillet(1.0)
except Exception:
    pass

# Conical pencil bore along +X, entering from -X end
cone = (
    cq.Workplane("YZ", origin=(-length / 2.0 - 0.1, 0, height / 2.0))
    .circle(4.5)
    .workplane(offset=length - 4)
    .circle(1.0)
    .loft(combine=True)
)
body = body.cut(cone)

# Blade slot on top
slot = (
    cq.Workplane("XY", origin=(-length * 0.1, 0, height - 2))
    .box(length * 0.8, 3.0, 3.0, centered=(True, True, False))
)
body = body.cut(slot)

# Screw boss on top (simplified dome + hole)
screw = (
    cq.Workplane("XY", origin=(length * 0.3, 0, height - 2))
    .circle(2.0)
    .extrude(2.5)
)
body = body.union(screw).faces(">Z").workplane().center(length * 0.3, 0).hole(1.5)

result = body
'''
