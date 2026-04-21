from ..core.metadata import ExampleMetadata

metadata = ExampleMetadata(
    id="syringe",
    name="Medical Syringe",
    category="medical",
    keywords=["syringe", "medical", "injection", "needle", "hypodermic"],
    description="Standard medical syringe: cylindrical barrel with finger grip flange, plunger, and needle hub.",
    techniques=["safe_revolve"],
    nominal_dimensions_mm={"barrel_diameter": 14.0, "barrel_length": 90.0, "needle_length": 30.0, "total_length": 170.0},
    difficulty="medium",
)

code = '''import cadquery as cq

barrel_d = 14.0
barrel_l = 90.0
needle_l = 30.0
plunger_l = 60.0
flange_d = 26.0
flange_t = 3.0
needle_d = 1.2
hub_d = 6.0
hub_l = 8.0

# Barrel (hollow cylinder)
barrel = (
    cq.Workplane("XY")
    .circle(barrel_d / 2.0)
    .extrude(barrel_l)
)
barrel_inside = (
    cq.Workplane("XY", origin=(0, 0, 2))
    .circle(barrel_d / 2.0 - 1.0)
    .extrude(barrel_l - 2)
)
barrel = barrel.cut(barrel_inside)

# Finger flange at the top
flange_profile = (
    cq.Workplane("XZ")
    .moveTo(barrel_d / 2.0, barrel_l - flange_t)
    .lineTo(flange_d / 2.0, barrel_l - flange_t)
    .lineTo(flange_d / 2.0, barrel_l)
    .lineTo(barrel_d / 2.0, barrel_l)
    .close()
)
flange = flange_profile.revolve(360)

# Plunger rod (cross-section) sticking out the top
plunger = (
    cq.Workplane("XY", origin=(0, 0, barrel_l * 0.5))
    .rect(3, 3)
    .extrude(plunger_l)
)
plunger_cap = (
    cq.Workplane("XY", origin=(0, 0, barrel_l * 0.5 + plunger_l))
    .circle(flange_d / 2.0 - 1)
    .extrude(2)
)

# Needle hub + needle
hub = (
    cq.Workplane("XY", origin=(0, 0, -hub_l))
    .circle(hub_d / 2.0)
    .extrude(hub_l)
)
needle = (
    cq.Workplane("XY", origin=(0, 0, -hub_l - needle_l))
    .circle(needle_d / 2.0)
    .extrude(needle_l)
)

body = barrel.union(flange).union(plunger).union(plunger_cap).union(hub).union(needle)

result = body
'''
