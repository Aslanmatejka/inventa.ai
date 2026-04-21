from ..core.metadata import ExampleMetadata

metadata = ExampleMetadata(
    id="bird_feeder",
    name="Bird Feeder",
    category="outdoor",
    keywords=["bird", "feeder", "seed", "garden", "bird feeder", "outdoor"],
    description="Tube-style bird feeder with peaked roof, seed tube, and perch ring.",
    techniques=["revolve", "boolean_union"],
    nominal_dimensions_mm={"height": 260.0, "tube_dia": 70.0},
    difficulty="medium",
)

code = '''import cadquery as cq

tube_r = 35.0
tube_h = 180.0
base_r = 50.0

# Seed tube (hollow)
tube = cq.Workplane("XY").circle(tube_r).circle(tube_r - 2).extrude(tube_h)

# Base dish
base_pts = [(0, 0), (base_r, 0), (base_r, 10), (tube_r + 2, 18), (0, 18)]
base = cq.Workplane("XZ").polyline(base_pts).close().revolve(360, (0, 0, 0), (0, 1, 0))

# Peaked roof
roof_pts = [(0, 0), (base_r, 0), (0, 35)]
roof = (cq.Workplane("XZ").polyline(roof_pts).close()
        .revolve(360, (0, 0, 0), (0, 1, 0))
        .translate((0, 0, tube_h)))

body = tube.union(base).union(roof)

# Two feeding ports
for ang in [0, 180]:
    import math
    x = (tube_r + 2) * math.cos(math.radians(ang))
    y = (tube_r + 2) * math.sin(math.radians(ang))
    port = (cq.Workplane("XY").workplane(offset=25)
            .center(x, y).circle(4).extrude(4))
    body = body.cut(port)

# Perch ring
perch = (cq.Workplane("XY").workplane(offset=22)
         .circle(tube_r + 12).circle(tube_r + 10).extrude(2))
body = body.union(perch)

# Hanging loop at top
loop = (cq.Workplane("YZ").workplane(offset=0)
        .center(0, tube_h + 40).circle(8).circle(6).extrude(2, both=True))
body = body.union(loop)

result = body
'''
