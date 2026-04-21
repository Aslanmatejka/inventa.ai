from ..core.metadata import ExampleMetadata

metadata = ExampleMetadata(
    id="paint_can",
    name="Paint Can",
    category="container",
    keywords=["paint", "can", "bucket", "pail", "lid", "steel"],
    description="Cylindrical paint can with rolled rim, wire handle eyes, and press-in lid groove.",
    techniques=["safe_revolve"],
    nominal_dimensions_mm={"diameter": 180.0, "height": 200.0, "wall": 1.5},
    difficulty="medium",
)

code = '''import cadquery as cq

diameter = 180.0
height = 200.0
wall = 1.5

r = diameter / 2.0

# Revolve profile: body + top rolled rim + inner lid channel
profile = (
    cq.Workplane("XZ")
    .moveTo(0, 0)
    .lineTo(r, 0)
    .lineTo(r, height - 8)
    .lineTo(r + 3, height - 4)
    .lineTo(r + 3, height + 2)
    .lineTo(r - 3, height + 2)
    .lineTo(r - 3, height - 3)
    .lineTo(r - 6, height - 3)
    .lineTo(r - 6, wall)
    .lineTo(0, wall)
    .close()
)
body = profile.revolve(360)

# Two handle eyes (small loops on opposite sides)
for dx in (-r - 2, r + 2):
    eye_outer = (
        cq.Workplane("YZ", origin=(dx, 0, height * 0.85))
        .circle(5.0)
        .extrude(3)
    )
    eye_hole = (
        cq.Workplane("YZ", origin=(dx, 0, height * 0.85))
        .circle(2.0)
        .extrude(4)
    )
    body = body.union(eye_outer).cut(eye_hole)

result = body
'''
