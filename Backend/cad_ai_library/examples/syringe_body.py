from ..core.metadata import ExampleMetadata

metadata = ExampleMetadata(
    id="syringe_body",
    name="Syringe Body",
    category="container",
    keywords=["syringe", "medical", "injection", "barrel", "dispenser"],
    description="Hollow syringe barrel with finger flange and luer-like tip.",
    techniques=["safe_revolve", "shell_cavity"],
    nominal_dimensions_mm={"barrel_diameter": 14.0, "barrel_length": 70.0, "flange_diameter": 26.0, "tip_length": 10.0},
    difficulty="medium",
)

code = '''import cadquery as cq

barrel_d = 14.0
barrel_l = 70.0
wall = 1.2
flange_d = 26.0
flange_t = 2.0
tip_l = 10.0
tip_base_d = 6.0
tip_end_d = 3.2

r_barrel = barrel_d / 2.0
r_flange = flange_d / 2.0
r_tip_b = tip_base_d / 2.0
r_tip_e = tip_end_d / 2.0

# Revolved outer profile
profile = (
    cq.Workplane("XZ")
    .moveTo(0, 0)
    .lineTo(r_tip_e, 0)
    .lineTo(r_tip_b, tip_l)
    .lineTo(r_barrel, tip_l)
    .lineTo(r_barrel, tip_l + barrel_l)
    .lineTo(r_flange, tip_l + barrel_l)
    .lineTo(r_flange, tip_l + barrel_l + flange_t)
    .lineTo(0, tip_l + barrel_l + flange_t)
    .close()
)
body = profile.revolve(360)

# Hollow bore
bore = (
    cq.Workplane("XY", origin=(0, 0, tip_l))
    .circle(r_barrel - wall)
    .extrude(barrel_l + flange_t + 1)
)
body = body.cut(bore)

# Tip channel
chan = (
    cq.Workplane("XY", origin=(0, 0, -0.1))
    .circle(r_tip_e * 0.5)
    .extrude(tip_l + wall + 0.2)
)
body = body.cut(chan)

result = body
'''
