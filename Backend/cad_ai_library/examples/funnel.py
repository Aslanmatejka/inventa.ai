from ..core.metadata import ExampleMetadata

metadata = ExampleMetadata(
    id="funnel",
    name="Kitchen Funnel",
    category="container",
    keywords=["funnel", "pour", "liquid", "kitchen", "oil", "spout"],
    description="Conical funnel with cylindrical spout and inner cavity.",
    techniques=["loft_frustum", "shell_cavity"],
    nominal_dimensions_mm={"top_diameter": 100.0, "spout_diameter": 12.0, "cone_height": 80.0, "spout_length": 40.0, "wall": 2.0},
    difficulty="medium",
)

code = '''import cadquery as cq

r_top = 50.0
r_spout_out = 8.0
r_spout_in = 6.0
cone_h = 80.0
spout_l = 40.0
wall = 2.0

# Outer: cone + spout (stacked solids)
cone_outer = (
    cq.Workplane("XY")
    .circle(r_spout_out)
    .workplane(offset=cone_h)
    .circle(r_top)
    .loft(combine=True)
)
spout_outer = cq.Workplane("XY", origin=(0, 0, -spout_l)).circle(r_spout_out).extrude(spout_l + 0.1)
outer = cone_outer.union(spout_outer)

# Inner cavity (same shape, shrunk by wall)
cone_inner = (
    cq.Workplane("XY", origin=(0, 0, wall * 0.5))
    .circle(max(r_spout_in, 1.0))
    .workplane(offset=cone_h)
    .circle(r_top - wall)
    .loft(combine=True)
)
spout_inner = cq.Workplane("XY", origin=(0, 0, -spout_l - 1)).circle(r_spout_in).extrude(spout_l + 2)
inner = cone_inner.union(spout_inner)

body = outer.cut(inner)

# Ground the model (translate so lowest point is at Z=0)
body = body.translate((0, 0, spout_l))

result = body
'''
