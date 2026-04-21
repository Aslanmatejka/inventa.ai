from ..core.metadata import ExampleMetadata

metadata = ExampleMetadata(
    id="water_bottle",
    name="Water Bottle",
    category="container",
    keywords=["bottle", "water", "water bottle", "drink", "reusable", "flask"],
    description="Sports water bottle: revolved cylindrical body with shoulder taper and threaded neck.",
    techniques=["revolve"],
    nominal_dimensions_mm={"diameter": 70.0, "height": 250.0},
    difficulty="easy",
)

code = '''import cadquery as cq

# Outer profile (revolved)
outer_pts = [
    (0, 0),
    (35, 0),        # base edge
    (35, 190),      # straight body
    (30, 215),      # shoulder
    (15, 225),      # shoulder-to-neck
    (15, 250),      # neck top
    (0, 250),
]
outer = cq.Workplane("XZ").polyline(outer_pts).close().revolve(360, (0, 0, 0), (0, 1, 0))

# Inner hollow
inner_pts = [
    (0, 3),
    (32, 3),
    (32, 188),
    (28, 212),
    (12, 223),
    (12, 250),
    (0, 250),
]
inner = cq.Workplane("XZ").polyline(inner_pts).close().revolve(360, (0, 0, 0), (0, 1, 0))
body = outer.cut(inner)

# Thread ridges on neck (stacked rings, no helix)
for z in [228, 234, 240]:
    ring = (cq.Workplane("XY").workplane(offset=z)
            .circle(16).circle(15).extrude(2))
    body = body.union(ring)

result = body
'''
