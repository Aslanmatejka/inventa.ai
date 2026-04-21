from ..core.metadata import ExampleMetadata

metadata = ExampleMetadata(
    id="duct_reducer",
    name="Duct Reducer",
    category="hvac",
    keywords=["duct", "reducer", "hvac", "air", "transition", "cone"],
    description="Round-to-round duct reducer with flared ends for slip fit.",
    techniques=["loft_frustum", "shell_cavity"],
    nominal_dimensions_mm={"large_diameter": 160.0, "small_diameter": 100.0, "length": 140.0, "wall": 2.0},
    difficulty="medium",
)

code = '''import cadquery as cq

D1 = 160.0
D2 = 100.0
length = 140.0
wall = 2.0
flare_l = 12.0

# Outer shell via lofting three circles
outer = (
    cq.Workplane("XY")
    .circle(D1 / 2.0)
    .workplane(offset=flare_l)
    .circle(D1 / 2.0)
    .workplane(offset=length - 2 * flare_l)
    .circle(D2 / 2.0)
    .workplane(offset=flare_l)
    .circle(D2 / 2.0)
    .loft(combine=True)
)
inner = (
    cq.Workplane("XY", origin=(0, 0, -0.1))
    .circle(D1 / 2.0 - wall)
    .workplane(offset=flare_l)
    .circle(D1 / 2.0 - wall)
    .workplane(offset=length - 2 * flare_l)
    .circle(D2 / 2.0 - wall)
    .workplane(offset=flare_l + 0.2)
    .circle(D2 / 2.0 - wall)
    .loft(combine=True)
)
result = outer.cut(inner)
'''
