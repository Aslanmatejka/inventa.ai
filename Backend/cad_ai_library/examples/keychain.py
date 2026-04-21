from ..core.metadata import ExampleMetadata

metadata = ExampleMetadata(
    id="keychain",
    name="Keychain Tag",
    category="accessory",
    keywords=["keychain", "tag", "fob", "keyring", "label"],
    description="Rounded rectangular keychain tag with split-ring hole.",
    techniques=["guarded_fillet"],
    nominal_dimensions_mm={"length": 50.0, "width": 25.0, "thickness": 4.0, "ring_hole_diameter": 5.0},
    difficulty="easy",
)

code = '''import cadquery as cq

length = 50.0
width = 25.0
thick = 4.0
ring_hole_d = 5.0
ring_edge_offset = 7.0

body = cq.Workplane("XY").box(length, width, thick, centered=(True, True, False))

try:
    body = body.edges("|Z").fillet(min(6.0, width * 0.25))
except Exception:
    pass
try:
    body = body.edges(">Z or <Z").fillet(min(0.8, thick * 0.2))
except Exception:
    pass

# Keyring hole near one short edge
body = (
    body.faces(">Z")
    .workplane()
    .center(-length / 2.0 + ring_edge_offset, 0)
    .hole(ring_hole_d)
)

result = body
'''
