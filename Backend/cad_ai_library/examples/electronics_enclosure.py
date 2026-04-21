from ..core.metadata import ExampleMetadata

metadata = ExampleMetadata(
    id="electronics_enclosure",
    name="Electronics Enclosure",
    category="enclosure",
    keywords=["enclosure", "case", "box", "electronics", "pcb", "housing", "lid"],
    description="Two-part enclosure: hollow shell with mounting bosses and a snap-fit lid.",
    techniques=["box+shell", "mounting bosses", "lid as separate piece", "guarded fillets"],
    nominal_dimensions_mm={"length": 120.0, "width": 80.0, "height": 40.0, "wall": 2.5},
    difficulty="intermediate",
)

code = '''\
import cadquery as cq

length, width, height = 120.0, 80.0, 40.0
wall = 2.5
boss_diameter = 6.0
boss_height = 8.0
boss_hole_diameter = 2.5
lid_height = 5.0
lid_lip = 1.5

# Body grounded at Z=0 (box is the only primitive that accepts `centered=`)
body = cq.Workplane("XY").box(length, width, height, centered=(True, True, False))
body = body.faces(">Z").shell(-wall)

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
    # Screw hole
    hole = (
        cq.Workplane("XY", origin=(x, y, wall))
        .circle(boss_hole_diameter / 2.0)
        .extrude(boss_height + 1.0)
    )
    body = body.union(boss).cut(hole)

# Soften outer top edges
try:
    body = body.edges(">Z").fillet(1.0)
except Exception:
    pass

# Lid — sits on top at Z = height
lid = (
    cq.Workplane("XY", origin=(0, 0, height + 1.0))
    .box(length, width, lid_height, centered=(True, True, False))
)
# Lid lip (inner tab that drops into the body opening)
lip = (
    cq.Workplane("XY", origin=(0, 0, height - lid_lip + 1.0))
    .box(length - 2 * wall - 0.4, width - 2 * wall - 0.4, lid_lip, centered=(True, True, False))
)
lid = lid.union(lip)

result = body.union(lid)
'''
