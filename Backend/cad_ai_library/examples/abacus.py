from ..core.metadata import ExampleMetadata

metadata = ExampleMetadata(
    id="abacus",
    name="Abacus Counting Frame",
    category="educational",
    keywords=["abacus", "counting", "education", "math", "beads", "school"],
    description="Classic abacus with wooden frame, horizontal rods, and arrayed spherical beads.",
    techniques=["polar_array"],
    nominal_dimensions_mm={"frame_length": 260.0, "frame_height": 180.0, "frame_depth": 30.0, "rows": 5, "beads_per_row": 10},
    difficulty="medium",
)

code = '''import cadquery as cq

frame_l = 260.0
frame_h = 180.0
frame_d = 30.0
post_w = 15.0
rows = 5
beads_per_row = 10
bead_d = 16.0
rod_d = 3.0

# Build outer frame as four posts
top_post = cq.Workplane("XY", origin=(0, 0, frame_h - post_w)).box(
    frame_l, frame_d, post_w, centered=(True, True, False)
)
bot_post = cq.Workplane("XY").box(frame_l, frame_d, post_w, centered=(True, True, False))
left_post = cq.Workplane("XY", origin=(-frame_l / 2.0 + post_w / 2.0, 0, post_w)).box(
    post_w, frame_d, frame_h - 2 * post_w, centered=(True, True, False)
)
right_post = cq.Workplane("XY", origin=(frame_l / 2.0 - post_w / 2.0, 0, post_w)).box(
    post_w, frame_d, frame_h - 2 * post_w, centered=(True, True, False)
)

body = top_post.union(bot_post).union(left_post).union(right_post)

# Horizontal rods (rows) and beads
row_area_h = frame_h - 2 * post_w
spacing_z = row_area_h / (rows + 1)
rod_len = frame_l - 2 * post_w
bead_slot_x = rod_len / beads_per_row

for r in range(rows):
    z = post_w + spacing_z * (r + 1)
    # Rod
    rod = (
        cq.Workplane("YZ", origin=(-rod_len / 2.0, 0, z))
        .circle(rod_d / 2.0)
        .extrude(rod_len)
    )
    body = body.union(rod)
    # Beads strung along the rod
    for b in range(beads_per_row):
        x = -rod_len / 2.0 + bead_slot_x * (b + 0.5)
        bead = cq.Workplane("XY", origin=(x, 0, z)).sphere(bead_d / 2.0)
        body = body.union(bead)

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
