from ..core.metadata import ExampleMetadata

metadata = ExampleMetadata(
    id="bolt",
    name="Hex Head Bolt",
    category="fastener",
    keywords=["bolt", "screw", "hex", "head", "fastener", "hardware", "m8"],
    description="Hex-head bolt with smooth shank and small tip chamfer (no helical thread).",
    techniques=["polar_array", "guarded_fillet"],
    nominal_dimensions_mm={"head_across_flats": 13.0, "shank_diameter": 8.0, "length": 40.0},
    difficulty="easy",
)

code = '''import cadquery as cq
import math

af = 13.0       # hex across flats
shank_d = 8.0
length = 40.0
head_h = 5.5

r_hex = af / math.sqrt(3)  # across corners radius
hex_pts = [(r_hex * math.cos(math.radians(30 + 60 * i)),
            r_hex * math.sin(math.radians(30 + 60 * i)))
           for i in range(6)]

# Hex head at Z=0..head_h
head = (
    cq.Workplane("XY")
    .polyline(hex_pts)
    .close()
    .extrude(head_h)
)
try:
    head = head.edges(">Z").chamfer(0.8)
except Exception:
    pass

# Shank
shank = (
    cq.Workplane("XY", origin=(0, 0, head_h))
    .circle(shank_d / 2.0)
    .extrude(length)
)
try:
    shank = shank.edges(">Z").chamfer(0.6)
except Exception:
    pass

body = head.union(shank)

result = body
'''
