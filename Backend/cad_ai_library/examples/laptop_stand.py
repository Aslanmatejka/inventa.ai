from ..core.metadata import ExampleMetadata

metadata = ExampleMetadata(
    id="laptop_stand",
    name="Laptop Stand",
    category="furniture",
    keywords=["laptop", "stand", "riser", "desk", "ergonomic", "notebook"],
    description="Angled laptop riser with two support arms and a front lip.",
    techniques=["boolean_union", "guarded_fillet"],
    nominal_dimensions_mm={"width": 300.0, "depth": 220.0, "height": 140.0},
    difficulty="medium",
)

code = '''import cadquery as cq

w = 300.0
d = 220.0
h = 140.0
t = 10.0

# Two triangular side arms as polygons in XZ
pts = [(-d/2, 0), (d/2, 0), (d/2, h * 0.3), (-d/2, h)]
left = (cq.Workplane("XZ").workplane(offset=-w/2)
        .polyline(pts).close().extrude(t))
right = (cq.Workplane("XZ").workplane(offset=w/2 - t)
         .polyline(pts).close().extrude(t))

# Angled top plate
plate_len = (d ** 2 + (h - h * 0.3) ** 2) ** 0.5
import math
angle = math.degrees(math.atan2(h - h * 0.3, d))
plate = (cq.Workplane("XY").box(plate_len, w - 2 * t, t, centered=(True, True, False))
         .rotate((0, 0, 0), (0, 1, 0), angle)
         .translate((0, 0, h * 0.3 + (h - h*0.3)/2)))

# Front lip
lip = (cq.Workplane("XY").workplane(offset=h * 0.3)
       .center(-d/2 + 8, 0).box(12, w - 2 * t, 18, centered=(False, True, False)))

body = left.union(right).union(plate).union(lip)

try:
    body = body.edges("|Y").fillet(3.0)
except Exception:
    pass

result = body
'''
