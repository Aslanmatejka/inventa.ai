from ..core.metadata import ExampleMetadata

metadata = ExampleMetadata(
    id="medal",
    name="Sport Medal",
    category="award",
    keywords=["medal", "award", "sport", "winner", "olympic", "coin"],
    description="Round sport medal with raised rim, star emblem recess, and ribbon loop.",
    techniques=["polar_array", "guarded_fillet"],
    nominal_dimensions_mm={"diameter": 60.0, "thickness": 5.0, "loop_diameter": 12.0},
    difficulty="easy",
)

code = '''import cadquery as cq
import math

diameter = 60.0
thick = 5.0
loop_d = 12.0

# Disk
body = cq.Workplane("XY").circle(diameter / 2.0).extrude(thick)
try:
    body = body.edges(">Z or <Z").fillet(1.0)
except Exception:
    pass

# Raised rim ring: recess the inner face
recess = (
    cq.Workplane("XY", origin=(0, 0, thick - 0.8))
    .circle(diameter / 2.0 - 3)
    .extrude(1.0)
)
body = body.cut(recess)

# Five-point star emblem recess at center
outer_r = 12.0
inner_r = 5.0
star_pts = []
for i in range(10):
    r = outer_r if i % 2 == 0 else inner_r
    theta = math.radians(90 + 36 * i)
    star_pts.append((r * math.cos(theta), r * math.sin(theta)))
star = (
    cq.Workplane("XY", origin=(0, 0, thick - 1.0))
    .polyline(star_pts).close()
    .extrude(0.8)
)
body = body.cut(star)

# Top loop for ribbon
loop = (
    cq.Workplane("XZ", origin=(0, 0, diameter / 2.0 + loop_d / 2.0 - 2))
    .circle(loop_d / 2.0)
    .extrude(thick)
    .translate((0, -thick / 2.0, 0))
)
loop_hole = (
    cq.Workplane("XZ", origin=(0, 0, diameter / 2.0 + loop_d / 2.0 - 2))
    .circle(loop_d / 2.0 - 2)
    .extrude(thick + 2)
    .translate((0, -thick / 2.0 - 1, 0))
)
body = body.union(loop).cut(loop_hole)

result = body
'''
