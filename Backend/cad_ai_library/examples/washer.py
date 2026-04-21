from ..core.metadata import ExampleMetadata

metadata = ExampleMetadata(
    id="washer",
    name="Flat Washer",
    category="mechanical",
    keywords=["washer", "fastener", "ring", "spacer", "hardware"],
    description="Simple flat washer — outer disc with concentric through-hole.",
    techniques=["guarded_fillet"],
    nominal_dimensions_mm={"outer_diameter": 20.0, "inner_diameter": 8.4, "thickness": 1.6},
    difficulty="easy",
)

code = '''import cadquery as cq

outer_d = 20.0
inner_d = 8.4
thick = 1.6

body = (
    cq.Workplane("XY")
    .circle(outer_d / 2.0)
    .circle(inner_d / 2.0)
    .extrude(thick)
)

try:
    body = body.edges().fillet(min(0.3, thick * 0.2))
except Exception:
    pass

result = body
'''
