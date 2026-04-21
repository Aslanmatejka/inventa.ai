from ..core.metadata import ExampleMetadata

metadata = ExampleMetadata(
    id="lamp",
    name="Table Lamp",
    category="lighting",
    keywords=["lamp", "light", "shade", "table lamp", "desk lamp"],
    description="Circular base, tapered stem, and a frustum-shaped shade built by lofting two circles.",
    techniques=["circular base", "cylinder stem", "loft frustum shade"],
    nominal_dimensions_mm={"base_diameter": 140.0, "height": 300.0},
    difficulty="intermediate",
)

code = '''\
import cadquery as cq

base_diameter = 140.0
base_height = 18.0
stem_diameter = 18.0
stem_height = 200.0
shade_bottom = 90.0
shade_top = 140.0
shade_height = 80.0

# Base (grounded)
base = cq.Workplane("XY").circle(base_diameter / 2.0).extrude(base_height)
try:
    base = base.edges(">Z").fillet(3.0)
except Exception:
    pass

# Stem
stem = (
    cq.Workplane("XY", origin=(0, 0, base_height))
    .circle(stem_diameter / 2.0)
    .extrude(stem_height)
)

# Shade — loft narrow->wide for a frustum
shade = (
    cq.Workplane("XY", origin=(0, 0, base_height + stem_height))
    .circle(shade_bottom / 2.0)
    .workplane(offset=shade_height)
    .circle(shade_top / 2.0)
    .loft(combine=True)
)
# Hollow the shade
try:
    shade = shade.faces(">Z").shell(-2.0)
except Exception:
    pass

result = base.union(stem).union(shade)
'''
