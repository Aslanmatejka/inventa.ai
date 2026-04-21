from ..core.metadata import ExampleMetadata

metadata = ExampleMetadata(
    id="road_cone",
    name="Traffic Cone",
    category="safety",
    keywords=["traffic", "cone", "road", "safety", "construction", "orange"],
    description="Classic traffic road cone: square base with tapered cone body and reflective stripes represented as grooves.",
    techniques=["safe_revolve"],
    nominal_dimensions_mm={"base_side": 360.0, "base_height": 40.0, "cone_height": 700.0, "top_diameter": 60.0},
    difficulty="medium",
)

code = '''import cadquery as cq

base_side = 360.0
base_h = 40.0
cone_h = 700.0
top_d = 60.0
bot_d = 220.0

r_bot = bot_d / 2.0
r_top = top_d / 2.0

# Square base
base = cq.Workplane("XY").box(base_side, base_side, base_h, centered=(True, True, False))
try:
    base = base.edges("|Z").fillet(20.0)
except Exception:
    pass

# Cone profile
cone_profile = (
    cq.Workplane("XZ")
    .moveTo(0, base_h)
    .lineTo(r_bot, base_h)
    .lineTo(r_top + 3, base_h + cone_h - 8)
    .lineTo(r_top + 3, base_h + cone_h)
    .lineTo(r_top, base_h + cone_h)
    .lineTo(0, base_h + cone_h - 4)
    .close()
)
cone = cone_profile.revolve(360)

body = base.union(cone)

# Two reflective stripe grooves
for z in (base_h + cone_h * 0.35, base_h + cone_h * 0.6):
    # A torus-like groove via two revolves
    r_at_z = r_bot - (r_bot - r_top - 3) * ((z - base_h) / cone_h)
    groove = (
        cq.Workplane("XZ")
        .moveTo(r_at_z - 2, z)
        .rect(4, 30, centered=True)
        .revolve(360)
    )
    body = body.cut(groove)

result = body
'''
