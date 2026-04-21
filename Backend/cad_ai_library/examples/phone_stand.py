from ..core.metadata import ExampleMetadata

metadata = ExampleMetadata(
    id="phone_stand",
    name="Phone Stand",
    category="accessory",
    keywords=["phone stand", "phone holder", "stand", "cradle", "desk", "charging stand"],
    description="L-shaped phone cradle with a wedge back for angle and a lip to hold the phone in place.",
    techniques=["polyline profile extrusion", "lip rib", "guarded chamfer"],
    nominal_dimensions_mm={"width": 80.0, "depth": 90.0, "height": 100.0},
    difficulty="beginner",
)

code = '''\
import cadquery as cq

width = 80.0
base_depth = 90.0
base_thickness = 8.0
back_height = 100.0
back_angle_deg = 15.0  # lean back
back_thickness = 8.0
lip_height = 8.0
lip_depth = 6.0
slot_width = 12.0  # cable pass-through

import math
lean = math.tan(math.radians(back_angle_deg)) * back_height

# Side profile in the XZ plane (width along Y). Walk a polyline
# around the outline, including the lean of the back panel.
profile = (
    cq.Workplane("XZ")
    .polyline([
        (0, 0),
        (base_depth, 0),
        (base_depth, base_thickness + lip_height),      # up the lip
        (base_depth - lip_depth, base_thickness + lip_height),
        (base_depth - lip_depth, base_thickness),       # back down
        (back_thickness + lean, base_thickness),        # floor until back panel foot
        (lean, base_thickness + back_height),            # up the back, leaning
        (0, base_thickness + back_height),
    ])
    .close()
    .extrude(width)
)

# Cable pass-through slot in the base
slot = (
    cq.Workplane("XY", origin=(base_depth / 2.0, 0, base_thickness / 2.0))
    .box(slot_width, width + 2.0, base_thickness + 1.0, centered=(True, True, True))
)
profile = profile.cut(slot)

try:
    profile = profile.edges(">Z").chamfer(1.0)
except Exception:
    pass

result = profile

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
