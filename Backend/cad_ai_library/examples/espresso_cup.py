from ..core.metadata import ExampleMetadata

metadata = ExampleMetadata(
    id="espresso_cup",
    name="Espresso Cup",
    category="drinkware",
    keywords=["espresso", "cup", "coffee", "mug", "drinkware", "demitasse"],
    description="Small espresso cup with saucer-compatible flat bottom and single loop handle.",
    techniques=["safe_revolve"],
    nominal_dimensions_mm={"diameter": 55.0, "height": 55.0, "wall": 2.2},
    difficulty="medium",
)

code = '''import cadquery as cq

diameter = 55.0
height = 55.0
wall = 2.2

r = diameter / 2.0

# Cup profile (all X >= 0)
profile = (
    cq.Workplane("XZ")
    .moveTo(0, 0)
    .lineTo(r - 4, 0)
    .lineTo(r, 6)
    .lineTo(r, height)
    .lineTo(r - wall, height)
    .lineTo(r - wall, 6 + wall)
    .lineTo(r - 4 - wall * 0.5, wall)
    .lineTo(0, wall)
    .close()
)
body = profile.revolve(360)

# Handle: torus-like loop on +X side
handle_outer = (
    cq.Workplane("XZ", origin=(r + 2, 0, height / 2.0))
    .circle(height * 0.35)
    .extrude(4.0)
    .translate((0, -2, 0))
)
handle_hole = (
    cq.Workplane("XZ", origin=(r + 2, 0, height / 2.0))
    .circle(height * 0.35 - 5)
    .extrude(5.0)
    .translate((0, -2.5, 0))
)
handle = handle_outer.cut(handle_hole)

body = body.union(handle)

result = body
'''
