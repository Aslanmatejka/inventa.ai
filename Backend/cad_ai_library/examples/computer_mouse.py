from ..core.metadata import ExampleMetadata

metadata = ExampleMetadata(
    id="computer_mouse",
    name="Computer Mouse",
    category="computing",
    keywords=["mouse", "computer", "pc", "peripheral", "ergonomic", "wireless"],
    description="Ergonomic computer mouse with curved top, scroll wheel slot, and two top buttons.",
    techniques=["loft_shape", "guarded_fillet"],
    nominal_dimensions_mm={"length": 115.0, "width": 65.0, "height": 40.0},
    difficulty="medium",
)

code = '''import cadquery as cq

length = 115.0
width = 65.0
height = 40.0

# Footprint ellipse at Z=0, taller oval at mid-height, smaller near top
body = (
    cq.Workplane("XY")
    .ellipse(length / 2.0, width / 2.0)
    .workplane(offset=height * 0.55)
    .ellipse(length / 2.0 * 0.95, width / 2.0 * 0.95)
    .workplane(offset=height * 0.45)
    .ellipse(length / 2.0 * 0.55, width / 2.0 * 0.65)
    .loft(combine=True)
)
try:
    body = body.edges().fillet(3.0)
except Exception:
    pass

# Scroll wheel slot on top front
wheel_slot = (
    cq.Workplane("XZ", origin=(length * 0.18, 0, height - 2))
    .circle(6)
    .extrude(12)
    .translate((0, -6, 0))
)
body = body.cut(wheel_slot)

# Button separation line (thin slot across the top front half)
btn_slot = (
    cq.Workplane("XZ", origin=(length * 0.05, 0, height - 3))
    .rect(0.6, 10)
    .extrude(length * 0.45)
    .translate((0, 0, 0))
)
body = body.cut(btn_slot)

result = body
'''
