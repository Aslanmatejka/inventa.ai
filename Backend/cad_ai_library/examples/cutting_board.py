from ..core.metadata import ExampleMetadata

metadata = ExampleMetadata(
    id="cutting_board",
    name="Cutting Board",
    category="accessory",
    keywords=["cutting", "board", "chopping", "kitchen", "wood"],
    description="Rectangular cutting board with juice groove and hang hole.",
    techniques=["guarded_fillet"],
    nominal_dimensions_mm={"length": 300.0, "width": 200.0, "thickness": 18.0},
    difficulty="easy",
)

code = '''import cadquery as cq

length = 300.0
width = 200.0
thick = 18.0
groove_inset = 15.0
groove_depth = 2.0
groove_w = 4.0

body = cq.Workplane("XY").box(length, width, thick, centered=(True, True, False))
try:
    body = body.edges("|Z").fillet(12.0)
except Exception:
    pass
try:
    body = body.edges(">Z or <Z").fillet(1.5)
except Exception:
    pass

# Juice groove on top
outer = (
    cq.Workplane("XY", origin=(0, 0, thick - groove_depth))
    .rect(length - 2 * groove_inset, width - 2 * groove_inset)
    .extrude(groove_depth + 0.1)
)
inner = (
    cq.Workplane("XY", origin=(0, 0, thick - groove_depth))
    .rect(length - 2 * groove_inset - 2 * groove_w, width - 2 * groove_inset - 2 * groove_w)
    .extrude(groove_depth + 0.2)
)
groove = outer.cut(inner)
body = body.cut(groove)

# Hang hole in one corner
body = (
    body.faces(">Z").workplane()
    .center(length / 2.0 - 20.0, width / 2.0 - 20.0)
    .hole(14.0)
)

result = body
'''
