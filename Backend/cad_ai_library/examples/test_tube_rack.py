from ..core.metadata import ExampleMetadata

metadata = ExampleMetadata(
    id="test_tube_rack",
    name="Test Tube Rack",
    category="lab",
    keywords=["test", "tube", "rack", "lab", "science", "holder", "vial"],
    description="Test tube rack with 2x6 holes for standard test tubes.",
    techniques=["polar_array"],
    nominal_dimensions_mm={"length": 180.0, "width": 60.0, "height": 60.0, "tube_diameter": 16.0},
    difficulty="easy",
)

code = '''import cadquery as cq

length = 180.0
width = 60.0
height = 60.0
tube_d = 16.0
wall = 6.0
rows = 2
cols = 6

# Top shelf with holes + base with shallow recesses + two side posts
top_t = 8.0
bot_t = 10.0

base = cq.Workplane("XY").box(length, width, bot_t, centered=(True, True, False))
try:
    base = base.edges("|Z").fillet(4.0)
except Exception:
    pass

# Side posts
post_w = 8.0
post_h = height - top_t
posts = []
for sx in (-1, 1):
    post = (
        cq.Workplane("XY", origin=(sx * (length / 2.0 - post_w / 2.0), 0, bot_t))
        .box(post_w, width, post_h, centered=(True, True, False))
    )
    try:
        post = post.edges("|Z").fillet(1.5)
    except Exception:
        pass
    posts.append(post)

top = (
    cq.Workplane("XY", origin=(0, 0, height - top_t))
    .box(length, width, top_t, centered=(True, True, False))
)

body = base.union(posts[0]).union(posts[1]).union(top)

# Tube holes through top + shallow recesses in base
cell_x = (length - 2 * wall) / cols
cell_y = (width - 2 * wall) / rows
hole_pts = []
for i in range(cols):
    for j in range(rows):
        cx = -length / 2.0 + wall + cell_x * (i + 0.5)
        cy = -width / 2.0 + wall + cell_y * (j + 0.5)
        hole_pts.append((cx, cy))

top_cutter = (
    cq.Workplane("XY", origin=(0, 0, height - top_t - 0.1))
    .pushPoints(hole_pts)
    .circle(tube_d / 2.0)
    .extrude(top_t + 0.3)
)
body = body.cut(top_cutter)

base_cutter = (
    cq.Workplane("XY", origin=(0, 0, bot_t - 3))
    .pushPoints(hole_pts)
    .circle(tube_d / 2.0 - 1)
    .extrude(3.2)
)
body = body.cut(base_cutter)

result = body
'''
