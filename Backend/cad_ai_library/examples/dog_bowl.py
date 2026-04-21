from ..core.metadata import ExampleMetadata

metadata = ExampleMetadata(
    id="dog_bowl",
    name="Pet Food Bowl",
    category="container",
    keywords=["dog", "cat", "pet", "bowl", "food", "water", "animal"],
    description="Wide, stable pet bowl with non-slip base ring.",
    techniques=["safe_revolve"],
    nominal_dimensions_mm={"top_diameter": 200.0, "base_diameter": 160.0, "height": 70.0, "wall": 4.0},
    difficulty="easy",
)

code = '''import cadquery as cq

r_top = 100.0
r_base = 80.0
height = 70.0
wall = 4.0
base_thick = 6.0

# Outer profile — trapezoidal with slight belly
outer = (
    cq.Workplane("XZ")
    .moveTo(0, 0)
    .lineTo(r_base, 0)
    .spline([(r_base + 8, height * 0.3), (r_top, height)])
    .lineTo(0, height)
    .close()
)
bowl = outer.revolve(360)

# Cavity
inner = (
    cq.Workplane("XZ")
    .moveTo(0, base_thick)
    .lineTo(r_base - wall, base_thick)
    .spline([(r_base + 8 - wall, height * 0.3), (r_top - wall, height)])
    .lineTo(0, height)
    .close()
)
cavity = inner.revolve(360)
body = bowl.cut(cavity)

# Non-slip ring groove on the bottom
groove = (
    cq.Workplane("XY")
    .circle(r_base * 0.75)
    .circle(r_base * 0.65)
    .extrude(0.8)
)
body = body.cut(groove)

result = body
'''
