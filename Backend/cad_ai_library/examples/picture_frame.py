from ..core.metadata import ExampleMetadata

metadata = ExampleMetadata(
    id="picture_frame",
    name="Picture Frame",
    category="decorative",
    keywords=["picture", "frame", "photo", "wall", "art"],
    description="Rectangular picture frame with stepped inner rabbet.",
    techniques=["guarded_fillet"],
    nominal_dimensions_mm={"outer_length": 200.0, "outer_width": 150.0, "border": 25.0, "thickness": 15.0},
    difficulty="easy",
)

code = '''import cadquery as cq

outer_l = 200.0
outer_w = 150.0
border = 25.0
thick = 15.0
rabbet_depth = 5.0
rabbet_lip = 4.0

body = cq.Workplane("XY").box(outer_l, outer_w, thick, centered=(True, True, False))

# Opening (full cut through)
opening = (
    cq.Workplane("XY", origin=(0, 0, -0.1))
    .rect(outer_l - 2 * border, outer_w - 2 * border)
    .extrude(thick + 0.2)
)
body = body.cut(opening)

# Rabbet on the back for the picture
rabbet = (
    cq.Workplane("XY", origin=(0, 0, -0.1))
    .rect(outer_l - 2 * (border - rabbet_lip), outer_w - 2 * (border - rabbet_lip))
    .extrude(rabbet_depth + 0.1)
)
body = body.cut(rabbet)

try:
    body = body.edges("|Z").fillet(2.0)
except Exception:
    pass

result = body
'''
