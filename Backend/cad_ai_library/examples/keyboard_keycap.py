from ..core.metadata import ExampleMetadata

metadata = ExampleMetadata(
    id="keyboard_keycap",
    name="Mechanical Keyboard Keycap",
    category="computing",
    keywords=["keyboard", "keycap", "key", "cherry", "mechanical", "mx", "typing"],
    description="Cherry-profile mechanical keyboard keycap with dished top and hollow bottom with MX+ stem.",
    techniques=["loft_shape"],
    nominal_dimensions_mm={"base": 18.0, "top": 14.0, "height": 10.0, "stem_size": 4.0},
    difficulty="medium",
)

code = '''import cadquery as cq

base = 18.0
top = 14.0
height = 10.0
wall = 1.5
stem_outer = 5.5
stem_inner_cross = 4.0

# Outer loft
outer = (
    cq.Workplane("XY")
    .rect(base, base)
    .workplane(offset=height)
    .rect(top, top)
    .loft(combine=True)
)
try:
    outer = outer.edges("|Z").fillet(1.2)
except Exception:
    pass

# Dish the top
dish = cq.Workplane("XY", origin=(0, 0, height + 10)).sphere(11)
outer = outer.cut(dish)

# Hollow underside
inner = (
    cq.Workplane("XY", origin=(0, 0, -0.1))
    .rect(base - 2 * wall, base - 2 * wall)
    .workplane(offset=height - 2 * wall)
    .rect(top - 2 * wall, top - 2 * wall)
    .loft(combine=True)
)
body = outer.cut(inner)

# Cherry MX stem cross: cylinder minus plus-sign
stem_post = (
    cq.Workplane("XY", origin=(0, 0, 0))
    .circle(stem_outer / 2.0)
    .extrude(height - wall * 1.5)
)
cross_h = (
    cq.Workplane("XY", origin=(0, 0, -0.1))
    .rect(stem_inner_cross, 1.3)
    .extrude(height)
)
cross_v = (
    cq.Workplane("XY", origin=(0, 0, -0.1))
    .rect(1.3, stem_inner_cross)
    .extrude(height)
)
stem = stem_post.cut(cross_h).cut(cross_v)
body = body.union(stem)

result = body
'''
