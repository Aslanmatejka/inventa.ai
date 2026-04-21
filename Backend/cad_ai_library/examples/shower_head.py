from ..core.metadata import ExampleMetadata

metadata = ExampleMetadata(
    id="shower_head",
    name="Round Shower Head",
    category="sanitary",
    keywords=["shower", "head", "bathroom", "rain", "spray", "fixture"],
    description="Round rain-style shower head with grid of spray holes.",
    techniques=["safe_revolve"],
    nominal_dimensions_mm={"diameter": 200.0, "thickness": 25.0, "arm_diameter": 22.0, "hole_count": 73},
    difficulty="medium",
)

code = '''import cadquery as cq
import math

diameter = 200.0
thick = 25.0
arm_d = 22.0
arm_l = 60.0
hole_d = 1.5

r = diameter / 2.0

# Disk head with slight dome on top
profile = (
    cq.Workplane("XZ")
    .moveTo(0, 0)
    .lineTo(r, 0)
    .lineTo(r, thick * 0.5)
    .spline([(r * 0.6, thick * 0.85), (0, thick)])
    .close()
)
head = profile.revolve(360)

# Spray holes on bottom face (grid clipped to circle)
pts = []
pitch = 10.0
for i in range(-10, 11):
    for j in range(-10, 11):
        x = i * pitch
        y = j * pitch
        if x * x + y * y <= (r * 0.85) ** 2:
            pts.append((x, y))

if pts:
    holes = (
        cq.Workplane("XY", origin=(0, 0, -0.1))
        .pushPoints(pts)
        .circle(hole_d / 2.0)
        .extrude(thick)
    )
    head = head.cut(holes)

# Connector arm
arm = (
    cq.Workplane("XY", origin=(0, 0, thick - 2))
    .circle(arm_d / 2.0)
    .extrude(arm_l)
)
body = head.union(arm)

result = body
'''
