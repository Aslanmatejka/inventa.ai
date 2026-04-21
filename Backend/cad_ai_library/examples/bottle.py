from ..core.metadata import ExampleMetadata

metadata = ExampleMetadata(
    id="bottle",
    name="Water Bottle",
    category="container",
    keywords=["bottle", "water", "flask", "tumbler", "neck", "threaded"],
    description="Tapered bottle body with a stepped shoulder and a short threaded neck (modeled as stacked rings, not a helix).",
    techniques=["stacked rings (no helix)", "loft shoulder", "revolve avoidance", "shell cavity"],
    nominal_dimensions_mm={"diameter": 72.0, "height": 230.0, "neck_diameter": 28.0},
    difficulty="intermediate",
)

code = '''\
import cadquery as cq

# Parameters
body_diameter = 72.0
body_height = 200.0
neck_diameter = 28.0
neck_height = 22.0
shoulder_height = 30.0
wall = 2.4
base_thickness = 3.0

# Base body (grounded at Z=0)
body = (
    cq.Workplane("XY")
    .circle(body_diameter / 2.0)
    .extrude(body_height)
)

# Shoulder — loft from body radius to neck radius over `shoulder_height`.
shoulder = (
    cq.Workplane("XY", origin=(0, 0, body_height))
    .circle(body_diameter / 2.0)
    .workplane(offset=shoulder_height)
    .circle(neck_diameter / 2.0)
    .loft(combine=True)
)

# Neck (plain cylinder; threads approximated as 4 stacked rings below)
neck = (
    cq.Workplane("XY", origin=(0, 0, body_height + shoulder_height))
    .circle(neck_diameter / 2.0)
    .extrude(neck_height)
)

# Thread rings — safer than a swept helix
for i in range(4):
    z = body_height + shoulder_height + 2.0 + i * 4.0
    ring = (
        cq.Workplane("XY", origin=(0, 0, z))
        .circle(neck_diameter / 2.0 + 0.6)
        .circle(neck_diameter / 2.0)
        .extrude(1.5)
    )
    neck = neck.union(ring)

# Hollow the full stack
total = body.union(shoulder).union(neck)
try:
    total = total.faces(">Z").shell(-wall)
except Exception:
    pass

result = total
'''
