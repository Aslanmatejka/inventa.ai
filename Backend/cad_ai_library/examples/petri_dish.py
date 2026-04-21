from ..core.metadata import ExampleMetadata

metadata = ExampleMetadata(
    id="petri_dish",
    name="Petri Dish",
    category="lab",
    keywords=["petri", "dish", "lab", "culture", "biology", "plate"],
    description="Shallow cylindrical petri dish with raised rim.",
    techniques=["safe_revolve", "shell_cavity"],
    nominal_dimensions_mm={"diameter": 90.0, "height": 15.0, "wall": 1.5},
    difficulty="easy",
)

code = '''import cadquery as cq

diameter = 90.0
height = 15.0
wall = 1.5

r = diameter / 2.0

profile = (
    cq.Workplane("XZ")
    .moveTo(0, 0)
    .lineTo(r, 0)
    .lineTo(r, height)
    .lineTo(r - wall, height)
    .lineTo(r - wall, wall)
    .lineTo(0, wall)
    .close()
)
body = profile.revolve(360)

result = body
'''
