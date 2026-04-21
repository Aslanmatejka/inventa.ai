from ..core.metadata import ExampleMetadata

metadata = ExampleMetadata(
    id="harmonica",
    name="Diatonic Harmonica",
    category="musical",
    keywords=["harmonica", "mouth organ", "music", "instrument", "blues", "reed"],
    description="Rectangular diatonic harmonica body with top/bottom cover plates and 10-hole row.",
    techniques=["guarded_fillet"],
    nominal_dimensions_mm={"length": 100.0, "width": 28.0, "height": 22.0, "hole_count": 10},
    difficulty="easy",
)

code = '''import cadquery as cq

length = 100.0
width = 28.0
height = 22.0
hole_count = 10

# Main comb body
body = cq.Workplane("XY").box(length, width, height, centered=(True, True, False))
try:
    body = body.edges("|X").fillet(3.0)
except Exception:
    pass
try:
    body = body.edges("|Z").fillet(1.5)
except Exception:
    pass

# 10 blow holes on the front face (-Y)
hole_spacing = length / (hole_count + 1)
hole_pts = []
for i in range(hole_count):
    x = -length / 2.0 + hole_spacing * (i + 1)
    hole_pts.append((x, height / 2.0))
cutter = (
    cq.Workplane("XZ", origin=(0, -width / 2.0 - 0.1, 0))
    .pushPoints(hole_pts)
    .rect(5.5, 3.5)
    .extrude(6)
)
body = body.cut(cutter)

# Screws on top and bottom covers (two each side)
for sz in (height - 1.5, 1.5):
    for sx in (-length / 2.0 + 10, length / 2.0 - 10):
        screw = (
            cq.Workplane("XY", origin=(sx, 0, sz))
            .circle(1.5)
            .extrude(1.5)
        )
        body = body.union(screw)

result = body
'''
