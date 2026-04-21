from ..core.metadata import ExampleMetadata

metadata = ExampleMetadata(
    id="stool",
    name="Four-Leg Stool",
    category="furniture",
    keywords=["stool", "seat", "chair", "furniture", "footstool"],
    description="Round seat on four tapered legs.",
    techniques=["loft_frustum", "polar_array"],
    nominal_dimensions_mm={"seat_diameter": 320.0, "seat_thickness": 30.0, "leg_length": 420.0},
    difficulty="medium",
)

code = '''import cadquery as cq
import math

seat_d = 320.0
seat_t = 30.0
leg_len = 420.0
leg_top = 25.0
leg_bot = 18.0
leg_inset = 60.0  # from seat center

# Seat
seat = (
    cq.Workplane("XY", origin=(0, 0, leg_len))
    .circle(seat_d / 2.0)
    .extrude(seat_t)
)
try:
    seat = seat.edges(">Z or <Z").fillet(4.0)
except Exception:
    pass

body = seat

# Legs: tapered cylinders via loft
leg_r = (seat_d / 2.0) - leg_inset
for i in range(4):
    theta = 45 + 90 * i
    x = leg_r * math.cos(math.radians(theta))
    y = leg_r * math.sin(math.radians(theta))
    leg = (
        cq.Workplane("XY", origin=(x, y, 0))
        .circle(leg_bot / 2.0)
        .workplane(offset=leg_len)
        .circle(leg_top / 2.0)
        .loft(combine=True)
    )
    body = body.union(leg)

result = body
'''
