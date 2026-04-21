from ..core.metadata import ExampleMetadata

metadata = ExampleMetadata(
    id="spirit_level",
    name="Spirit Level",
    category="tool",
    keywords=["level", "spirit level", "bubble", "tool", "carpenter"],
    description="Aluminum spirit level body with two viewing windows and bubble vials.",
    techniques=["boolean_cut"],
    nominal_dimensions_mm={"length": 400.0, "height": 50.0, "depth": 22.0},
    difficulty="easy",
)

code = '''import cadquery as cq

length = 400.0
height = 50.0
depth = 22.0

body = cq.Workplane("XY").box(length, depth, height, centered=(True, True, False))

# Two viewing windows
for x in [-length/4, length/4]:
    win = (cq.Workplane("XZ").workplane(offset=-depth/2 - 1)
           .center(x, height/2).rect(60, 20).extrude(depth + 2))
    body = body.cut(win)

# Center vial window
vial = (cq.Workplane("XZ").workplane(offset=-depth/2 - 1)
        .center(0, height/2).rect(40, 14).extrude(depth + 2))
body = body.cut(vial)

# Grip hole on top
grip = (cq.Workplane("XY").workplane(offset=height)
        .rect(120, depth - 8).extrude(-height * 0.6))
try:
    grip = grip.edges("|Z").fillet(4.0)
except Exception:
    pass
body = body.cut(grip)

result = body
'''
