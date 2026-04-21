from ..core.metadata import ExampleMetadata

metadata = ExampleMetadata(
    id="faucet_handle",
    name="Faucet Handle",
    category="plumbing",
    keywords=["faucet", "handle", "tap", "valve", "plumbing", "knob"],
    description="Cross-style faucet handle with four arms and central broach.",
    techniques=["polar_array", "guarded_fillet"],
    nominal_dimensions_mm={"span": 60.0, "arm_diameter": 10.0, "hub_diameter": 22.0},
    difficulty="medium",
)

code = '''import cadquery as cq

span = 60.0
arm_d = 10.0
hub_d = 22.0
hub_h = 16.0
stem_d = 7.0

# Central hub
body = cq.Workplane("XY").circle(hub_d / 2.0).extrude(hub_h)

# Four arms
arm_len = span / 2.0
for i in range(4):
    theta = 90 * i
    arm = (
        cq.Workplane("YZ", origin=(0, 0, hub_h / 2.0))
        .circle(arm_d / 2.0)
        .extrude(arm_len)
        .rotate((0, 0, 0), (0, 0, 1), theta)
    )
    # End cap
    tip = (
        cq.Workplane("XY", origin=(arm_len, 0, hub_h / 2.0))
        .sphere(arm_d / 2.0 * 1.2)
        .rotate((0, 0, 0), (0, 0, 1), theta)
    )
    body = body.union(arm).union(tip)

# Broach for valve stem (square-ish hole)
broach = (
    cq.Workplane("XY")
    .rect(stem_d, stem_d)
    .extrude(hub_h)
)
body = body.cut(broach)

try:
    body = body.edges(">Z or <Z").fillet(1.0)
except Exception:
    pass

result = body
'''
