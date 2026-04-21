from ..core.metadata import ExampleMetadata

metadata = ExampleMetadata(
    id="skateboard_deck",
    name="Skateboard Deck",
    category="sports",
    keywords=["skateboard", "deck", "board", "skate", "sports"],
    description="Popsicle-shape skateboard deck with truck mount holes.",
    techniques=["polyline_profile", "guarded_fillet"],
    nominal_dimensions_mm={"length": 800.0, "width": 200.0, "thickness": 12.0},
    difficulty="medium",
)

code = '''import cadquery as cq

length = 800.0
width = 200.0
thick = 12.0
nose_tail_r = width / 2.0 - 5

# Outline: rounded rectangle via two semicircles + straight sides
deck = (
    cq.Workplane("XY")
    .moveTo(-length / 2.0 + nose_tail_r, width / 2.0)
    .lineTo(length / 2.0 - nose_tail_r, width / 2.0)
    .threePointArc((length / 2.0, 0), (length / 2.0 - nose_tail_r, -width / 2.0))
    .lineTo(-length / 2.0 + nose_tail_r, -width / 2.0)
    .threePointArc((-length / 2.0, 0), (-length / 2.0 + nose_tail_r, width / 2.0))
    .close()
    .extrude(thick)
)
try:
    deck = deck.edges(">Z or <Z").fillet(1.5)
except Exception:
    pass

# Truck mounting holes: 4 at each end (two pairs)
hole_d = 6.0
mount_pts = []
for xc in (-length * 0.35, length * 0.35):
    for dx in (-16, 16):
        for dy in (-20, 20):
            mount_pts.append((xc + dx, dy))

cutter = (
    cq.Workplane("XY", origin=(0, 0, -1))
    .pushPoints(mount_pts)
    .circle(hole_d / 2.0)
    .extrude(thick + 2)
)
deck = deck.cut(cutter)

result = deck
'''
