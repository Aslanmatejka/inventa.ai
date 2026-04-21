from ..core.metadata import ExampleMetadata

metadata = ExampleMetadata(
    id="wall_clock",
    name="Round Wall Clock",
    category="decorative",
    keywords=["clock", "wall", "analog", "time", "round", "timepiece"],
    description="Round analog wall clock face with hour markers and central spindle.",
    techniques=["polar_array", "guarded_fillet"],
    nominal_dimensions_mm={"diameter": 260.0, "thickness": 28.0, "rim": 8.0},
    difficulty="medium",
)

code = '''import cadquery as cq
import math

diameter = 260.0
thick = 28.0
rim = 8.0
face_depth = 4.0

r = diameter / 2.0

# Outer rim body
body = cq.Workplane("XY").circle(r).extrude(thick)
try:
    body = body.edges(">Z or <Z").fillet(3.0)
except Exception:
    pass

# Face recess (dial area)
face_recess = (
    cq.Workplane("XY", origin=(0, 0, thick - face_depth))
    .circle(r - rim)
    .extrude(face_depth + 0.1)
)
body = body.cut(face_recess)

# 12 hour markers: small rectangular bosses inside the rim
for i in range(12):
    theta = math.radians(90 - 30 * i)
    x = (r - rim / 2.0 - 3) * math.cos(theta)
    y = (r - rim / 2.0 - 3) * math.sin(theta)
    marker = (
        cq.Workplane("XY", origin=(x, y, thick - face_depth))
        .rect(4, 10)
        .extrude(1.5)
        .rotate((x, y, 0), (x, y, 1), math.degrees(theta) - 90)
    )
    body = body.union(marker)

# Central spindle hole
body = (
    body.faces(">Z").workplane()
    .hole(8.0, depth=10.0)
)

# Hang hole on back
body = (
    body.faces("<Z").workplane()
    .center(0, -r * 0.4)
    .hole(5.0, depth=6.0)
)

result = body
'''
