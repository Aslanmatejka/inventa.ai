from ..core.metadata import ExampleMetadata

metadata = ExampleMetadata(
    id="crate_stackable",
    name="Stackable Storage Crate",
    category="packaging",
    keywords=["crate", "storage", "stackable", "container", "bin", "shipping"],
    description="Stackable open-top crate with side handles and corner stacking lugs.",
    techniques=["shell_cavity", "guarded_fillet"],
    nominal_dimensions_mm={"length": 400.0, "width": 300.0, "height": 220.0, "wall": 4.0},
    difficulty="medium",
)

code = '''import cadquery as cq

length = 400.0
width = 300.0
height = 220.0
wall = 4.0

body = cq.Workplane("XY").box(length, width, height, centered=(True, True, False))
try:
    body = body.edges("|Z").fillet(8.0)
except Exception:
    pass

body = body.faces(">Z").shell(-wall)

# Side handle cutouts (long faces)
for y_side in (width / 2.0 - wall / 2.0, -width / 2.0 + wall / 2.0):
    handle = (
        cq.Workplane("XZ", origin=(0, y_side, height - 40))
        .rect(length * 0.3, 25, forConstruction=False)
        .extrude(wall + 2)
        .translate((0, -wall - 1 if y_side > 0 else 0, 0))
    )
    body = body.cut(handle)

# Stacking lugs on top rim (4 corners, small bumps)
lug_inset = 18
for sx in (-1, 1):
    for sy in (-1, 1):
        lug = (
            cq.Workplane("XY",
                         origin=(sx * (length / 2.0 - lug_inset),
                                 sy * (width / 2.0 - lug_inset),
                                 height))
            .box(10, 10, 4, centered=(True, True, False))
        )
        body = body.union(lug)

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
