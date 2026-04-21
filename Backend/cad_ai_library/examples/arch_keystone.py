from ..core.metadata import ExampleMetadata

metadata = ExampleMetadata(
    id="arch_keystone",
    name="Arch Keystone",
    category="architecture",
    keywords=["keystone", "arch", "stone", "architecture", "wedge", "voussoir"],
    description="Trapezoidal keystone block with decorative chamfered face.",
    techniques=["polyline_profile", "guarded_fillet"],
    nominal_dimensions_mm={"bottom_width": 60.0, "top_width": 90.0, "height": 100.0, "depth": 40.0},
    difficulty="easy",
)

code = '''import cadquery as cq

bot_w = 60.0
top_w = 90.0
height = 100.0
depth = 40.0

# Trapezoidal profile in XZ (wider at top)
profile = (
    cq.Workplane("XZ")
    .moveTo(-bot_w / 2.0, 0)
    .lineTo(bot_w / 2.0, 0)
    .lineTo(top_w / 2.0, height)
    .lineTo(-top_w / 2.0, height)
    .close()
)
body = profile.extrude(depth).translate((0, -depth / 2.0, 0))

try:
    body = body.edges("|Y").chamfer(3.0)
except Exception:
    pass

# Decorative recess on the front face
recess = (
    cq.Workplane("XZ", origin=(0, depth / 2.0 - 3.0, height / 2.0))
    .rect(top_w * 0.5, height * 0.5)
    .extrude(-3.1)
)
body = body.cut(recess)

result = body
'''
