from ..core.metadata import ExampleMetadata

metadata = ExampleMetadata(
    id="tractor_wheel",
    name="Tractor Wheel with Lugs",
    category="agriculture",
    keywords=["tractor", "wheel", "tire", "agriculture", "farm", "lug"],
    description="Large tractor rear wheel with deep diagonal lug treads for traction.",
    techniques=["safe_revolve", "polar_array"],
    nominal_dimensions_mm={"outer_diameter": 500.0, "width": 180.0, "rim_diameter": 300.0, "lug_count": 24},
    difficulty="medium",
)

code = '''import cadquery as cq
import math

od = 500.0
width = 180.0
rim_d = 300.0
lug_count = 24

r_out = od / 2.0
r_rim = rim_d / 2.0

# Tire + rim as a revolved profile (simplified)
profile = (
    cq.Workplane("XZ")
    .moveTo(r_rim, 0)
    .lineTo(r_out - 10, 0)
    .lineTo(r_out, 10)
    .lineTo(r_out, width - 10)
    .lineTo(r_out - 10, width)
    .lineTo(r_rim, width)
    .lineTo(r_rim, width * 0.75)
    .lineTo(r_rim - 20, width * 0.7)
    .lineTo(r_rim - 20, width * 0.3)
    .lineTo(r_rim, width * 0.25)
    .close()
)
body = profile.revolve(360)

# Diagonal lug treads
for i in range(lug_count):
    theta = 360.0 / lug_count * i
    x = r_out * math.cos(math.radians(theta))
    y = r_out * math.sin(math.radians(theta))
    v = (math.cos(math.radians(theta)), math.sin(math.radians(theta)), 0)
    lug = (
        cq.Workplane(cq.Plane(origin=(x, y, width / 2.0),
                              xDir=(-v[1], v[0], 0),
                              normal=v))
        .rect(18, width * 0.7)
        .extrude(20)
        .rotate((x, y, width / 2.0), (x, y, width / 2.0 + 1), 25)
    )
    body = body.union(lug)

# Center hub bolts (5)
hub_r = r_rim * 0.3
for i in range(5):
    theta = 72 * i
    bx = hub_r * math.cos(math.radians(theta))
    by = hub_r * math.sin(math.radians(theta))
    bolt = (
        cq.Workplane("XY", origin=(bx, by, width * 0.4))
        .circle(4.0)
        .extrude(width * 0.2)
    )
    body = body.union(bolt)

# Central axle hole through the hub
axle = (
    cq.Workplane("XY", origin=(0, 0, -1))
    .circle(35.0)
    .extrude(width + 2)
)
body = body.cut(axle)

result = body
'''
