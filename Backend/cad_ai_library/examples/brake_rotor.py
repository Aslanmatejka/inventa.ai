from ..core.metadata import ExampleMetadata

metadata = ExampleMetadata(
    id="brake_rotor",
    name="Brake Rotor Disc",
    category="automotive",
    keywords=["brake", "rotor", "disc", "car", "automotive", "wheel", "stopping"],
    description="Ventilated brake disc with hub, friction surface, and drilled cooling holes.",
    techniques=["boolean_cut", "polar_pattern"],
    nominal_dimensions_mm={"diameter": 320.0, "thickness": 28.0},
    difficulty="medium",
)

code = '''import cadquery as cq
import math

outer_r = 160.0
inner_r = 90.0
disc_t = 28.0
hub_r = 55.0
hub_h = 45.0

# Friction disc
disc = cq.Workplane("XY").circle(outer_r).circle(inner_r).extrude(disc_t)

# Internal vent cavity (simplified: thin disc cut radially would be complex,
# use inner friction band only)
vent = (cq.Workplane("XY").workplane(offset=disc_t * 0.35)
        .circle(outer_r - 8).circle(inner_r + 8).extrude(disc_t * 0.3))
disc = disc.cut(vent)

# Hub bell
hub = (cq.Workplane("XY").circle(hub_r).extrude(hub_h))
hub_bore = cq.Workplane("XY").circle(35).extrude(hub_h)
hub = hub.cut(hub_bore)

# Connect hub to disc with thin web
web = (cq.Workplane("XY").workplane(offset=hub_h - 8)
       .circle(inner_r + 5).circle(hub_r).extrude(8))

body = disc.union(web).union(hub)

# Drilled cooling holes (pattern of 12)
for i in range(12):
    ang = i * 30
    x = (outer_r - 25) * math.cos(math.radians(ang))
    y = (outer_r - 25) * math.sin(math.radians(ang))
    hole = (cq.Workplane("XY").center(x, y).circle(5).extrude(disc_t + 2))
    body = body.cut(hole)

# Lug bolt holes on hub (5)
for i in range(5):
    ang = i * 72
    x = 42 * math.cos(math.radians(ang))
    y = 42 * math.sin(math.radians(ang))
    hole = (cq.Workplane("XY").center(x, y).circle(6).extrude(hub_h + 2))
    body = body.cut(hole)

result = body
'''
