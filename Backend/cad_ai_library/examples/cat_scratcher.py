from ..core.metadata import ExampleMetadata

metadata = ExampleMetadata(
    id="cat_scratcher",
    name="Cat Scratcher Post",
    category="pet",
    keywords=["cat", "scratcher", "post", "scratching", "pet", "sisal"],
    description="Cat scratcher post: round base with vertical rope column.",
    techniques=["safe_revolve"],
    nominal_dimensions_mm={"base_diameter": 300.0, "base_height": 30.0, "post_height": 500.0, "post_diameter": 80.0},
    difficulty="easy",
)

code = '''import cadquery as cq

base_d = 300.0
base_h = 30.0
post_d = 80.0
post_h = 500.0

base = cq.Workplane("XY").circle(base_d / 2.0).extrude(base_h)
try:
    base = base.edges(">Z or <Z").fillet(4.0)
except Exception:
    pass

post = (
    cq.Workplane("XY", origin=(0, 0, base_h))
    .circle(post_d / 2.0)
    .extrude(post_h)
)

# Cap ball on top
cap = cq.Workplane("XY", origin=(0, 0, base_h + post_h)).sphere(post_d * 0.55)

body = base.union(post).union(cap)

result = body
'''
