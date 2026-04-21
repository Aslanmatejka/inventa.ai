from ..core.metadata import ExampleMetadata

metadata = ExampleMetadata(
    id="column_greek",
    name="Greek Column",
    category="architecture",
    keywords=["column", "pillar", "architecture", "greek", "doric", "fluted"],
    description="Fluted Doric-style column with base and capital.",
    techniques=["polar_array", "safe_revolve"],
    nominal_dimensions_mm={"height": 200.0, "shaft_diameter": 40.0, "flute_count": 16},
    difficulty="advanced",
)

code = '''import cadquery as cq

height = 200.0
shaft_d = 40.0
flute_count = 16
base_d = shaft_d * 1.35
base_h = 12.0
cap_d = shaft_d * 1.30
cap_h = 10.0
abacus_h = 6.0

shaft_h = height - base_h - cap_h - abacus_h

# Base
base = cq.Workplane("XY").circle(base_d / 2.0).extrude(base_h)
try:
    base = base.edges(">Z or <Z").fillet(2.0)
except Exception:
    pass

# Shaft
shaft = (
    cq.Workplane("XY", origin=(0, 0, base_h))
    .circle(shaft_d / 2.0)
    .extrude(shaft_h)
)

# Flutes (narrow vertical cutters around the shaft)
flute_r = 1.6
for i in range(flute_count):
    theta = 360.0 / flute_count * i
    cutter = (
        cq.Workplane("XY", origin=(shaft_d / 2.0 - 0.3, 0, base_h + 2))
        .circle(flute_r)
        .extrude(shaft_h - 4)
        .rotate((0, 0, 0), (0, 0, 1), theta)
    )
    shaft = shaft.cut(cutter)

# Capital (echinus flared top)
cap = (
    cq.Workplane("XY", origin=(0, 0, base_h + shaft_h))
    .circle(shaft_d / 2.0)
    .workplane(offset=cap_h)
    .circle(cap_d / 2.0)
    .loft(combine=True)
)

# Abacus (square slab on top)
abacus = (
    cq.Workplane("XY", origin=(0, 0, base_h + shaft_h + cap_h))
    .box(cap_d, cap_d, abacus_h, centered=(True, True, False))
)

body = base.union(shaft).union(cap).union(abacus)

result = body
'''
