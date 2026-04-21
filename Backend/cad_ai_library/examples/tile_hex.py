from ..core.metadata import ExampleMetadata

metadata = ExampleMetadata(
    id="tile_hex",
    name="Hex Floor Tile",
    category="architecture",
    keywords=["tile", "hex", "hexagonal", "floor", "ceramic", "pattern"],
    description="Hexagonal floor tile with beveled top edge.",
    techniques=["polar_array", "guarded_fillet"],
    nominal_dimensions_mm={"across_flats": 100.0, "thickness": 8.0},
    difficulty="easy",
)

code = '''import cadquery as cq
import math

af = 100.0
thick = 8.0

r_corner = af / math.sqrt(3)
pts = [(r_corner * math.cos(math.radians(30 + 60 * i)),
        r_corner * math.sin(math.radians(30 + 60 * i)))
       for i in range(6)]

body = (
    cq.Workplane("XY")
    .polyline(pts).close()
    .extrude(thick)
)

try:
    body = body.edges(">Z").chamfer(min(1.5, thick * 0.2))
except Exception:
    pass

result = body
'''
