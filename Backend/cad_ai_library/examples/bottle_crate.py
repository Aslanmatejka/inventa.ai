from ..core.metadata import ExampleMetadata

metadata = ExampleMetadata(
    id="bottle_crate",
    name="Bottle Crate (6-Pack)",
    category="packaging",
    keywords=["bottle", "crate", "carrier", "6-pack", "six pack", "beer", "divider"],
    description="6-cell bottle crate with dividers and a central lift handle.",
    techniques=["shell_cavity", "polar_array"],
    nominal_dimensions_mm={"length": 260.0, "width": 175.0, "height": 160.0},
    difficulty="medium",
)

code = '''import cadquery as cq

length = 260.0
width = 175.0
height = 160.0
wall = 3.0
rows = 2
cols = 3
bottle_d = 70.0
handle_h = 80.0

body = cq.Workplane("XY").box(length, width, height, centered=(True, True, False))
try:
    body = body.edges("|Z").fillet(5.0)
except Exception:
    pass
body = body.faces(">Z").shell(-wall)

# Bottle cavities
cell_x = (length - 2 * wall) / cols
cell_y = (width - 2 * wall) / rows
for i in range(cols):
    for j in range(rows):
        cx = -length / 2.0 + wall + cell_x * (i + 0.5)
        cy = -width / 2.0 + wall + cell_y * (j + 0.5)
        cavity = (
            cq.Workplane("XY", origin=(cx, cy, wall))
            .circle(bottle_d / 2.0)
            .extrude(height - wall + 0.1)
        )
        body = body.cut(cavity)

# Central divider wall along X
div_x = (
    cq.Workplane("XY", origin=(0, -wall / 2.0, wall))
    .box(length - 2 * wall, wall, height - wall,
         centered=(True, False, False))
)
body = body.union(div_x.intersect(cq.Workplane("XY").box(length - 2*wall, wall, height - wall, centered=(True, False, False)).translate((0, -wall/2.0, wall))))

# Central lift handle spanning the top across X
handle_slab = (
    cq.Workplane("XY", origin=(0, -wall / 2.0, height - wall))
    .box(length - 2 * wall, wall, handle_h, centered=(True, False, False))
)
body = body.union(handle_slab)
# Finger slot
slot = (
    cq.Workplane("XZ", origin=(0, -wall / 2.0 - 1, height + handle_h * 0.4))
    .ellipse(length * 0.25, handle_h * 0.2)
    .extrude(wall + 2)
)
body = body.cut(slot)

result = body
'''
