from ..core.metadata import ExampleMetadata

metadata = ExampleMetadata(
    id="medicine_bottle",
    name="Medicine Bottle",
    category="container",
    keywords=["medicine", "pill", "bottle", "prescription", "pharma", "medical"],
    description="Cylindrical medicine bottle with child-resistant-style threaded neck (stacked rings).",
    techniques=["stacked_rings_threads", "shell_cavity"],
    nominal_dimensions_mm={"body_diameter": 55.0, "body_height": 95.0, "neck_diameter": 38.0, "wall": 2.0},
    difficulty="medium",
)

code = '''import cadquery as cq

body_d = 55.0
body_h = 95.0
neck_d = 38.0
neck_h = 12.0
wall = 2.0
ring_count = 3

body = cq.Workplane("XY").circle(body_d / 2.0).extrude(body_h)

# Neck
neck = (
    cq.Workplane("XY", origin=(0, 0, body_h))
    .circle(neck_d / 2.0)
    .extrude(neck_h)
)
body = body.union(neck)

# Stacked ring "threads" on neck (no helix sweep)
for i in range(ring_count):
    z = body_h + 2.0 + i * 2.5
    ring = (
        cq.Workplane("XY", origin=(0, 0, z))
        .circle(neck_d / 2.0 + 1.2)
        .circle(neck_d / 2.0)
        .extrude(1.2)
    )
    body = body.union(ring)

# Hollow interior
body = body.faces(">Z").shell(-wall)

try:
    body = body.edges(">Z or <Z").fillet(0.8)
except Exception:
    pass

result = body
'''
