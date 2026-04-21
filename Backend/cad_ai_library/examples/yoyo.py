from ..core.metadata import ExampleMetadata

metadata = ExampleMetadata(
    id="yoyo",
    name="Yo-Yo",
    category="toy",
    keywords=["yoyo", "yo-yo", "toy", "spinning", "game"],
    description="Two-halves yo-yo with string gap and central axle bore.",
    techniques=["safe_revolve"],
    nominal_dimensions_mm={"outer_diameter": 56.0, "width": 40.0, "string_gap": 3.5},
    difficulty="easy",
)

code = '''import cadquery as cq

outer_d = 56.0
width = 40.0
string_gap = 3.5
axle_d = 4.0

r_out = outer_d / 2.0
half_w = (width - string_gap) / 2.0

# Half profile (one disc) revolved
profile = (
    cq.Workplane("XZ")
    .moveTo(0, 0)
    .lineTo(r_out, 0)
    .spline([(r_out * 0.95, half_w * 0.5), (r_out * 0.5, half_w * 0.85), (0, half_w)])
    .close()
)
half1 = profile.revolve(360)

# Mirror the half to make the other side (translated by half_w + gap)
half2 = half1.mirror("XY").translate((0, 0, width))

body = half1.union(half2)

# Central axle bore
body = body.faces(">Z").workplane().hole(axle_d)

result = body
'''
