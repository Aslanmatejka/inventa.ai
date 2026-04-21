from ..core.metadata import ExampleMetadata

metadata = ExampleMetadata(
    id="spoon",
    name="Serving Spoon",
    category="accessory",
    keywords=["spoon", "utensil", "cutlery", "scoop", "kitchen"],
    description="Loft-formed spoon bowl on a tapered handle.",
    techniques=["loft_frustum", "guarded_fillet"],
    nominal_dimensions_mm={"length": 180.0, "bowl_width": 45.0, "bowl_depth": 12.0, "handle_width": 18.0},
    difficulty="medium",
)

code = '''import cadquery as cq

total_len = 180.0
bowl_w = 45.0
bowl_l = 60.0
bowl_depth = 12.0
handle_w = 18.0
handle_thick = 6.0

# Handle (rounded rectangle extruded)
handle = (
    cq.Workplane("XY")
    .rect(total_len - bowl_l, handle_w)
    .extrude(handle_thick)
    .translate((-(bowl_l) / 2.0 - (total_len - bowl_l) / 2.0 + bowl_l / 2.0, 0, 0))
)
try:
    handle = handle.edges("|Z").fillet(handle_w * 0.4)
except Exception:
    pass

# Spoon bowl: shallow elliptical dish via loft
bowl_outer = (
    cq.Workplane("XY", origin=(bowl_l / 2.0, 0, 0))
    .ellipse(bowl_l / 2.0, bowl_w / 2.0)
    .workplane(offset=handle_thick)
    .ellipse(bowl_l / 2.0 * 0.9, bowl_w / 2.0 * 0.9)
    .loft(combine=True)
)
bowl_cavity = (
    cq.Workplane("XY", origin=(bowl_l / 2.0, 0, handle_thick - bowl_depth))
    .ellipse(bowl_l / 2.0 - 2.0, bowl_w / 2.0 - 2.0)
    .workplane(offset=bowl_depth + 1)
    .ellipse(bowl_l / 2.0 * 0.85, bowl_w / 2.0 * 0.85)
    .loft(combine=True)
)
bowl = bowl_outer.cut(bowl_cavity)

body = handle.union(bowl)

try:
    body = body.edges(">Z or <Z").fillet(1.0)
except Exception:
    pass

result = body
'''
