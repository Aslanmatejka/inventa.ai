from ..core.metadata import ExampleMetadata

metadata = ExampleMetadata(
    id="funnel_strainer",
    name="Strainer / Colander",
    category="container",
    keywords=["strainer", "colander", "sieve", "filter", "kitchen", "drain"],
    description="Hemispherical strainer with hex-pattern drain holes.",
    techniques=["safe_revolve", "shell_cavity"],
    nominal_dimensions_mm={"diameter": 180.0, "depth": 70.0, "wall": 2.0, "hole_diameter": 3.5},
    difficulty="medium",
)

code = '''import cadquery as cq
import math

diameter = 180.0
depth = 70.0
wall = 2.0
hole_d = 3.5
hole_pitch = 10.0

r_out = diameter / 2.0

# Hemisphere-like bowl via revolve (all X >= 0)
profile = (
    cq.Workplane("XZ")
    .moveTo(0, 0)
    .spline([(r_out * 0.5, depth * 0.15), (r_out * 0.9, depth * 0.6), (r_out, depth)])
    .lineTo(r_out + 6, depth)
    .lineTo(r_out + 6, depth + 4)
    .spline([(r_out * 0.9 - wall, depth * 0.6), (r_out * 0.5 - wall, depth * 0.15)])
    .lineTo(0, wall)
    .close()
)
body = profile.revolve(360)

# Hex grid of holes projected from +Z face
dx = hole_pitch
dy = hole_pitch * math.sqrt(3) / 2.0
pts = []
rows = int(r_out / dy) + 1
for j in range(-rows, rows + 1):
    y = j * dy
    x_off = 0 if j % 2 == 0 else dx / 2.0
    cols = int(r_out / dx) + 1
    for i in range(-cols, cols + 1):
        x = i * dx + x_off
        # Only keep holes that are inside the projected hemisphere near the bottom
        if x * x + y * y <= (r_out * 0.92) ** 2:
            pts.append((x, y))

if pts:
    cutters = (
        cq.Workplane("XY", origin=(0, 0, -1))
        .pushPoints(pts)
        .circle(hole_d / 2.0)
        .extrude(depth + 5)
    )
    body = body.cut(cutters)

result = body
'''
