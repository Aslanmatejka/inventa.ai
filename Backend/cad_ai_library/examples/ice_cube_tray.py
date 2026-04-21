from ..core.metadata import ExampleMetadata

metadata = ExampleMetadata(
    id="ice_cube_tray",
    name="Ice Cube Tray",
    category="container",
    keywords=["ice", "cube", "tray", "freezer", "kitchen", "mold"],
    description="2x6 ice cube tray with tapered cube cavities.",
    techniques=["loft_frustum", "guarded_fillet"],
    nominal_dimensions_mm={"length": 180.0, "width": 80.0, "height": 30.0, "cube_size_top": 28.0},
    difficulty="medium",
)

code = '''import cadquery as cq

length = 180.0
width = 80.0
height = 30.0
wall = 3.0
rows = 2
cols = 6
cube_top = 28.0
cube_bot = 22.0

body = cq.Workplane("XY").box(length, width, height, centered=(True, True, False))
try:
    body = body.edges("|Z").fillet(4.0)
except Exception:
    pass

# Tapered cube cavities
cell_x = (length - 2 * wall) / cols
cell_y = (width - 2 * wall) / rows
for i in range(cols):
    for j in range(rows):
        cx = -length / 2.0 + wall + cell_x * (i + 0.5)
        cy = -width / 2.0 + wall + cell_y * (j + 0.5)
        cavity = (
            cq.Workplane("XY", origin=(cx, cy, wall))
            .rect(cube_bot, cube_bot)
            .workplane(offset=height - wall + 0.1)
            .rect(cube_top, cube_top)
            .loft(combine=True)
        )
        body = body.cut(cavity)

result = body
'''
