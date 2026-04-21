from ..core.metadata import ExampleMetadata

metadata = ExampleMetadata(
    id="sundial",
    name="Sundial",
    category="decorative",
    keywords=["sundial", "sun", "dial", "garden", "clock", "time"],
    description="Horizontal sundial with round dial plate and triangular gnomon.",
    techniques=["boolean_union", "guarded_fillet"],
    nominal_dimensions_mm={"diameter": 200.0, "gnomon_height": 80.0},
    difficulty="easy",
)

code = '''import cadquery as cq

plate_r = 100.0
plate_t = 8.0

plate = cq.Workplane("XY").circle(plate_r).extrude(plate_t)
try:
    plate = plate.edges(">Z").fillet(1.5)
except Exception:
    pass

# Triangular gnomon (right triangle in XZ)
gnomon_pts = [(-plate_r * 0.7, 0), (plate_r * 0.7, 0), (-plate_r * 0.7, 80)]
gnomon = (cq.Workplane("XZ").workplane(offset=3)
          .polyline(gnomon_pts).close().extrude(-6))
gnomon = gnomon.translate((0, 0, plate_t))

body = plate.union(gnomon)

# Hour marker slots around the rim
import math
for i in range(12):
    ang = i * 30
    x = (plate_r - 8) * math.cos(math.radians(ang))
    y = (plate_r - 8) * math.sin(math.radians(ang))
    marker = (cq.Workplane("XY").workplane(offset=plate_t - 1)
              .center(x, y).rect(2, 8).extrude(1.5))
    marker = marker.rotate((x, y, 0), (x, y, 1), ang)
    body = body.cut(marker)

result = body
'''
