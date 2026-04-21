from ..core.metadata import ExampleMetadata

metadata = ExampleMetadata(
    id="wrench",
    name="Open-End Wrench",
    category="mechanical",
    keywords=["wrench", "spanner", "tool", "open", "nut", "hex"],
    description="Thin open-end wrench with hex jaw profile and handle.",
    techniques=["polyline_profile", "guarded_fillet"],
    nominal_dimensions_mm={"length": 140.0, "jaw_across_flats": 13.0, "thickness": 5.0},
    difficulty="medium",
)

code = '''import cadquery as cq
import math

length = 140.0
af = 13.0         # across-flats of the jaw
thick = 5.0
handle_w = 14.0
jaw_head_d = af * 1.9

# Handle
handle = (
    cq.Workplane("XY")
    .rect(length - jaw_head_d / 2.0, handle_w)
    .extrude(thick)
    .translate((-(length - jaw_head_d / 2.0) / 2.0 + (jaw_head_d / 2.0 - length / 2.0) + (length - jaw_head_d / 2.0) / 2.0, 0, 0))
)
try:
    handle = handle.edges("|Z").fillet(handle_w * 0.4)
except Exception:
    pass

# Jaw head (round disc) at one end
head_x = length / 2.0 - jaw_head_d / 2.0
head = (
    cq.Workplane("XY", origin=(head_x, 0, 0))
    .circle(jaw_head_d / 2.0)
    .extrude(thick)
)
body = handle.union(head)

# Open slot: hex mouth facing +Y out of the head
r_hex = af / math.sqrt(3)
hex_pts = [(r_hex * math.cos(math.radians(30 + 60 * i)),
            r_hex * math.sin(math.radians(30 + 60 * i)))
           for i in range(6)]
hex_poly = (
    cq.Workplane("XY", origin=(head_x, 0, -0.1))
    .polyline(hex_pts)
    .close()
    .extrude(thick + 0.2)
)
body = body.cut(hex_poly)

# Slot opening to the +Y edge of the head
opening = (
    cq.Workplane("XY", origin=(head_x, jaw_head_d / 2.0, -0.1))
    .rect(af * 0.9, jaw_head_d)
    .extrude(thick + 0.2)
)
body = body.cut(opening)

try:
    body = body.edges(">Z or <Z").fillet(0.6)
except Exception:
    pass

result = body
'''
