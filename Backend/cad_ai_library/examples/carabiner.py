from ..core.metadata import ExampleMetadata

metadata = ExampleMetadata(
    id="carabiner",
    name="Carabiner Clip",
    category="camping",
    keywords=["carabiner", "biner", "clip", "climbing", "camping", "keychain"],
    description="D-shaped carabiner clip with rounded cross-section.",
    techniques=["safe_revolve"],
    nominal_dimensions_mm={"length": 80.0, "width": 45.0, "rod_diameter": 8.0},
    difficulty="medium",
)

code = '''import cadquery as cq

length = 80.0
width = 45.0
rod_d = 8.0
gate_gap = 12.0

# Build a D-shaped loop: two straight bars connected by two arcs
# Use a sweep-by-revolve approach: build the centerline as a wire, then tube it
r_arc = width / 2.0
straight_len = length - 2 * r_arc

wire = (
    cq.Workplane("XY")
    .moveTo(-straight_len / 2.0, r_arc)
    .lineTo(straight_len / 2.0 - 2, r_arc)
    .threePointArc((straight_len / 2.0 + r_arc - 2, 0),
                   (straight_len / 2.0 - 2, -r_arc))
    .lineTo(-straight_len / 2.0 + gate_gap, -r_arc)
    .threePointArc((-straight_len / 2.0 - r_arc + gate_gap, -r_arc * 0.3),
                   (-straight_len / 2.0 + gate_gap - 2, r_arc * 0.3))
)

# Sweep a circle along the path
body = (
    cq.Workplane("XZ", origin=(-straight_len / 2.0, r_arc, 0))
    .circle(rod_d / 2.0)
    .sweep(wire)
)

result = body
'''
