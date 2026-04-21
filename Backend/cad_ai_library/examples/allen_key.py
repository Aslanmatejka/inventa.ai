from ..core.metadata import ExampleMetadata

metadata = ExampleMetadata(
    id="allen_key",
    name="Allen Key / Hex Wrench",
    category="tool",
    keywords=["allen", "key", "hex", "wrench", "tool", "l-shape"],
    description="L-shaped hex wrench with a short and long arm.",
    techniques=["polyline_profile"],
    nominal_dimensions_mm={"long_arm": 80.0, "short_arm": 25.0, "across_flats": 5.0},
    difficulty="easy",
)

code = '''import cadquery as cq
import math

long_arm = 80.0
short_arm = 25.0
af = 5.0  # across flats

r_corner = af / math.sqrt(3)
hex_pts = [(r_corner * math.cos(math.radians(30 + 60 * i)),
            r_corner * math.sin(math.radians(30 + 60 * i)))
           for i in range(6)]

# Long arm along +X
long = (
    cq.Workplane("YZ")
    .polyline(hex_pts).close()
    .extrude(long_arm)
)

# Short arm along +Z, at the -X end (origin)
short = (
    cq.Workplane("XY", origin=(0, 0, 0))
    .polyline(hex_pts).close()
    .extrude(short_arm)
)

# Small corner fillet sphere to blend the joint visually
joint = cq.Workplane("XY").sphere(af * 0.55)

body = long.union(short).union(joint)

result = body
'''
