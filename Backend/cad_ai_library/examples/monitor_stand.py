from ..core.metadata import ExampleMetadata

metadata = ExampleMetadata(
    id="monitor_stand",
    name="Monitor Riser Stand",
    category="furniture",
    keywords=["monitor", "stand", "riser", "desk", "shelf", "display"],
    description="Desk monitor riser shelf with two side panels and a flat top.",
    techniques=["boolean_union", "guarded_fillet"],
    nominal_dimensions_mm={"width": 600.0, "depth": 250.0, "height": 120.0},
    difficulty="easy",
)

code = '''import cadquery as cq

w = 600.0
d = 250.0
h = 120.0
t = 15.0

top = cq.Workplane("XY").workplane(offset=h - t).box(w, d, t, centered=(True, True, False))
left = cq.Workplane("XY").center(-w/2 + t/2, 0).box(t, d, h - t, centered=(True, True, False))
right = cq.Workplane("XY").center(w/2 - t/2, 0).box(t, d, h - t, centered=(True, True, False))

body = top.union(left).union(right)

# Cable cutout in top
cable = (cq.Workplane("XY").workplane(offset=h - t - 1)
         .center(0, d/2 - 30).rect(80, 20).extrude(t + 2))
body = body.cut(cable)

try:
    body = body.edges("|Y").fillet(3.0)
except Exception:
    pass

result = body
'''
