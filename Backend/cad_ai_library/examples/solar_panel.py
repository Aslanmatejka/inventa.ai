from ..core.metadata import ExampleMetadata

metadata = ExampleMetadata(
    id="solar_panel",
    name="Solar Panel Module",
    category="energy",
    keywords=["solar", "panel", "photovoltaic", "pv", "renewable", "energy", "cell"],
    description="Rectangular solar panel module with arrayed photovoltaic cells in an aluminum frame.",
    techniques=["polar_array"],
    nominal_dimensions_mm={"length": 1650.0, "width": 1000.0, "frame_thickness": 40.0, "cell_rows": 10, "cell_cols": 6},
    difficulty="easy",
)

code = '''import cadquery as cq

length = 1650.0
width = 1000.0
frame_t = 40.0
frame_w = 30.0
cells_rows = 10
cells_cols = 6
cell_gap = 3.0
cell_recess = 1.0

# Outer frame
body = cq.Workplane("XY").box(length, width, frame_t, centered=(True, True, False))
try:
    body = body.edges("|Z").fillet(3.0)
except Exception:
    pass

# Hollow the frame interior
inner = (
    cq.Workplane("XY", origin=(0, 0, 3))
    .box(length - 2 * frame_w, width - 2 * frame_w, frame_t - 3, centered=(True, True, False))
)
body = body.cut(inner)

# Glass sheet covering the opening
glass = (
    cq.Workplane("XY", origin=(0, 0, 3))
    .box(length - 2 * frame_w + 4, width - 2 * frame_w + 4, 4, centered=(True, True, False))
)
body = body.union(glass)

# PV cells arrayed on top of the glass
usable_l = length - 2 * frame_w - 10
usable_w = width - 2 * frame_w - 10
cell_l = (usable_l - (cells_cols - 1) * cell_gap) / cells_cols
cell_w = (usable_w - (cells_rows - 1) * cell_gap) / cells_rows

cells = cq.Workplane("XY")
cell_pts = []
for i in range(cells_cols):
    for j in range(cells_rows):
        x = -usable_l / 2.0 + cell_l / 2.0 + i * (cell_l + cell_gap)
        y = -usable_w / 2.0 + cell_w / 2.0 + j * (cell_w + cell_gap)
        cell_pts.append((x, y))
cells = (
    cq.Workplane("XY", origin=(0, 0, 3 + 4 - cell_recess))
    .pushPoints(cell_pts)
    .rect(cell_l, cell_w)
    .extrude(cell_recess + 0.5)
)
body = body.union(cells)

result = body
'''
