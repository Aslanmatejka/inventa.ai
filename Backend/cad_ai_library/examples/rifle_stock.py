from ..core.metadata import ExampleMetadata

metadata = ExampleMetadata(
    id="rifle_stock",
    name="Rifle Stock",
    category="firearm",
    keywords=["rifle", "stock", "gun", "firearm", "wooden stock", "buttstock", "weapon"],
    description="Wooden rifle buttstock with cheek riser, pistol grip, and recoil pad (display/prop).",
    techniques=["boolean_union", "guarded_fillet"],
    nominal_dimensions_mm={"length": 380.0, "height": 130.0, "thickness": 40.0},
    difficulty="medium",
)

code = '''import cadquery as cq

# Main stock profile (side view in XZ)
stock_pts = [
    (0, 0),        # toe (bottom front)
    (350, 10),     # buttpad bottom
    (380, 40),     # buttpad back
    (380, 100),    # heel
    (340, 120),    # comb back
    (180, 105),    # comb front
    (100, 70),     # wrist top
    (40, 55),      # grip top
    (0, 30),       # grip bottom
]
stock = (cq.Workplane("XZ").polyline(stock_pts).close()
         .extrude(40, both=False))
stock = stock.translate((0, -20, 0))

# Pistol grip extension below wrist
grip = (cq.Workplane("XZ").polyline([
    (40, 55), (20, 55), (10, 0), (60, 0)
]).close().extrude(40, both=False))
grip = grip.translate((0, -20, 0))

body = stock.union(grip)

# Cheek riser (raised pad on side)
riser = (cq.Workplane("XY").workplane(offset=90)
         .center(260, 20).rect(140, 15).extrude(10))
try:
    riser = riser.edges("|Z").fillet(8.0)
except Exception:
    pass
body = body.union(riser)

# Recoil pad (back)
pad = (cq.Workplane("YZ").workplane(offset=380)
       .center(0, 55).rect(40, 95).extrude(10))
try:
    pad = pad.edges("|X").fillet(8.0)
except Exception:
    pass
body = body.union(pad)

try:
    body = body.edges("|Y").fillet(3.0)
except Exception:
    pass

result = body
'''
