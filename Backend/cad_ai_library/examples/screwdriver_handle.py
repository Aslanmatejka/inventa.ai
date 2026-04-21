from ..core.metadata import ExampleMetadata

metadata = ExampleMetadata(
    id="screwdriver_handle",
    name="Screwdriver Handle",
    category="mechanical",
    keywords=["screwdriver", "handle", "grip", "tool", "driver"],
    description="Ergonomic screwdriver handle with grip flutes and hex shaft socket.",
    techniques=["safe_revolve", "polar_array"],
    nominal_dimensions_mm={"length": 90.0, "max_diameter": 32.0, "shaft_socket_across_flats": 6.35},
    difficulty="medium",
)

code = '''import cadquery as cq
import math

length = 90.0
r_max = 16.0
r_end = 10.0
socket_af = 6.35  # 1/4" hex
socket_depth = 18.0

# Barrel profile revolved (all X >= 0)
profile = (
    cq.Workplane("XZ")
    .moveTo(0, 0)
    .lineTo(r_end, 0)
    .spline([(r_max, length * 0.35), (r_max, length * 0.65), (r_end, length)])
    .lineTo(0, length)
    .close()
)
body = profile.revolve(360)

# Grip flutes
flute_count = 10
flute_r = 1.5
for i in range(flute_count):
    theta = 360.0 / flute_count * i
    cutter = (
        cq.Workplane("XY", origin=(r_max - 0.3, 0, length * 0.35))
        .circle(flute_r)
        .extrude(length * 0.3)
        .rotate((0, 0, 0), (0, 0, 1), theta)
    )
    body = body.cut(cutter)

# Hex socket on the bottom face
hex_pts = [(socket_af / math.sqrt(3) * math.cos(math.radians(60 * i)),
            socket_af / math.sqrt(3) * math.sin(math.radians(60 * i)))
           for i in range(6)]
hex_cut = (
    cq.Workplane("XY")
    .polyline(hex_pts)
    .close()
    .extrude(socket_depth)
)
body = body.cut(hex_cut)

result = body
'''
