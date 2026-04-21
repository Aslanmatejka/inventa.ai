from ..core.metadata import ExampleMetadata

metadata = ExampleMetadata(
    id="nut",
    name="Hex Nut",
    category="fastener",
    keywords=["nut", "hex", "fastener", "hardware", "m8", "thread"],
    description="Simple hex nut with through-hole (no helical thread).",
    techniques=["polar_array", "guarded_fillet"],
    nominal_dimensions_mm={"across_flats": 13.0, "hole_diameter": 8.0, "thickness": 6.5},
    difficulty="easy",
)

code = '''import cadquery as cq
import math

af = 13.0
hole_d = 8.0
thick = 6.5

r_hex = af / math.sqrt(3)
hex_pts = [(r_hex * math.cos(math.radians(30 + 60 * i)),
            r_hex * math.sin(math.radians(30 + 60 * i)))
           for i in range(6)]

body = (
    cq.Workplane("XY")
    .polyline(hex_pts)
    .close()
    .extrude(thick)
)

# Through hole
body = body.faces(">Z").workplane().hole(hole_d)

# Chamfer top and bottom corners for that classic nut look
try:
    body = body.edges(">Z or <Z").chamfer(0.8)
except Exception:
    pass

result = body
'''
