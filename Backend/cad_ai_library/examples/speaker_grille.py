from ..core.metadata import ExampleMetadata

metadata = ExampleMetadata(
    id="speaker_grille",
    name="Speaker Grille",
    category="electronics",
    keywords=["speaker", "grille", "mesh", "audio", "cover", "driver"],
    description="Circular speaker grille with hex pattern of through-holes.",
    techniques=["polar_array", "guarded_fillet"],
    nominal_dimensions_mm={"diameter": 80.0, "thickness": 3.0, "hole_diameter": 3.0, "spacing": 5.0},
    difficulty="medium",
)

code = '''import cadquery as cq
import math

diameter = 80.0
thick = 3.0
hole_d = 3.0
spacing = 5.0
mount_hole_d = 3.5
mount_ring_r = diameter / 2.0 - 4.0

body = cq.Workplane("XY").circle(diameter / 2.0).extrude(thick)
try:
    body = body.edges().fillet(min(0.8, thick * 0.25))
except Exception:
    pass

# Hex grid of holes within an inner radius
inner_r = diameter / 2.0 - 8.0
dx = spacing
dy = spacing * math.sqrt(3) / 2.0
points = []
rows = int(inner_r / dy) + 1
for j in range(-rows, rows + 1):
    y = j * dy
    x_off = 0 if j % 2 == 0 else dx / 2.0
    cols = int(inner_r / dx) + 1
    for i in range(-cols, cols + 1):
        x = i * dx + x_off
        if x * x + y * y <= inner_r * inner_r:
            points.append((x, y))

if points:
    body = (
        body.faces(">Z").workplane()
        .pushPoints(points)
        .hole(hole_d)
    )

# Four mounting holes on a circle
mount_pts = [(mount_ring_r * math.cos(math.radians(a)),
              mount_ring_r * math.sin(math.radians(a)))
             for a in (45, 135, 225, 315)]
body = (
    body.faces(">Z").workplane()
    .pushPoints(mount_pts)
    .hole(mount_hole_d)
)

result = body
'''
