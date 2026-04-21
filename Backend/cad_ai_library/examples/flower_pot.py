from ..core.metadata import ExampleMetadata

metadata = ExampleMetadata(
    id="flower_pot",
    name="Flower Pot",
    category="container",
    keywords=["pot", "planter", "flower", "plant", "garden", "succulent"],
    description="Tapered planter with drainage hole and outer lip.",
    techniques=["loft_frustum", "safe_revolve", "shell_cavity"],
    nominal_dimensions_mm={"top_diameter": 120.0, "bottom_diameter": 90.0, "height": 110.0, "wall": 4.0},
    difficulty="medium",
)

code = '''import cadquery as cq

r_top = 60.0
r_bot = 45.0
height = 110.0
wall = 4.0
base_thick = 6.0
drain_d = 10.0

# Outer tapered body via loft
outer = (
    cq.Workplane("XY")
    .circle(r_bot)
    .workplane(offset=height)
    .circle(r_top)
    .loft(combine=True)
)

# Inner cavity (slightly smaller, keeps base thickness)
inner = (
    cq.Workplane("XY", origin=(0, 0, base_thick))
    .circle(r_bot - wall)
    .workplane(offset=height - base_thick)
    .circle(r_top - wall)
    .loft(combine=True)
)

body = outer.cut(inner)

# Drainage hole
drain = cq.Workplane("XY").circle(drain_d / 2.0).extrude(base_thick + 1)
body = body.cut(drain)

# Rim lip on top
try:
    body = body.edges(">Z").fillet(1.5)
except Exception:
    pass

result = body
'''
