from ..core.metadata import ExampleMetadata

metadata = ExampleMetadata(
    id="game_card_tray",
    name="Card Deck Tray",
    category="gaming",
    keywords=["card", "deck", "tray", "holder", "gaming", "tabletop", "organizer"],
    description="Board-game card tray with slanted back stop, designed to hold a standard deck.",
    techniques=["guarded_fillet"],
    nominal_dimensions_mm={"length": 100.0, "width": 70.0, "height": 35.0},
    difficulty="easy",
)

code = '''import cadquery as cq

length = 100.0
width = 70.0
height = 35.0
wall = 3.0

base = cq.Workplane("XY").box(length, width, wall, centered=(True, True, False))

# Left + right side walls
left = (
    cq.Workplane("XY", origin=(-length / 2.0 + wall / 2.0, 0, 0))
    .box(wall, width, height, centered=(True, True, False))
)
right = (
    cq.Workplane("XY", origin=(length / 2.0 - wall / 2.0, 0, 0))
    .box(wall, width, height, centered=(True, True, False))
)
# Back wall
back = (
    cq.Workplane("XY", origin=(0, -width / 2.0 + wall / 2.0, 0))
    .box(length, wall, height, centered=(True, True, False))
)
# Front low lip
front = (
    cq.Workplane("XY", origin=(0, width / 2.0 - wall / 2.0, 0))
    .box(length, wall, height * 0.35, centered=(True, True, False))
)

body = base.union(left).union(right).union(back).union(front)
try:
    body = body.edges("|Z").fillet(2.0)
except Exception:
    pass

# Finger notch in the front wall
notch = (
    cq.Workplane("XZ", origin=(0, width / 2.0 - wall - 0.1, height * 0.15))
    .circle(8.0)
    .extrude(wall + 0.2)
)
body = body.cut(notch)

result = body
'''
