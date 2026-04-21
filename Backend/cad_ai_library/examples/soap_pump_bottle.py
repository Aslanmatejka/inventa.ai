from ..core.metadata import ExampleMetadata

metadata = ExampleMetadata(
    id="soap_pump_bottle",
    name="Soap Pump Bottle",
    category="sanitary",
    keywords=["soap", "pump", "bottle", "dispenser", "bathroom", "lotion"],
    description="Soap dispenser bottle with threaded-style neck and pump stem.",
    techniques=["safe_revolve", "stacked_rings_threads"],
    nominal_dimensions_mm={"body_diameter": 65.0, "body_height": 150.0, "neck_diameter": 28.0, "pump_height": 90.0},
    difficulty="medium",
)

code = '''import cadquery as cq

body_d = 65.0
body_h = 150.0
neck_d = 28.0
neck_h = 14.0
pump_h = 90.0
nozzle_l = 25.0

# Body
profile = (
    cq.Workplane("XZ")
    .moveTo(0, 0)
    .lineTo(body_d / 2.0, 0)
    .lineTo(body_d / 2.0, body_h * 0.85)
    .spline([(neck_d / 2.0 + 3, body_h * 0.95), (neck_d / 2.0, body_h)])
    .lineTo(0, body_h)
    .close()
)
body = profile.revolve(360)

# Neck ring threads via stacked rings
thread_pitch = 2.5
thread_count = int(neck_h / thread_pitch)
for i in range(thread_count):
    z = body_h + i * thread_pitch
    ring_outer = (
        cq.Workplane("XY", origin=(0, 0, z))
        .circle(neck_d / 2.0 + 0.8)
        .extrude(thread_pitch * 0.6)
    )
    ring_inner = (
        cq.Workplane("XY", origin=(0, 0, z))
        .circle(neck_d / 2.0)
        .extrude(thread_pitch * 0.7)
    )
    body = body.union(ring_outer.cut(ring_inner))

# Pump collar
collar = (
    cq.Workplane("XY", origin=(0, 0, body_h + neck_h))
    .circle(neck_d / 2.0 + 3)
    .extrude(8)
)
body = body.union(collar)

# Pump stem straight up
stem = (
    cq.Workplane("XY", origin=(0, 0, body_h + neck_h + 8))
    .circle(6.0)
    .extrude(pump_h - 10)
)
body = body.union(stem)

# Nozzle head (box pointing sideways)
nozzle = (
    cq.Workplane("XY", origin=(0, -nozzle_l / 2.0, body_h + neck_h + pump_h - 12))
    .box(18, nozzle_l, 14, centered=(True, False, False))
)
try:
    nozzle = nozzle.edges("|Y").fillet(2.0)
except Exception:
    pass
body = body.union(nozzle)

result = body
'''
