from ..core.metadata import ExampleMetadata

metadata = ExampleMetadata(
    id="lens_mount",
    name="Camera Lens Mount Ring",
    category="optics",
    keywords=["lens", "mount", "camera", "optics", "bayonet", "ring"],
    description="Thin lens mount ring with three bayonet tabs on the inside.",
    techniques=["polar_array", "guarded_fillet"],
    nominal_dimensions_mm={"outer_diameter": 48.0, "inner_diameter": 42.0, "thickness": 4.0},
    difficulty="medium",
)

code = '''import cadquery as cq
import math

od = 48.0
id_ = 42.0
thick = 4.0
tab_count = 3
tab_arc = 22.0  # degrees
tab_depth = 1.5

r_out = od / 2.0
r_in = id_ / 2.0

body = (
    cq.Workplane("XY")
    .circle(r_out).circle(r_in)
    .extrude(thick)
)

# Bayonet tabs sticking inward
for i in range(tab_count):
    theta = 360.0 / tab_count * i
    # Build a wedge-shaped tab by intersecting an annulus with an angular sector
    r_tab_in = r_in - tab_depth
    start = theta - tab_arc / 2.0
    pts = [(0, 0)]
    steps = 12
    for k in range(steps + 1):
        a = math.radians(start + tab_arc * k / steps)
        pts.append((r_in * math.cos(a), r_in * math.sin(a)))
    pts.append((0, 0))
    outer_wedge = (
        cq.Workplane("XY")
        .polyline(pts).close()
        .extrude(thick * 0.5)
    )
    pts_in = [(0, 0)]
    for k in range(steps + 1):
        a = math.radians(start + tab_arc * k / steps)
        pts_in.append((r_tab_in * math.cos(a), r_tab_in * math.sin(a)))
    pts_in.append((0, 0))
    inner_wedge = (
        cq.Workplane("XY")
        .polyline(pts_in).close()
        .extrude(thick * 0.5)
    )
    tab = outer_wedge.cut(inner_wedge)
    body = body.union(tab)

try:
    body = body.edges(">Z or <Z").fillet(min(0.6, thick * 0.2))
except Exception:
    pass

result = body
'''
