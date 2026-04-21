from ..core.metadata import ExampleMetadata

metadata = ExampleMetadata(
    id="anchor",
    name="Boat Anchor",
    category="marine",
    keywords=["anchor", "boat", "ship", "marine", "nautical", "mooring"],
    description="Stockless boat anchor with flukes, shank, and ring.",
    techniques=["polyline_profile"],
    nominal_dimensions_mm={"total_length": 500.0, "fluke_spread": 400.0, "shank_thickness": 25.0},
    difficulty="medium",
)

code = '''import cadquery as cq

total_l = 500.0
fluke_spread = 400.0
shank_t = 25.0

# Shank (vertical bar)
shank = (
    cq.Workplane("XY")
    .box(shank_t, shank_t, total_l - 60, centered=(True, True, False))
    .translate((0, 0, 60))
)

# Fluke crown (bottom crossbar)
crown = (
    cq.Workplane("XY")
    .box(fluke_spread, shank_t * 1.4, shank_t * 1.2, centered=(True, True, False))
)

# Two fluke blades (triangular arms)
for sx in (-1, 1):
    fluke = (
        cq.Workplane("XY")
        .moveTo(sx * shank_t / 2.0, -shank_t)
        .lineTo(sx * fluke_spread / 2.0, 0)
        .lineTo(sx * fluke_spread / 2.0, shank_t * 1.2)
        .lineTo(sx * shank_t / 2.0, shank_t * 1.2)
        .close()
        .extrude(shank_t)
        .translate((0, 0, -shank_t / 2.0 + shank_t * 0.1))
    )
    crown = crown.union(fluke)

# Top ring
ring_outer = (
    cq.Workplane("YZ", origin=(0, 0, total_l))
    .circle(shank_t * 0.9)
    .extrude(shank_t * 0.5)
    .translate((-shank_t * 0.25, 0, 0))
)
ring_hole = (
    cq.Workplane("YZ", origin=(0, 0, total_l))
    .circle(shank_t * 0.55)
    .extrude(shank_t * 0.8)
    .translate((-shank_t * 0.4, 0, 0))
)
ring = ring_outer.cut(ring_hole)

body = shank.union(crown).union(ring)
try:
    body = body.edges().fillet(2.0)
except Exception:
    pass

result = body

# --- Modern finishing pass (guarded) ---
try:
    result = result.edges("|Z").fillet(1.2)
except Exception:
    pass
try:
    result = result.faces(">Z").edges().chamfer(0.5)
except Exception:
    pass
try:
    result = result.faces("<Z").edges().fillet(0.8)
except Exception:
    pass
'''
