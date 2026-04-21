from ..core.metadata import ExampleMetadata

metadata = ExampleMetadata(
    id="earbud_case",
    name="Wireless Earbud Case",
    category="electronics",
    keywords=["earbud", "earphone", "case", "airpods", "wireless", "charging"],
    description="Pocket-size wireless earbud charging case with two ear cups and hinge slot.",
    techniques=["shell_cavity", "guarded_fillet"],
    nominal_dimensions_mm={"length": 65.0, "width": 50.0, "height": 28.0, "wall": 2.2},
    difficulty="medium",
)

code = '''import cadquery as cq

length = 65.0
width = 50.0
height = 28.0
wall = 2.2

body = cq.Workplane("XY").box(length, width, height, centered=(True, True, False))
try:
    body = body.edges("|Z").fillet(10.0)
except Exception:
    pass
try:
    body = body.edges(">Z or <Z").fillet(4.0)
except Exception:
    pass

# Two ear cup cavities on the top face
for xc in (-length * 0.22, length * 0.22):
    cup = (
        cq.Workplane("XY", origin=(xc, 0, height - 4))
        .circle(9.0)
        .extrude(14)
        .translate((0, 0, -12))
    )
    body = body.cut(cup)

# Hinge slot on back edge
slot = (
    cq.Workplane("XY", origin=(0, width / 2.0 - 3, height - 1.5))
    .box(length * 0.7, 2.0, 2.0, centered=(True, True, False))
)
body = body.cut(slot)

# LED indicator pin hole on front
body = body.faces("<Y").workplane().center(0, -height * 0.2).hole(1.5)

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
