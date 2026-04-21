from ..core.metadata import ExampleMetadata

metadata = ExampleMetadata(
    id="pallet",
    name="Shipping Pallet",
    category="packaging",
    keywords=["pallet", "shipping", "wood", "deck", "logistics", "forklift"],
    description="Standard 4-way shipping pallet with top deck boards, stringers, and bottom boards.",
    techniques=["polar_array"],
    nominal_dimensions_mm={"length": 1200.0, "width": 800.0, "height": 144.0},
    difficulty="medium",
)

code = '''import cadquery as cq

length = 1200.0
width = 800.0
total_h = 144.0
deck_t = 22.0
stringer_h = 100.0
stringer_w = 70.0
bottom_t = 22.0

# Bottom boards: three across the length direction
bottom_spacing = (length - bottom_t * 3) / 2.0
body = None
for i, xc in enumerate((-length / 2.0 + bottom_t / 2.0,
                         0.0,
                         length / 2.0 - bottom_t / 2.0)):
    board = (
        cq.Workplane("XY", origin=(xc, 0, 0))
        .box(bottom_t, width, bottom_t, centered=(True, True, False))
    )
    body = board if body is None else body.union(board)

# Three stringers running along length
for yc in (-width / 2.0 + stringer_w / 2.0,
           0.0,
           width / 2.0 - stringer_w / 2.0):
    stringer = (
        cq.Workplane("XY", origin=(0, yc, bottom_t))
        .box(length, stringer_w, stringer_h, centered=(True, True, False))
    )
    body = body.union(stringer)

# Top deck boards: 7 across the width direction
deck_z = bottom_t + stringer_h
top_count = 7
gap = (width - top_count * (width / (top_count + 2))) / (top_count - 1)
board_w = (width - gap * (top_count - 1)) / top_count
for i in range(top_count):
    yc = -width / 2.0 + board_w / 2.0 + i * (board_w + gap)
    board = (
        cq.Workplane("XY", origin=(0, yc, deck_z))
        .box(length, board_w, deck_t, centered=(True, True, False))
    )
    body = body.union(board)

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
