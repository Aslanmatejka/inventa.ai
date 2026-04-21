from ..core.metadata import ExampleMetadata

metadata = ExampleMetadata(
    id="trash_can",
    name="Kitchen Trash Can",
    category="container",
    keywords=["trash", "can", "bin", "garbage", "waste", "rubbish", "kitchen"],
    description="Tall round kitchen trash can with tapered body and top rim.",
    techniques=["safe_revolve", "shell_cavity"],
    nominal_dimensions_mm={"top_diameter": 280.0, "bottom_diameter": 240.0, "height": 500.0, "wall": 2.5},
    difficulty="easy",
)

code = '''import cadquery as cq

top_d = 280.0
bot_d = 240.0
height = 500.0
wall = 2.5
rim_h = 6.0

r_top = top_d / 2.0
r_bot = bot_d / 2.0

# Revolve profile
profile = (
    cq.Workplane("XZ")
    .moveTo(0, 0)
    .lineTo(r_bot, 0)
    .lineTo(r_top, height - rim_h)
    .lineTo(r_top + 4, height - rim_h)
    .lineTo(r_top + 4, height)
    .lineTo(r_top - 2, height)
    .lineTo(r_top - 2 - wall, height - wall)
    .lineTo(r_bot - wall, wall)
    .lineTo(0, wall)
    .close()
)
body = profile.revolve(360)

# Foot recess (small lip on the bottom)
foot = (
    cq.Workplane("XY", origin=(0, 0, -0.1))
    .circle(r_bot - 10)
    .extrude(wall + 0.2)
)
body = body.cut(foot.intersect(cq.Workplane("XY").circle(r_bot - 20).extrude(wall + 0.2)))

result = body
'''
