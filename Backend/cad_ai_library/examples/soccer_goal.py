from ..core.metadata import ExampleMetadata

metadata = ExampleMetadata(
    id="soccer_goal",
    name="Soccer Goal Frame",
    category="sports",
    keywords=["soccer", "goal", "football", "post", "sports", "net"],
    description="Soccer goal frame: two vertical posts, horizontal crossbar, and angled back supports.",
    techniques=["polyline_profile"],
    nominal_dimensions_mm={"width": 2440.0, "height": 2000.0, "depth": 1200.0, "tube_diameter": 80.0},
    difficulty="easy",
)

code = '''import cadquery as cq

# Scaled to printable model size
width = 600.0
height = 500.0
depth = 300.0
tube_d = 20.0

r = tube_d / 2.0

# Left post
left_post = (
    cq.Workplane("XY", origin=(-width / 2.0, 0, 0))
    .circle(r)
    .extrude(height)
)
# Right post
right_post = (
    cq.Workplane("XY", origin=(width / 2.0, 0, 0))
    .circle(r)
    .extrude(height)
)
# Crossbar
crossbar = (
    cq.Workplane("YZ", origin=(-width / 2.0, 0, height))
    .circle(r)
    .extrude(width)
)

# Back ground bar between posts at Z=0, Y=depth
back_bar = (
    cq.Workplane("YZ", origin=(-width / 2.0, depth, 0))
    .circle(r)
    .extrude(width)
)

# Two slanted back supports from top of each post down to the back bar
for sx in (-1, 1):
    sx_pos = sx * width / 2.0
    # Build a cylindrical rod from top corner to back-bottom corner via sweep
    slant_len = (depth ** 2 + height ** 2) ** 0.5
    slant = (
        cq.Workplane("XY", origin=(sx_pos, 0, height))
        .circle(r)
        .extrude(-slant_len)
    )
    # Rotate so it runs from top-front to bottom-back
    import math as _m
    angle = _m.degrees(_m.atan2(depth, height))
    slant = slant.rotate((sx_pos, 0, height), (sx_pos + 1, 0, height), -angle)
    left_post = left_post.union(slant)

body = left_post.union(right_post).union(crossbar).union(back_bar)

result = body
'''
