from ..core.metadata import ExampleMetadata

metadata = ExampleMetadata(
    id="earring_hoop",
    name="Hoop Earring",
    category="wearable",
    keywords=["earring", "hoop", "jewelry", "ear", "ring"],
    description="Round hoop earring with a post stub.",
    techniques=["safe_revolve"],
    nominal_dimensions_mm={"hoop_diameter": 25.0, "wire_diameter": 1.6, "post_length": 10.0},
    difficulty="easy",
)

code = '''import cadquery as cq

hoop_d = 25.0
wire_d = 1.6
post_l = 10.0

r_hoop = hoop_d / 2.0
r_wire = wire_d / 2.0

# Torus via revolve of a circle offset along +X, around Z axis.
profile = (
    cq.Workplane("XZ")
    .moveTo(r_hoop, 0)
    .circle(r_wire)
)
hoop = profile.revolve(360)

# Post sticking out along +X at top of hoop
post = (
    cq.Workplane("YZ", origin=(r_hoop, 0, -r_wire))
    .circle(r_wire)
    .extrude(post_l)
)
body = hoop.union(post)

result = body
'''
