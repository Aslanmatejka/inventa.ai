from ..core.metadata import ExampleMetadata

metadata = ExampleMetadata(
    id="tent_stake",
    name="Tent Stake",
    category="camping",
    keywords=["tent", "stake", "peg", "camping", "ground", "anchor"],
    description="Aluminum V-profile tent stake with hook top and pointed tip.",
    techniques=["polyline_profile"],
    nominal_dimensions_mm={"length": 230.0, "profile_width": 20.0, "thickness": 2.0},
    difficulty="medium",
)

code = '''import cadquery as cq

length = 230.0
wing_w = 12.0
thick = 2.0
hook_r = 8.0

# V-shaped cross-section profile (two wings at 90 degrees), X all >= 0 for a clean extrude
profile = (
    cq.Workplane("XZ")
    .moveTo(0, 0)
    .lineTo(wing_w, 0)
    .lineTo(wing_w, thick)
    .lineTo(thick, thick)
    .lineTo(thick, wing_w)
    .lineTo(0, wing_w)
    .close()
)
shaft = profile.extrude(length - 20)

# Pointed tip — tapered box replacing loft
tip = (
    cq.Workplane("XY")
    .rect(wing_w, wing_w)
    .workplane(offset=-20)
    .rect(thick, thick)
    .loft(combine=True)
    .translate((wing_w / 2.0, wing_w / 2.0, 0))
)

# Hook at top (a small cylinder protrusion with a bent tab)
hook = (
    cq.Workplane("XZ", origin=(wing_w / 2.0, 0, length))
    .circle(hook_r)
    .extrude(thick)
)
hook_hole = (
    cq.Workplane("XZ", origin=(wing_w / 2.0, 0, length))
    .circle(hook_r - 3)
    .extrude(thick)
)
hook = hook.cut(hook_hole)

body = shaft.translate((0, 0, 20)).union(tip).union(hook)

result = body
'''
