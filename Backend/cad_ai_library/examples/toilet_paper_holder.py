from ..core.metadata import ExampleMetadata

metadata = ExampleMetadata(
    id="toilet_paper_holder",
    name="Toilet Paper Holder",
    category="sanitary",
    keywords=["toilet", "paper", "holder", "bathroom", "tp", "roller"],
    description="Wall-mount toilet paper holder with spring bar between two arms.",
    techniques=["polyline_profile"],
    nominal_dimensions_mm={"arm_spacing": 145.0, "arm_depth": 100.0, "backplate_length": 170.0},
    difficulty="medium",
)

code = '''import cadquery as cq

span = 145.0
arm_d = 100.0
back_l = 170.0
back_w = 40.0
back_t = 6.0
arm_t = 8.0
bar_d = 10.0

# Backplate
back = (
    cq.Workplane("XY")
    .box(back_l, back_w, back_t, centered=(True, True, False))
)
try:
    back = back.edges("|Z").fillet(4.0)
except Exception:
    pass
body = back

# Two arms sticking out along +Y
for dx in (-span / 2.0, span / 2.0):
    arm = (
        cq.Workplane("XZ", origin=(dx, 0, back_t))
        .moveTo(-arm_t / 2.0, 0)
        .lineTo(arm_t / 2.0, 0)
        .lineTo(arm_t / 2.0, arm_d - 12)
        .threePointArc((0, arm_d), (-arm_t / 2.0, arm_d - 12))
        .lineTo(-arm_t / 2.0, 0)
        .close()
        .extrude(back_w * 0.5)
        .translate((0, -back_w * 0.25, 0))
    )
    body = body.union(arm)

# Spring bar between arms (along X at the tip)
bar = (
    cq.Workplane("YZ", origin=(-span / 2.0, 0, back_t + arm_d - 6))
    .circle(bar_d / 2.0)
    .extrude(span)
)
body = body.union(bar)

# Mount holes through backplate — explicit cuts
for hx in (-back_l * 0.35, back_l * 0.35):
    hole = (
        cq.Workplane("XY", origin=(hx, 0, -1))
        .circle(2.0)
        .extrude(back_t + 2)
    )
    body = body.cut(hole)

result = body
'''
