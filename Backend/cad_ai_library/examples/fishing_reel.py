from ..core.metadata import ExampleMetadata

metadata = ExampleMetadata(
    id="fishing_reel",
    name="Spinning Fishing Reel",
    category="fishing",
    keywords=["fishing", "reel", "spinning", "angler", "rod", "tackle"],
    description="Stylized spinning fishing reel: spool, body, and folding handle arm.",
    techniques=["safe_revolve"],
    nominal_dimensions_mm={"spool_diameter": 60.0, "spool_height": 30.0, "body_length": 90.0},
    difficulty="medium",
)

code = '''import cadquery as cq

spool_d = 60.0
spool_h = 30.0
body_l = 90.0

# Spool (revolved profile)
r = spool_d / 2.0
spool_profile = (
    cq.Workplane("XZ")
    .moveTo(0, 0)
    .lineTo(r, 0)
    .lineTo(r, 4)
    .lineTo(r * 0.55, 6)
    .lineTo(r * 0.55, spool_h - 6)
    .lineTo(r, spool_h - 4)
    .lineTo(r, spool_h)
    .lineTo(0, spool_h)
    .close()
)
spool = spool_profile.revolve(360)

# Reel body below spool (oval)
body = (
    cq.Workplane("XY", origin=(0, 0, -body_l))
    .ellipse(30, 18)
    .extrude(body_l)
)
try:
    body = body.edges(">Z or <Z").fillet(4.0)
except Exception:
    pass

# Foot mount plate
foot = (
    cq.Workplane("XY", origin=(0, 0, -body_l - 6))
    .box(80, 18, 6, centered=(True, True, False))
)
try:
    foot = foot.edges("|Z").fillet(3.0)
except Exception:
    pass

# Handle arm
arm = (
    cq.Workplane("XY", origin=(30, 0, -body_l * 0.4))
    .box(50, 10, 6, centered=(False, True, False))
)
knob = cq.Workplane("XY", origin=(85, 0, -body_l * 0.4 + 3)).cylinder(14, 6)

body = body.union(spool).union(foot).union(arm).union(knob)

result = body
'''
