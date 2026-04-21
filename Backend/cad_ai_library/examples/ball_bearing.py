from ..core.metadata import ExampleMetadata

metadata = ExampleMetadata(
    id="ball_bearing",
    name="Ball Bearing (Visual)",
    category="mechanical",
    keywords=["bearing", "ball", "race", "hub", "mechanical", "deep groove"],
    description="Simplified ball bearing — two races plus polar-arrayed ball spheres.",
    techniques=["polar_array", "safe_revolve"],
    nominal_dimensions_mm={"outer_diameter": 22.0, "inner_diameter": 8.0, "thickness": 7.0},
    difficulty="medium",
)

code = '''import cadquery as cq
import math

od = 22.0
id_ = 8.0
thick = 7.0
ball_count = 8

r_out = od / 2.0
r_in = id_ / 2.0
r_race_mid = (r_out + r_in) / 2.0
ball_d = (r_out - r_in) * 0.55

# Outer race (ring with inner groove)
outer_race = (
    cq.Workplane("XY")
    .circle(r_out).circle(r_race_mid + ball_d * 0.55)
    .extrude(thick)
)
# Inner race
inner_race = (
    cq.Workplane("XY")
    .circle(r_race_mid - ball_d * 0.55).circle(r_in)
    .extrude(thick)
)

body = outer_race.union(inner_race)

# Balls
for i in range(ball_count):
    theta = 360.0 / ball_count * i
    x = r_race_mid * math.cos(math.radians(theta))
    y = r_race_mid * math.sin(math.radians(theta))
    ball = cq.Workplane("XY", origin=(x, y, thick / 2.0)).sphere(ball_d / 2.0)
    body = body.union(ball)

result = body
'''
