from ..core.metadata import ExampleMetadata

metadata = ExampleMetadata(
    id="inhaler_body",
    name="Asthma Inhaler Body",
    category="medical",
    keywords=["inhaler", "asthma", "medical", "puffer", "mdi", "canister"],
    description="L-shaped metered-dose inhaler body with mouthpiece and canister well.",
    techniques=["polyline_profile", "shell_cavity"],
    nominal_dimensions_mm={"body_length": 80.0, "body_width": 40.0, "mouthpiece_length": 35.0},
    difficulty="medium",
)

code = '''import cadquery as cq

body_l = 80.0
body_w = 40.0
body_t = 30.0
mouth_l = 35.0
mouth_w = 28.0
mouth_t = 18.0
can_d = 22.0
can_depth = body_l - 10

# L profile in XZ (vertical canister well + horizontal mouthpiece)
profile = (
    cq.Workplane("XZ")
    .moveTo(0, 0)
    .lineTo(mouth_l + 6, 0)
    .lineTo(mouth_l + 6, mouth_t)
    .lineTo(body_t, mouth_t)
    .lineTo(body_t, body_l)
    .lineTo(0, body_l)
    .close()
)
body = profile.extrude(body_w).translate((0, -body_w / 2.0, 0))

try:
    body = body.edges("|Y").fillet(3.0)
except Exception:
    pass

# Canister well (cut from the top)
can_well = (
    cq.Workplane("XY", origin=(body_t / 2.0, 0, body_l - can_depth))
    .circle(can_d / 2.0)
    .extrude(can_depth + 1)
)
body = body.cut(can_well)

# Mouthpiece opening
mouth_bore = (
    cq.Workplane("YZ", origin=(mouth_l + 7, 0, mouth_t / 2.0))
    .ellipse(mouth_w / 2.0, mouth_t / 2.0 - 2)
    .extrude(-mouth_l - 2)
)
body = body.cut(mouth_bore)

result = body
'''
