from ..core.metadata import ExampleMetadata

metadata = ExampleMetadata(
    id="lego_brick",
    name="Toy Brick (2x4)",
    category="toy",
    keywords=["lego", "brick", "toy", "stud", "block", "building"],
    description="Classic 2x4 interlocking toy brick with studs and hollow underside.",
    techniques=["polar_array", "shell_cavity"],
    nominal_dimensions_mm={"length": 31.8, "width": 15.8, "height": 9.6, "stud_diameter": 4.8},
    difficulty="medium",
)

code = '''import cadquery as cq

length = 31.8
width = 15.8
height = 9.6
wall = 1.2
stud_d = 4.8
stud_h = 1.7
stud_pitch = 8.0
cols = 4
rows = 2

body = cq.Workplane("XY").box(length, width, height, centered=(True, True, False))

# Studs on top (polar/grid array)
stud_pts = []
for i in range(cols):
    x = -(cols - 1) / 2.0 * stud_pitch + i * stud_pitch
    for j in range(rows):
        y = -(rows - 1) / 2.0 * stud_pitch + j * stud_pitch
        stud_pts.append((x, y))

studs = (
    cq.Workplane("XY", origin=(0, 0, height))
    .pushPoints(stud_pts)
    .circle(stud_d / 2.0)
    .extrude(stud_h)
)
body = body.union(studs)

# Hollow underside cavity
cavity = (
    cq.Workplane("XY", origin=(0, 0, -0.1))
    .rect(length - 2 * wall, width - 2 * wall)
    .extrude(height - wall + 0.1)
)
body = body.cut(cavity)

# Center tubes on the underside (between stud grid)
tube_od = 6.5
tube_id = 4.9
for i in range(cols - 1):
    x = -(cols - 2) / 2.0 * stud_pitch + i * stud_pitch
    tube = (
        cq.Workplane("XY", origin=(x, 0, 0))
        .circle(tube_od / 2.0)
        .circle(tube_id / 2.0)
        .extrude(height - wall)
    )
    body = body.union(tube)

result = body
'''
