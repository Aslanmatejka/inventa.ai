from ..core.metadata import ExampleMetadata

metadata = ExampleMetadata(
    id="book_end",
    name="Book End",
    category="accessory",
    keywords=["bookend", "book", "shelf", "library", "holder"],
    description="L-shaped bookend with ribbed vertical face.",
    techniques=["polyline_profile", "guarded_fillet"],
    nominal_dimensions_mm={"base_length": 140.0, "base_width": 110.0, "wall_height": 150.0, "thickness": 8.0},
    difficulty="easy",
)

code = '''import cadquery as cq

base_l = 140.0
base_w = 110.0
wall_h = 150.0
thick = 8.0

# L-profile in XZ
profile = (
    cq.Workplane("XZ")
    .moveTo(0, 0)
    .lineTo(base_l, 0)
    .lineTo(base_l, thick)
    .lineTo(thick, thick)
    .lineTo(thick, wall_h)
    .lineTo(0, wall_h)
    .close()
)
body = profile.extrude(base_w).translate((-base_l / 2.0, -base_w / 2.0, 0))

try:
    body = body.edges("|Y").fillet(min(3.0, thick * 0.35))
except Exception:
    pass

# Decorative ribs on the back of the vertical wall
rib_count = 5
for i in range(rib_count):
    z = thick + (wall_h - thick - 10) * (i + 1) / (rib_count + 1)
    rib = (
        cq.Workplane("XY", origin=(0, 0, z))
        .rect(thick * 1.6, base_w - 20)
        .extrude(2.0)
        .translate((-base_l / 2.0 + thick / 2.0, 0, 0))
    )
    body = body.union(rib)

result = body
'''
