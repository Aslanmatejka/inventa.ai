from ..core.metadata import ExampleMetadata

metadata = ExampleMetadata(
    id="hinge",
    name="Barrel Hinge Leaf",
    category="mechanical",
    keywords=["hinge", "pivot", "door", "lid", "leaf", "barrel"],
    description="Single hinge leaf with two barrels and two mounting holes.",
    techniques=["cbore_hole", "guarded_fillet"],
    nominal_dimensions_mm={"length": 60.0, "width": 25.0, "thickness": 3.0, "pin_diameter": 4.0},
    difficulty="medium",
)

code = '''import cadquery as cq

length = 60.0
width = 25.0
thick = 3.0
pin_d = 4.0
barrel_od = pin_d + 4.0
barrel_len = 18.0
hole_d = 3.5

# Flat leaf
leaf = cq.Workplane("XY").box(length, width, thick, centered=(True, True, False))

# Two barrels along the front edge (Y = +width/2)
barrel1 = (
    cq.Workplane("YZ", origin=(-barrel_len / 2.0, width / 2.0, barrel_od / 2.0))
    .circle(barrel_od / 2.0)
    .extrude(barrel_len)
)
barrel2 = barrel1.translate((length / 2.0 - barrel_len / 2.0 - (-length / 2.0 + barrel_len / 2.0), 0, 0))
body = leaf.union(barrel1).union(barrel2)

# Pin hole through barrels
pin_cut = (
    cq.Workplane("YZ", origin=(-length / 2.0 - 1, width / 2.0, barrel_od / 2.0))
    .circle(pin_d / 2.0)
    .extrude(length + 2)
)
body = body.cut(pin_cut)

# Mounting holes
body = (
    body.faces(">Z")
    .workplane()
    .pushPoints([(-length / 4.0, -width / 4.0), (length / 4.0, -width / 4.0)])
    .hole(hole_d)
)

try:
    body = body.edges("|Z").fillet(1.5)
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
