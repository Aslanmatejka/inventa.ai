from ..core.metadata import ExampleMetadata

metadata = ExampleMetadata(
    id="steering_wheel",
    name="Steering Wheel",
    category="automotive",
    keywords=["steering", "wheel", "car", "driving", "automotive", "rim"],
    description="Three-spoke steering wheel with torus rim, center hub, and horn pad.",
    techniques=["revolve", "polar_pattern"],
    nominal_dimensions_mm={"diameter": 380.0, "rim_thickness": 32.0},
    difficulty="medium",
)

code = '''import cadquery as cq
import math

rim_R = 175.0   # center-of-rim radius
rim_r = 16.0    # tube radius
hub_r = 45.0

# Rim: revolve a circle offset from the Z axis around Z axis
rim_profile = cq.Workplane("XZ").moveTo(rim_R, rim_r).circle(rim_r)
rim = rim_profile.revolve(360)

# Three spokes
spokes = None
for i in range(3):
    ang = 90 + i * 120  # one up, two bottom
    spoke = (cq.Workplane("XY")
             .rect(rim_R, 14).extrude(12)
             .translate(((rim_R / 2) * math.cos(math.radians(ang)),
                         (rim_R / 2) * math.sin(math.radians(ang)), 0)))
    spoke = spoke.rotate((0, 0, 0), (0, 0, 1), ang)
    spokes = spoke if spokes is None else spokes.union(spoke)

# Hub
hub = cq.Workplane("XY").circle(hub_r).extrude(30)

# Horn pad (rounded square)
pad = (cq.Workplane("XY").workplane(offset=22)
       .rect(70, 70).extrude(10))
try:
    pad = pad.edges("|Z").fillet(12.0)
except Exception:
    pass

body = rim.union(spokes).union(hub).union(pad)

# Column bore
bore = cq.Workplane("XY").circle(12).extrude(40)
body = body.cut(bore)

result = body
'''
