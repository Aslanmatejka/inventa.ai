from ..core.metadata import ExampleMetadata

metadata = ExampleMetadata(
    id="glasses_case",
    name="Eyeglasses Case",
    category="container",
    keywords=["glasses", "eyeglass", "case", "spectacles", "eyewear"],
    description="Oval eyeglasses case body sized for standard frames.",
    techniques=["shell_cavity", "guarded_fillet"],
    nominal_dimensions_mm={"length": 160.0, "width": 65.0, "height": 40.0, "wall": 3.0},
    difficulty="easy",
)

code = '''import cadquery as cq

length = 160.0
width = 65.0
height = 40.0
wall = 3.0

# Start with an ellipse extrusion
body = (
    cq.Workplane("XY")
    .ellipse(length / 2.0, width / 2.0)
    .extrude(height)
)
try:
    body = body.edges(">Z or <Z").fillet(min(5.0, height * 0.2))
except Exception:
    pass

body = body.faces(">Z").shell(-wall)

result = body
'''
