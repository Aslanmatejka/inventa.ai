from ..core.metadata import ExampleMetadata

metadata = ExampleMetadata(
    id="fire_extinguisher",
    name="Fire Extinguisher Body",
    category="safety",
    keywords=["fire", "extinguisher", "safety", "cylinder", "valve"],
    description="Classic dome-topped fire extinguisher canister with valve body.",
    techniques=["safe_revolve"],
    nominal_dimensions_mm={"body_diameter": 120.0, "total_height": 380.0, "valve_diameter": 35.0},
    difficulty="medium",
)

code = '''import cadquery as cq

body_d = 120.0
body_h = 300.0
valve_d = 35.0
valve_h = 45.0
handle_l = 70.0

r = body_d / 2.0

# Cylinder body with a rounded top dome
profile = (
    cq.Workplane("XZ")
    .moveTo(0, 0)
    .lineTo(r, 0)
    .lineTo(r, body_h)
    .threePointArc((r * 0.7, body_h + r * 0.45), (0, body_h + r * 0.55))
    .close()
)
body = profile.revolve(360)

# Valve stem
valve = (
    cq.Workplane("XY", origin=(0, 0, body_h + r * 0.55))
    .circle(valve_d / 2.0)
    .extrude(valve_h)
)
body = body.union(valve)

# Handle (side lever)
handle = (
    cq.Workplane("XY", origin=(valve_d / 2.0, 0, body_h + r * 0.55 + valve_h - 8))
    .box(handle_l, 20, 10, centered=(False, True, False))
)
try:
    handle = handle.edges("|Z").fillet(3.0)
except Exception:
    pass
body = body.union(handle)

# Hose nipple
hose = (
    cq.Workplane("YZ", origin=(0, -valve_d / 2.0, body_h + r * 0.55 + valve_h * 0.4))
    .circle(4.0)
    .extrude(-25)
)
body = body.union(hose)

result = body
'''
