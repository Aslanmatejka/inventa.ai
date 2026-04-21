from ..core.metadata import ExampleMetadata

metadata = ExampleMetadata(
    id="abstract_sculpture",
    name="Abstract Sculpture",
    category="sculpture",
    keywords=["sculpture", "abstract", "art", "statue", "modern art", "decor"],
    description="Abstract sculpture: stacked twisted rectangular prisms on a square base.",
    techniques=["boolean_union", "rotation_pattern"],
    nominal_dimensions_mm={"base_width": 120.0, "height": 320.0},
    difficulty="easy",
)

code = '''import cadquery as cq

# Base
base = cq.Workplane("XY").box(120, 120, 20, centered=(True, True, False))
try:
    base = base.edges("|Z").fillet(6.0)
except Exception:
    pass

body = base

# Stack of 8 rotated slabs
slab_w = 80
slab_d = 30
slab_h = 35
z = 20
for i in range(8):
    slab = cq.Workplane("XY").workplane(offset=z).box(slab_w, slab_d, slab_h, centered=(True, True, False))
    slab = slab.rotate((0, 0, z + slab_h / 2), (0, 0, 1), i * 22.5)
    try:
        slab = slab.edges("|Z").fillet(3.0)
    except Exception:
        pass
    body = body.union(slab)
    z += slab_h

# Finial sphere on top
body = body.union(cq.Workplane("XY").workplane(offset=z).sphere(22))

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
