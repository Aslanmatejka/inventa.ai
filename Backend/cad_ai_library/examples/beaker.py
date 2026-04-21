from ..core.metadata import ExampleMetadata

metadata = ExampleMetadata(
    id="beaker",
    name="Lab Beaker",
    category="lab",
    keywords=["beaker", "lab", "science", "chemistry", "glass", "graduated"],
    description="Graduated lab beaker with pour spout and flat bottom.",
    techniques=["safe_revolve", "shell_cavity"],
    nominal_dimensions_mm={"diameter": 80.0, "height": 110.0, "wall": 1.5, "volume_ml": 400},
    difficulty="medium",
)

code = '''import cadquery as cq

diameter = 80.0
height = 110.0
wall = 1.5

r = diameter / 2.0

# Cylindrical body with a raised lip
profile = (
    cq.Workplane("XZ")
    .moveTo(0, 0)
    .lineTo(r, 0)
    .lineTo(r, height - 6)
    .lineTo(r + 2, height - 3)
    .lineTo(r + 2, height)
    .lineTo(r - 2, height)
    .lineTo(r - wall, height - wall)
    .lineTo(r - wall, wall)
    .lineTo(0, wall)
    .close()
)
body = profile.revolve(360)

# Pour spout on one side
spout = (
    cq.Workplane("XZ", origin=(r - 2, 0, height - 6))
    .moveTo(-2, 0)
    .lineTo(10, 0)
    .lineTo(10, 6)
    .lineTo(-2, 8)
    .close()
    .extrude(6)
    .translate((0, -3, 0))
)
body = body.union(spout)

result = body
'''
