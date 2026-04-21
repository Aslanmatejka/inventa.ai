from ..core.metadata import ExampleMetadata

metadata = ExampleMetadata(
    id="life_ring",
    name="Life Ring Buoy",
    category="marine",
    keywords=["life", "ring", "buoy", "lifesaver", "marine", "rescue", "boat"],
    description="Ring-shaped life buoy: torus body with four rope attachment points.",
    techniques=["safe_revolve", "polar_array"],
    nominal_dimensions_mm={"outer_diameter": 700.0, "tube_diameter": 110.0},
    difficulty="easy",
)

code = '''import cadquery as cq
import math

outer_d = 700.0
tube_d = 110.0

r_center = (outer_d - tube_d) / 2.0  # centerline radius
r_tube = tube_d / 2.0

# Torus via revolving a circle off-axis (all X >= 0).
torus_profile = (
    cq.Workplane("XZ")
    .moveTo(r_center, r_tube)
    .circle(r_tube)
)
body = torus_profile.revolve(360)

# Four rope attachment lugs around the outer circumference
for i in range(4):
    theta = 90 * i
    x = (r_center + r_tube * 0.6) * math.cos(math.radians(theta))
    y = (r_center + r_tube * 0.6) * math.sin(math.radians(theta))
    v = (math.cos(math.radians(theta)), math.sin(math.radians(theta)), 0)
    lug = (
        cq.Workplane(cq.Plane(origin=(x, y, r_tube),
                              xDir=(-v[1], v[0], 0),
                              normal=v))
        .rect(20, 12)
        .extrude(14)
    )
    lug_hole = (
        cq.Workplane(cq.Plane(origin=(x, y, r_tube),
                              xDir=(-v[1], v[0], 0),
                              normal=v))
        .circle(4)
        .extrude(16)
    )
    body = body.union(lug).cut(lug_hole)

result = body
'''
