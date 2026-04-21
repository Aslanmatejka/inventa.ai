from ..core.metadata import ExampleMetadata

metadata = ExampleMetadata(
    id="bike_pedal",
    name="Bicycle Pedal",
    category="vehicle",
    keywords=["pedal", "bike", "bicycle", "cycle", "foot", "cycling"],
    description="Platform bicycle pedal with grip pins and spindle bore.",
    techniques=["polar_array", "guarded_fillet"],
    nominal_dimensions_mm={"length": 100.0, "width": 95.0, "thickness": 18.0},
    difficulty="medium",
)

code = '''import cadquery as cq

length = 100.0
width = 95.0
thick = 18.0
spindle_d = 12.0
pin_d = 3.0
pin_h = 3.0

body = cq.Workplane("XY").box(length, width, thick, centered=(True, True, False))
try:
    body = body.edges("|Z").fillet(6.0)
except Exception:
    pass
try:
    body = body.edges(">Z or <Z").fillet(1.5)
except Exception:
    pass

# Weight-saving oval on each side of the spindle
for dx in (-length * 0.3, length * 0.3):
    relief = (
        cq.Workplane("XY", origin=(dx, 0, -1))
        .ellipse(length * 0.15, width * 0.3)
        .extrude(thick + 2)
    )
    body = body.cut(relief)

# Spindle bore along Y
spindle = (
    cq.Workplane("XZ", origin=(0, -width / 2.0 - 1, 0))
    .circle(spindle_d / 2.0)
    .extrude(width + 2)
)
body = body.cut(spindle)

# Grip pins: 4 per side (top and bottom)
pin_pts = []
for dx in (-length * 0.35, -length * 0.12, length * 0.12, length * 0.35):
    for dy in (-width * 0.35, width * 0.35):
        pin_pts.append((dx, dy))

for z_top in (thick, 0):
    for (px, py) in pin_pts:
        if z_top == thick:
            pin = (
                cq.Workplane("XY", origin=(px, py, thick))
                .circle(pin_d / 2.0)
                .extrude(pin_h)
            )
        else:
            pin = (
                cq.Workplane("XY", origin=(px, py, -pin_h))
                .circle(pin_d / 2.0)
                .extrude(pin_h)
            )
        body = body.union(pin)

result = body
'''
