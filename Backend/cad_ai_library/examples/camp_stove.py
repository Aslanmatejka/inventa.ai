from ..core.metadata import ExampleMetadata

metadata = ExampleMetadata(
    id="camp_stove",
    name="Camping Stove",
    category="camping",
    keywords=["camping", "stove", "camp", "burner", "outdoor", "backpacking"],
    description="Compact camping stove burner head with fuel stem and arrayed flame holes.",
    techniques=["safe_revolve", "polar_array"],
    nominal_dimensions_mm={"burner_diameter": 70.0, "stem_length": 50.0, "stem_diameter": 12.0},
    difficulty="medium",
)

code = '''import cadquery as cq
import math

burner_d = 70.0
burner_h = 20.0
stem_d = 12.0
stem_l = 50.0

r = burner_d / 2.0

# Burner head profile
profile = (
    cq.Workplane("XZ")
    .moveTo(0, 0)
    .lineTo(stem_d / 2.0, 0)
    .lineTo(stem_d / 2.0, stem_l)
    .lineTo(r, stem_l + 4)
    .lineTo(r, stem_l + burner_h - 4)
    .lineTo(r * 0.6, stem_l + burner_h)
    .lineTo(0, stem_l + burner_h)
    .close()
)
body = profile.revolve(360)

# Flame holes around the burner rim (radial)
hole_count = 24
for i in range(hole_count):
    theta = 360.0 / hole_count * i
    x = r * math.cos(math.radians(theta))
    y = r * math.sin(math.radians(theta))
    v = (math.cos(math.radians(theta)), math.sin(math.radians(theta)), 0)
    cutter = (
        cq.Workplane(cq.Plane(origin=(x, y, stem_l + burner_h / 2.0),
                              xDir=(-v[1], v[0], 0),
                              normal=v))
        .circle(1.2)
        .extrude(8)
    )
    body = body.cut(cutter)

# Three pot-support tabs sticking up
for i in range(3):
    theta = 120 * i
    tab = (
        cq.Workplane("XY", origin=(r - 4, 0, stem_l + burner_h))
        .box(6, 3, 12, centered=(False, True, False))
        .rotate((0, 0, 0), (0, 0, 1), theta)
    )
    body = body.union(tab)

result = body
'''
