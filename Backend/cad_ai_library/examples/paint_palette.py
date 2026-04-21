from ..core.metadata import ExampleMetadata

metadata = ExampleMetadata(
    id="paint_palette",
    name="Artist Paint Palette",
    category="art_supplies",
    keywords=["paint", "palette", "artist", "art", "mixing", "thumb"],
    description="Kidney-shaped artist paint palette with thumb hole and arrayed paint wells.",
    techniques=["polyline_profile"],
    nominal_dimensions_mm={"length": 300.0, "width": 220.0, "thickness": 8.0},
    difficulty="medium",
)

code = '''import cadquery as cq

length = 300.0
width = 220.0
thick = 8.0

# Kidney-shape outline via spline through control points
outline_pts = [
    (-length / 2.0, 0),
    (-length * 0.3, width / 2.0),
    (length * 0.1, width / 2.0 * 0.9),
    (length / 2.0, width / 4.0),
    (length / 2.0, -width / 4.0),
    (length * 0.1, -width / 2.0 * 0.9),
    (-length * 0.3, -width / 2.0),
]
body = (
    cq.Workplane("XY")
    .spline(outline_pts, periodic=True, makeWire=True)
    .toPending()
    .extrude(thick)
)

# Thumb hole
thumb = (
    cq.Workplane("XY", origin=(-length * 0.35, 0, -0.1))
    .circle(15.0)
    .extrude(thick + 0.2)
)
body = body.cut(thumb)

# Paint wells: grid of shallow round recesses
well_d = 22.0
well_depth = 4.0
well_pts = []
for i in range(-1, 3):
    for j in range(-1, 2):
        x = i * 35 + 10
        y = j * 40
        # Skip wells near the thumb hole and edges
        if x * x + y * y < 70 * 70 and x < 0:
            continue
        well_pts.append((x, y))

if well_pts:
    wells = (
        cq.Workplane("XY", origin=(0, 0, thick - well_depth))
        .pushPoints(well_pts)
        .circle(well_d / 2.0)
        .extrude(well_depth + 0.2)
    )
    body = body.cut(wells)

result = body
'''
