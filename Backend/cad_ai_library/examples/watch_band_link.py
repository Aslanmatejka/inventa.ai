from ..core.metadata import ExampleMetadata

metadata = ExampleMetadata(
    id="watch_band_link",
    name="Watch Band Link",
    category="wearable",
    keywords=["watch", "band", "link", "strap", "bracelet", "wearable"],
    description="Single watch-band link with two barrel ends and pin holes.",
    techniques=["guarded_fillet"],
    nominal_dimensions_mm={"width": 18.0, "length": 10.0, "thickness": 3.5},
    difficulty="medium",
)

code = '''import cadquery as cq

width = 18.0      # along Y (strap width)
length = 10.0     # along X (between pins)
thick = 3.5
barrel_d = 3.0
pin_d = 1.2

# Flat slab
body = cq.Workplane("XY").box(length, width, thick, centered=(True, True, False))
try:
    body = body.edges("|Z or |Y").fillet(0.6)
except Exception:
    pass

# Two barrels on +Y and -Y ends along the short edges
for xc in (-length / 2.0, length / 2.0):
    barrel = (
        cq.Workplane("YZ", origin=(xc, -width / 2.0, thick / 2.0))
        .circle(barrel_d / 2.0)
        .extrude(width)
    )
    body = body.union(barrel)
    pin = (
        cq.Workplane("YZ", origin=(xc, -width / 2.0 - 0.1, thick / 2.0))
        .circle(pin_d / 2.0)
        .extrude(width + 0.2)
    )
    body = body.cut(pin)

result = body
'''
