from ..core.metadata import ExampleMetadata

metadata = ExampleMetadata(
    id="name_plate",
    name="Name Plate",
    category="accessory",
    keywords=["nameplate", "plaque", "sign", "label", "desk", "name"],
    description="Rectangular plaque with raised border and countersunk mount holes.",
    techniques=["guarded_fillet", "cbore_hole"],
    nominal_dimensions_mm={"length": 150.0, "width": 50.0, "thickness": 6.0, "border": 3.0},
    difficulty="easy",
)

code = '''import cadquery as cq

length = 150.0
width = 50.0
thick = 6.0
border = 3.0
recess_depth = 1.5
screw_d = 3.5
screw_head_d = 6.5

body = cq.Workplane("XY").box(length, width, thick, centered=(True, True, False))
try:
    body = body.edges("|Z").fillet(3.0)
except Exception:
    pass

# Inner recess for a label insert
recess = (
    cq.Workplane("XY", origin=(0, 0, thick - recess_depth))
    .rect(length - 2 * border, width - 2 * border)
    .extrude(recess_depth + 0.1)
)
body = body.cut(recess)

# Two countersunk mount holes on the centerline (short-edge ends)
body = (
    body.faces(">Z").workplane()
    .pushPoints([(-length / 2.0 + border * 1.5, 0), (length / 2.0 - border * 1.5, 0)])
    .cboreHole(screw_d, screw_head_d, 2.0)
)

result = body
'''
