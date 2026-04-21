from ..core.metadata import ExampleMetadata

metadata = ExampleMetadata(
    id="whiskey_tumbler",
    name="Whiskey Tumbler",
    category="drinkware",
    keywords=["whiskey", "tumbler", "glass", "rocks", "drinkware", "bourbon"],
    description="Thick-walled whiskey tumbler (rocks glass) with heavy faceted base.",
    techniques=["safe_revolve", "polar_array"],
    nominal_dimensions_mm={"diameter": 85.0, "height": 95.0, "wall": 4.0, "base_thickness": 15.0},
    difficulty="medium",
)

code = '''import cadquery as cq
import math

diameter = 85.0
height = 95.0
wall = 4.0
base_t = 15.0

r = diameter / 2.0

# Cup profile
profile = (
    cq.Workplane("XZ")
    .moveTo(0, 0)
    .lineTo(r, 0)
    .lineTo(r, height)
    .lineTo(r - wall, height)
    .lineTo(r - wall, base_t)
    .lineTo(0, base_t)
    .close()
)
body = profile.revolve(360)

# Vertical facet cuts around the lower outside for a "whiskey" faceted look
facet_count = 10
facet_d = 3.0
for i in range(facet_count):
    theta = 360.0 / facet_count * i
    x = (r + 0.5) * math.cos(math.radians(theta))
    y = (r + 0.5) * math.sin(math.radians(theta))
    v = (math.cos(math.radians(theta)), math.sin(math.radians(theta)), 0)
    facet = (
        cq.Workplane(cq.Plane(origin=(x, y, base_t * 0.5),
                              xDir=(-v[1], v[0], 0),
                              normal=v))
        .rect(facet_d, base_t * 0.9)
        .extrude(2.5)
    )
    body = body.cut(facet)

result = body
'''
