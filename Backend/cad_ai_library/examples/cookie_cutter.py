from ..core.metadata import ExampleMetadata

metadata = ExampleMetadata(
    id="cookie_cutter",
    name="Star Cookie Cutter",
    category="accessory",
    keywords=["cookie", "cutter", "baking", "star", "kitchen", "mold"],
    description="Five-point star cookie cutter — thin-wall star outline with top reinforcement ring.",
    techniques=["polar_array", "polyline_profile"],
    nominal_dimensions_mm={"outer_diameter": 80.0, "height": 28.0, "wall": 1.2},
    difficulty="medium",
)

code = '''import cadquery as cq
import math

outer_r = 40.0
inner_r = 16.0
points = 5
height = 28.0
wall = 1.2

# Build star outline
outer_pts = []
for i in range(2 * points):
    r = outer_r if i % 2 == 0 else inner_r
    theta = math.radians(90 + 180.0 / points * i)
    outer_pts.append((r * math.cos(theta), r * math.sin(theta)))

outer_star = (
    cq.Workplane("XY")
    .polyline(outer_pts).close()
    .extrude(height)
)

# Inner star (shrunk by wall thickness)
inner_pts = []
for (x, y) in outer_pts:
    # Simple radial shrink
    d = math.hypot(x, y)
    s = (d - wall) / d
    inner_pts.append((x * s, y * s))

inner_star = (
    cq.Workplane("XY")
    .polyline(inner_pts).close()
    .extrude(height + 0.1)
)

body = outer_star.cut(inner_star)

# Top reinforcement ring (flat cap around the outline)
cap = (
    cq.Workplane("XY", origin=(0, 0, height - 3))
    .polyline(outer_pts).close()
    .extrude(3)
)
cap_hole = (
    cq.Workplane("XY", origin=(0, 0, height - 3.1))
    .polyline([(x * 0.72, y * 0.72) for (x, y) in outer_pts]).close()
    .extrude(3.3)
)
cap = cap.cut(cap_hole)
body = body.union(cap)

result = body
'''
