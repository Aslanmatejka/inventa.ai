from ..core.metadata import ExampleMetadata

metadata = ExampleMetadata(
    id="pedestal_bust",
    name="Pedestal Bust",
    category="sculpture",
    keywords=["bust", "sculpture", "pedestal", "statue", "head", "art", "figurine"],
    description="Stylized human bust: spherical head on shoulder mass atop a classical pedestal.",
    techniques=["boolean_union", "revolve"],
    nominal_dimensions_mm={"base_width": 140.0, "total_height": 340.0},
    difficulty="medium",
)

code = '''import cadquery as cq

# Pedestal (revolved classical profile)
ped_pts = [
    (0, 0), (70, 0), (70, 20), (55, 30), (50, 150),
    (55, 160), (65, 170), (0, 170),
]
ped = cq.Workplane("XZ").polyline(ped_pts).close().revolve(360, (0, 0, 0), (0, 1, 0))

# Shoulders (trapezoid block)
shoulder_pts = [(-60, 0), (60, 0), (40, 60), (-40, 60)]
shoulders = (cq.Workplane("XZ").polyline(shoulder_pts).close()
             .extrude(40, both=True)
             .translate((0, 0, 170)))
try:
    shoulders = shoulders.edges().fillet(8.0)
except Exception:
    pass

# Neck
neck = (cq.Workplane("XY").workplane(offset=230)
        .circle(18).extrude(30))

# Head (sphere, slightly squashed)
head = (cq.Workplane("XY").workplane(offset=295)
        .sphere(35))

body = ped.union(shoulders).union(neck).union(head)

# Eye socket hints
for x in [-12, 12]:
    eye = (cq.Workplane("XY").workplane(offset=302)
           .center(x, 28).circle(5).extrude(4))
    body = body.cut(eye)

result = body
'''
