from ..core.metadata import ExampleMetadata

metadata = ExampleMetadata(
    id="measuring_cup",
    name="Measuring Cup",
    category="container",
    keywords=["measuring", "cup", "kitchen", "pour", "baking", "volume"],
    description="Measuring cup with pour spout and integrated handle.",
    techniques=["safe_revolve", "shell_cavity"],
    nominal_dimensions_mm={"diameter": 85.0, "height": 95.0, "wall": 2.5, "volume_ml": 250},
    difficulty="medium",
)

code = '''import cadquery as cq

r_out = 42.5
height = 95.0
wall = 2.5
base_thick = 4.0

body = cq.Workplane("XY").circle(r_out).extrude(height)
body = body.faces(">Z").shell(-wall)

# Pour spout: add a small wedge on one side near the top
spout = (
    cq.Workplane("XZ", origin=(0, r_out - 2, height - 10))
    .moveTo(-8, 0)
    .lineTo(8, 0)
    .lineTo(0, 10)
    .close()
    .extrude(12)
    .translate((0, -4, 0))
)
body = body.union(spout)

# Handle: an oval loop on the side
handle_outer = (
    cq.Workplane("YZ", origin=(r_out + 5, 0, height * 0.4))
    .ellipse(35, 18)
    .extrude(8)
    .translate((0, 0, 0))
)
handle_inner = (
    cq.Workplane("YZ", origin=(r_out + 5, 0, height * 0.4))
    .ellipse(28, 11)
    .extrude(8.2)
)
handle = handle_outer.cut(handle_inner)
body = body.union(handle)

try:
    body = body.edges(">Z").fillet(0.6)
except Exception:
    pass

result = body
'''
