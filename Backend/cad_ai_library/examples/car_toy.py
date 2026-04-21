from ..core.metadata import ExampleMetadata

metadata = ExampleMetadata(
    id="car_toy",
    name="Toy Car",
    category="vehicle",
    keywords=["car", "toy", "vehicle", "automobile", "racer"],
    description="Simplified toy car body with cabin and four wheels.",
    techniques=["guarded_fillet", "polar_array"],
    nominal_dimensions_mm={"length": 120.0, "width": 50.0, "height": 35.0, "wheel_diameter": 22.0},
    difficulty="medium",
)

code = '''import cadquery as cq

length = 120.0
width = 50.0
chassis_h = 18.0
cabin_h = 17.0
wheel_d = 22.0
wheel_w = 8.0

# Chassis
chassis = cq.Workplane("XY").box(length, width, chassis_h, centered=(True, True, False))
try:
    chassis = chassis.edges("|Z").fillet(5.0)
except Exception:
    pass

# Cabin (narrower, set back)
cabin = (
    cq.Workplane("XY", origin=(-length * 0.05, 0, chassis_h))
    .box(length * 0.55, width * 0.8, cabin_h, centered=(True, True, False))
)
try:
    cabin = cabin.edges("|Z or >Z").fillet(4.0)
except Exception:
    pass

body = chassis.union(cabin)

# Four wheels (cylinders along Y axis)
wheel_positions = [
    (length * 0.32, width / 2.0),
    (length * 0.32, -width / 2.0),
    (-length * 0.32, width / 2.0),
    (-length * 0.32, -width / 2.0),
]
for (x, y) in wheel_positions:
    wheel = (
        cq.Workplane("XZ", origin=(x, y, wheel_d / 2.0))
        .circle(wheel_d / 2.0)
        .extrude(wheel_w if y > 0 else -wheel_w)
    )
    body = body.union(wheel)

# Translate whole model so wheels touch Z=0
body = body.translate((0, 0, 0))  # wheels already at Z=0 bottom via origin

result = body

# --- Modern finishing pass (guarded) ---
try:
    result = result.edges("|Z").fillet(1.2)
except Exception:
    pass
try:
    result = result.faces(">Z").edges().chamfer(0.5)
except Exception:
    pass
try:
    result = result.faces("<Z").edges().fillet(0.8)
except Exception:
    pass
'''
