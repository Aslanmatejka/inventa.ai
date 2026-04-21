from ..core.metadata import ExampleMetadata

metadata = ExampleMetadata(
    id="toothbrush_holder",
    name="Toothbrush Holder",
    category="container",
    keywords=["toothbrush", "holder", "bathroom", "stand", "cup"],
    description="Multi-slot toothbrush holder with drainage hole in each slot.",
    techniques=["shell_cavity", "polar_array"],
    nominal_dimensions_mm={"diameter": 80.0, "height": 110.0, "slots": 4},
    difficulty="easy",
)

code = '''import cadquery as cq
import math

diameter = 80.0
height = 110.0
wall = 2.5
slots = 4
slot_d = 18.0
slot_depth = 90.0
drain_d = 3.0

# Solid cylinder body
body = cq.Workplane("XY").circle(diameter / 2.0).extrude(height)
try:
    body = body.edges(">Z or <Z").fillet(2.0)
except Exception:
    pass

# Shell so it's hollow (open top)
body = body.faces(">Z").shell(-wall)

# Top lid plate with slots
lid = (
    cq.Workplane("XY", origin=(0, 0, height - 6))
    .circle(diameter / 2.0 - wall - 0.2)
    .extrude(6)
)
# Polar array of slots
slot_r = (diameter / 2.0) * 0.45
for i in range(slots):
    theta = math.radians(90 + 360.0 / slots * i)
    x = slot_r * math.cos(theta)
    y = slot_r * math.sin(theta)
    cutter = (
        cq.Workplane("XY", origin=(x, y, height - slot_depth - 1))
        .circle(slot_d / 2.0)
        .extrude(slot_depth + 7)
    )
    lid = lid.cut(cutter)
    # Drainage below each slot
    drain = (
        cq.Workplane("XY", origin=(x, y, height - slot_depth - 2))
        .circle(drain_d / 2.0)
        .extrude(4)
    )
    lid = lid.cut(drain)

body = body.union(lid)

result = body
'''
