from ..core.metadata import ExampleMetadata

metadata = ExampleMetadata(
    id="iv_drip_bag",
    name="IV Drip Bag",
    category="medical",
    keywords=["iv", "drip", "bag", "saline", "medical", "hospital", "infusion"],
    description="Stylized IV drip bag: flat pillow-shaped body with hanging hole and tubing port.",
    techniques=["polyline_profile"],
    nominal_dimensions_mm={"length": 220.0, "width": 140.0, "thickness": 25.0},
    difficulty="medium",
)

code = '''import cadquery as cq

length = 220.0
width = 140.0
thick = 25.0

# Rounded pouch outline
body = (
    cq.Workplane("XY")
    .moveTo(-width / 2.0 + 15, 0)
    .threePointArc((-width / 2.0, length * 0.15), (-width / 2.0 + 20, length * 0.3))
    .lineTo(-width / 2.0 + 20, length - 15)
    .threePointArc((0, length), (width / 2.0 - 20, length - 15))
    .lineTo(width / 2.0 - 20, length * 0.3)
    .threePointArc((width / 2.0, length * 0.15), (width / 2.0 - 15, 0))
    .close()
    .extrude(thick)
)
try:
    body = body.edges(">Z or <Z").fillet(3.0)
except Exception:
    pass

# Hanging hole at the top
hang = (
    cq.Workplane("XY", origin=(0, length - 8, -0.1))
    .rect(20, 6)
    .extrude(thick + 0.2)
)
body = body.cut(hang)

# Tubing port at the bottom
port = (
    cq.Workplane("XY", origin=(0, -10, thick / 2.0))
    .circle(4.0)
    .extrude(30)
    .rotate((0, -10, thick / 2.0), (1, -10, thick / 2.0), -90)
)
body = body.union(port)

result = body
'''
