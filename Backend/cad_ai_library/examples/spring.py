from ..core.metadata import ExampleMetadata

metadata = ExampleMetadata(
    id="spring",
    name="Compression Spring Approximation",
    category="mechanical",
    keywords=["spring", "coil", "helical", "compression", "mechanical"],
    description="Spring approximation using stacked rings (avoids helical sweep edge cases).",
    techniques=["stacked_rings_threads"],
    nominal_dimensions_mm={"outer_diameter": 20.0, "wire_diameter": 2.0, "turns": 8, "pitch": 5.0},
    difficulty="medium",
)

code = '''import cadquery as cq

outer_d = 20.0
wire_d = 2.0
turns = 8
pitch = 5.0

r_mean = (outer_d - wire_d) / 2.0

body = None
for i in range(turns):
    z = i * pitch
    ring = (
        cq.Workplane("XY", origin=(0, 0, z))
        .circle(r_mean + wire_d / 2.0)
        .circle(r_mean - wire_d / 2.0)
        .extrude(wire_d)
    )
    if body is None:
        body = ring
    else:
        body = body.union(ring)

# End caps (solid discs so it sits flat)
cap_bot = cq.Workplane("XY").circle(r_mean + wire_d / 2.0).extrude(wire_d * 0.6)
cap_top = (
    cq.Workplane("XY", origin=(0, 0, (turns - 1) * pitch + wire_d - wire_d * 0.6))
    .circle(r_mean + wire_d / 2.0)
    .extrude(wire_d * 0.6)
)
body = body.union(cap_bot).union(cap_top)

result = body
'''
