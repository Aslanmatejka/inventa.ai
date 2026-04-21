from ..core.metadata import ExampleMetadata

metadata = ExampleMetadata(
    id="cable_clip",
    name="Adhesive Cable Clip",
    category="accessory",
    keywords=["cable", "clip", "wire", "cord", "organizer", "management"],
    description="Adhesive-mount cable clip with sprung top jaw.",
    techniques=["polyline_profile", "guarded_fillet"],
    nominal_dimensions_mm={"base_length": 25.0, "base_width": 18.0, "cable_diameter": 6.0},
    difficulty="easy",
)

code = '''import cadquery as cq

base_l = 25.0
base_w = 18.0
base_t = 3.0
cable_d = 6.0
wall = 2.0

base = cq.Workplane("XY").box(base_l, base_w, base_t, centered=(True, True, False))
try:
    base = base.edges("|Z").fillet(2.5)
except Exception:
    pass

# Clip profile (side view in YZ): U-shape that grips the cable
profile = (
    cq.Workplane("YZ")
    .moveTo(-base_w / 2.0, base_t)
    .lineTo(-base_w / 2.0 + wall, base_t)
    .lineTo(-base_w / 2.0 + wall, base_t + wall)
    .lineTo(-cable_d / 2.0 - wall, base_t + wall)
    .threePointArc((0, base_t + cable_d / 2.0 + wall + 1.0), (cable_d / 2.0 + wall, base_t + wall))
    .lineTo(base_w / 2.0 - wall, base_t + wall)
    .lineTo(base_w / 2.0 - wall, base_t)
    .lineTo(base_w / 2.0, base_t)
    .lineTo(base_w / 2.0, base_t + cable_d + 2 * wall)
    .lineTo(-base_w / 2.0, base_t + cable_d + 2 * wall)
    .close()
)
clip = profile.extrude(base_l * 0.6).translate((-base_l * 0.3, 0, 0))

body = base.union(clip)

result = body
'''
