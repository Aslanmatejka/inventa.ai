from ..core.metadata import ExampleMetadata

metadata = ExampleMetadata(
    id="smoke_detector",
    name="Smoke Detector Housing",
    category="safety",
    keywords=["smoke", "detector", "alarm", "safety", "fire", "ceiling"],
    description="Round ceiling smoke detector housing with vent slots and test button.",
    techniques=["safe_revolve", "polar_array"],
    nominal_dimensions_mm={"diameter": 130.0, "height": 40.0, "button_diameter": 18.0},
    difficulty="easy",
)

code = '''import cadquery as cq
import math

diameter = 130.0
height = 40.0
button_d = 18.0
button_h = 2.5

r = diameter / 2.0

# Revolve a bell-shaped profile
profile = (
    cq.Workplane("XZ")
    .moveTo(0, 0)
    .lineTo(r, 0)
    .spline([(r * 0.95, height * 0.4), (r * 0.6, height * 0.85), (r * 0.4, height)])
    .lineTo(0, height)
    .close()
)
body = profile.revolve(360)

# Vent slot ring (radial)
slot_count = 24
for i in range(slot_count):
    theta = 360.0 / slot_count * i
    x = (r - 6) * math.cos(math.radians(theta))
    y = (r - 6) * math.sin(math.radians(theta))
    slot = (
        cq.Workplane(cq.Plane(origin=(x, y, height * 0.25),
                              xDir=(-math.sin(math.radians(theta)), math.cos(math.radians(theta)), 0),
                              normal=(math.cos(math.radians(theta)), math.sin(math.radians(theta)), 0)))
        .rect(8.0, 3.0)
        .extrude(8)
    )
    body = body.cut(slot)

# Test button (small boss on top)
button = (
    cq.Workplane("XY", origin=(0, 0, height))
    .circle(button_d / 2.0)
    .extrude(button_h)
)
body = body.union(button)

# Mounting tab holes on back (two small through-holes, cut explicitly)
for x_sign in (-1, 1):
    hole = (
        cq.Workplane("XY", origin=(x_sign * r * 0.65, 0, -1))
        .circle(1.75)
        .extrude(height + 2)
    )
    body = body.cut(hole)

result = body
'''
