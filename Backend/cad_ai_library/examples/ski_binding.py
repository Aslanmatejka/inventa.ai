from ..core.metadata import ExampleMetadata

metadata = ExampleMetadata(
    id="ski_binding",
    name="Ski Binding Toe Piece",
    category="winter",
    keywords=["ski", "binding", "winter", "snow", "toe", "sports"],
    description="Ski binding toe piece: mounting base with curved wings and central boot clamp.",
    techniques=["guarded_fillet"],
    nominal_dimensions_mm={"base_length": 120.0, "base_width": 80.0, "height": 45.0},
    difficulty="medium",
)

code = '''import cadquery as cq

base_l = 120.0
base_w = 80.0
height = 45.0

# Base plate
base = cq.Workplane("XY").box(base_l, base_w, 6, centered=(True, True, False))
try:
    base = base.edges("|Z").fillet(3.0)
except Exception:
    pass

# Central tower
tower = cq.Workplane("XY", origin=(0, 0, 6)).box(40, 30, height - 6, centered=(True, True, False))
try:
    tower = tower.edges("|Z").fillet(3.0)
except Exception:
    pass

# Two wings (left + right clamp jaws)
for sy in (-1, 1):
    wing = (
        cq.Workplane("XY", origin=(0, sy * 15, 6))
        .moveTo(-25, 0)
        .lineTo(25, 0)
        .lineTo(20, sy * 18)
        .lineTo(-20, sy * 18)
        .close()
        .extrude(height - 10)
    )
    base = base.union(wing)

body = base.union(tower)

# Four mounting holes in the base
body = (
    body.faces(">Z[0]").workplane()
    .pushPoints([(-base_l * 0.35, -base_w * 0.35),
                 (base_l * 0.35, -base_w * 0.35),
                 (-base_l * 0.35, base_w * 0.35),
                 (base_l * 0.35, base_w * 0.35)])
    .hole(4.5)
)

result = body
'''
