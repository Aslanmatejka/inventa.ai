from ..core.metadata import ExampleMetadata

metadata = ExampleMetadata(
    id="bowl",
    name="Shallow Bowl",
    category="container",
    keywords=["bowl", "dish", "shallow", "kitchen", "soup", "salad", "serving"],
    description="Revolved bowl profile with thick base and flared rim.",
    techniques=["safe_revolve", "profile_all_x_positive"],
    nominal_dimensions_mm={"diameter": 160.0, "height": 60.0, "wall": 4.0},
    difficulty="easy",
)

code = '''import cadquery as cq

diameter = 160.0
height = 60.0
wall = 4.0
base_thick = 6.0

r_outer = diameter / 2.0
r_inner = r_outer - wall

# Outer profile (X >= 0 always)
outer = (
    cq.Workplane("XZ")
    .moveTo(0, 0)
    .lineTo(r_outer * 0.55, 0)
    .spline([(r_outer, height * 0.3), (r_outer + 4, height)])
    .lineTo(0, height)
    .close()
)
bowl = outer.revolve(360)

# Inner cavity (leave base_thick at bottom)
inner = (
    cq.Workplane("XZ")
    .moveTo(0, base_thick)
    .lineTo(r_inner * 0.5, base_thick)
    .spline([(r_inner - 1, height * 0.4), (r_inner - 2, height)])
    .lineTo(0, height)
    .close()
)
cavity = inner.revolve(360)

result = bowl.cut(cavity)
'''
