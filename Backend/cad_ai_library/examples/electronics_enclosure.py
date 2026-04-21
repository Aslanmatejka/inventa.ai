from ..core.metadata import ExampleMetadata

metadata = ExampleMetadata(
    id="electronics_enclosure",
    name="Electronics Enclosure",
    category="enclosure",
    keywords=["enclosure", "case", "box", "electronics", "pcb", "housing", "lid"],
    description="Rounded-rect extruded enclosure with soft-edge body, internal mounting bosses and a matching curved lid.",
    techniques=["rounded_rect_extrude", "shell", "mounting_bosses", "guarded_fillet", "chamfer"],
    nominal_dimensions_mm={"length": 120.0, "width": 80.0, "height": 40.0, "wall": 2.5},
    difficulty="intermediate",
)

code = '''\
import cadquery as cq

length, width, height = 120.0, 80.0, 40.0
wall = 2.5
corner_r = 8.0        # rounded vertical corners
boss_diameter = 6.0
boss_height = 8.0
boss_hole_diameter = 2.5
lid_height = 5.0
lid_lip = 1.5

# Body: rounded-rect profile extruded (no raw box).
body_profile = (
    cq.Workplane("XY")
    .rect(length, width)
    .extrude(height)
)
try:
    body_profile = body_profile.edges("|Z").fillet(corner_r)
except Exception:
    pass
# Hollow it out from the top, leaving bottom wall intact.
body = body_profile.faces(">Z").shell(-wall)

# Corner mounting bosses (inside the shell)
inset = wall + boss_diameter / 2.0 + 2.0
for sx, sy in [(-1, -1), (1, -1), (-1, 1), (1, 1)]:
    x = sx * (length / 2.0 - inset)
    y = sy * (width / 2.0 - inset)
    boss = (
        cq.Workplane("XY", origin=(x, y, wall))
        .circle(boss_diameter / 2.0)
        .extrude(boss_height)
    )
    hole = (
        cq.Workplane("XY", origin=(x, y, wall))
        .circle(boss_hole_diameter / 2.0)
        .extrude(boss_height + 1.0)
    )
    body = body.union(boss).cut(hole)

# Soft-edge top and bottom rims
try:
    body = body.faces(">Z").edges().chamfer(0.6)
except Exception:
    pass
try:
    body = body.faces("<Z").edges().fillet(1.2)
except Exception:
    pass

# Lid — rounded-rect that mirrors the body corners
lid = (
    cq.Workplane("XY", origin=(0, 0, height + 1.0))
    .rect(length, width)
    .extrude(lid_height)
)
try:
    lid = lid.edges("|Z").fillet(corner_r)
except Exception:
    pass
try:
    lid = lid.faces(">Z").edges().fillet(1.5)
except Exception:
    pass

# Lip that drops into the body cavity
lip = (
    cq.Workplane("XY", origin=(0, 0, height - lid_lip + 1.0))
    .rect(length - 2 * wall - 0.4, width - 2 * wall - 0.4)
    .extrude(lid_lip)
)
try:
    lip = lip.edges("|Z").fillet(max(corner_r - wall - 0.2, 1.0))
except Exception:
    pass
lid = lid.union(lip)

result = body.union(lid)
'''
