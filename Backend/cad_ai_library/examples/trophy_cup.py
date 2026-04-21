from ..core.metadata import ExampleMetadata

metadata = ExampleMetadata(
    id="trophy_cup",
    name="Trophy Cup",
    category="award",
    keywords=["trophy", "cup", "award", "prize", "winner", "sport"],
    description="Classic two-handled trophy cup on a square base.",
    techniques=["safe_revolve"],
    nominal_dimensions_mm={"cup_height": 160.0, "cup_diameter": 110.0, "base_side": 90.0, "total_height": 220.0},
    difficulty="medium",
)

code = '''import cadquery as cq

base_side = 90.0
base_h = 30.0
stem_h = 40.0
cup_h = 160.0
cup_d = 110.0

# Square base (stepped)
base = cq.Workplane("XY").box(base_side, base_side, base_h, centered=(True, True, False))
try:
    base = base.edges("|Z").fillet(4.0)
except Exception:
    pass
base_cap = cq.Workplane("XY", origin=(0, 0, base_h)).box(
    base_side * 0.7, base_side * 0.7, 10, centered=(True, True, False)
)
base = base.union(base_cap)

# Stem (column)
stem = (
    cq.Workplane("XY", origin=(0, 0, base_h + 10))
    .circle(12)
    .extrude(stem_h)
)

# Cup profile (goblet) — simple polyline
z0 = base_h + 10 + stem_h
cup_profile = (
    cq.Workplane("XZ")
    .moveTo(0, z0)
    .lineTo(30, z0)
    .lineTo(cup_d / 2.0, z0 + cup_h * 0.3)
    .lineTo(cup_d / 2.0, z0 + cup_h - 6)
    .lineTo(cup_d / 2.0 + 4, z0 + cup_h - 3)
    .lineTo(cup_d / 2.0 + 4, z0 + cup_h)
    .lineTo(cup_d / 2.0 - 4, z0 + cup_h)
    .lineTo(cup_d / 2.0 - 4, z0 + cup_h * 0.5)
    .lineTo(28, z0 + cup_h * 0.3)
    .lineTo(0, z0 + 4)
    .close()
)
cup = cup_profile.revolve(360)

# Two handles (simple rings on the sides)
for sx in (-1, 1):
    handle_ring = (
        cq.Workplane("XZ", origin=(sx * (cup_d / 2.0 + 2), 0, z0 + cup_h * 0.65))
        .circle(22)
        .extrude(6)
        .translate((0, -3, 0))
    )
    handle_hole = (
        cq.Workplane("XZ", origin=(sx * (cup_d / 2.0 + 2), 0, z0 + cup_h * 0.65))
        .circle(16)
        .extrude(8)
        .translate((0, -4, 0))
    )
    cup = cup.union(handle_ring).cut(handle_hole)

body = base.union(stem).union(cup)

result = body
'''
