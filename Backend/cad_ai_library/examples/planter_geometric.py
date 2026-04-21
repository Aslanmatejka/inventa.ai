from ..core.metadata import ExampleMetadata

metadata = ExampleMetadata(
    id="planter_geometric",
    name="Geometric Planter",
    category="decorative",
    keywords=["planter", "pot", "geometric", "faceted", "plant", "decor"],
    description="Hexagonal faceted decorative planter with tapered sides and drainage hole.",
    techniques=["polyline_profile", "loft_frustum", "shell_cavity"],
    nominal_dimensions_mm={"top_across_flats": 140.0, "bottom_across_flats": 90.0, "height": 120.0, "wall": 3.5},
    difficulty="medium",
)

code = '''import cadquery as cq
import math

top_af = 140.0
bot_af = 90.0
height = 120.0
wall = 3.5

def hex_points(af):
    r = af / math.sqrt(3)
    return [(r * math.cos(math.radians(30 + 60 * i)),
             r * math.sin(math.radians(30 + 60 * i)))
            for i in range(6)]

bot_pts = hex_points(bot_af)
top_pts = hex_points(top_af)

# Tapered faceted body via loft
body = (
    cq.Workplane("XY")
    .polyline(bot_pts).close()
    .workplane(offset=height)
    .polyline(top_pts).close()
    .loft(combine=True)
)

# Interior cavity (slightly scaled down profiles)
bot_in = hex_points(bot_af - 2 * wall)
top_in = hex_points(top_af - 2 * wall)
cavity = (
    cq.Workplane("XY", origin=(0, 0, wall))
    .polyline(bot_in).close()
    .workplane(offset=height - wall + 0.1)
    .polyline(top_in).close()
    .loft(combine=True)
)
body = body.cut(cavity)

# Drainage hole
drain = (
    cq.Workplane("XY", origin=(0, 0, -0.1))
    .circle(5.0)
    .extrude(wall + 0.3)
)
body = body.cut(drain)

result = body
'''
