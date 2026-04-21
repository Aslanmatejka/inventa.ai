from ..core.metadata import ExampleMetadata

metadata = ExampleMetadata(
    id="pliers",
    name="Pliers",
    category="tool",
    keywords=["pliers", "plier", "tool", "gripping", "jaw", "wire cutter"],
    description="Slip-joint pliers with two mirrored jaw/handle halves and a central pivot.",
    techniques=["boolean_union", "guarded_fillet"],
    nominal_dimensions_mm={"length": 180.0, "handle_width": 14.0},
    difficulty="medium",
)

code = '''import cadquery as cq

total_len = 180.0
pivot_x = 40.0
thickness = 6.0
jaw_len = pivot_x
handle_len = total_len - pivot_x

def build_half(mirror_y):
    # Handle arm (angled)
    handle = (cq.Workplane("XY")
              .center(-pivot_x - handle_len/2, mirror_y * 8)
              .box(handle_len, 14, thickness, centered=(True, True, False)))
    # Jaw (narrows toward tip)
    jaw_pts = [(0, mirror_y * 2), (jaw_len, mirror_y * 1.5),
               (jaw_len, mirror_y * -1.5), (0, mirror_y * -2 + mirror_y * 14)]
    # Simpler: use a tapered box
    jaw = (cq.Workplane("XY")
           .center(jaw_len/2, mirror_y * 4)
           .box(jaw_len, 8, thickness, centered=(True, True, False)))
    # Pivot boss
    pivot = (cq.Workplane("XY").circle(8).extrude(thickness))
    return handle.union(jaw).union(pivot)

top = build_half(1)
bot = build_half(-1)
body = top.union(bot)

# Pivot hole
hole = cq.Workplane("XY").circle(2.5).extrude(thickness + 2)
body = body.cut(hole)

try:
    body = body.edges("|Z").fillet(1.5)
except Exception:
    pass

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
