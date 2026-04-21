from ..core.metadata import ExampleMetadata

metadata = ExampleMetadata(
    id="knob",
    name="Control Knob",
    category="mechanical",
    keywords=["knob", "dial", "handle", "grip", "control", "volume"],
    description="Knurled-style control knob with D-shaped shaft bore and indicator flat.",
    techniques=["polar_array", "guarded_fillet", "shell_cavity"],
    nominal_dimensions_mm={"diameter": 30.0, "height": 22.0, "shaft_diameter": 6.0},
    difficulty="medium",
)

code = '''import cadquery as cq

diameter = 30.0
height = 22.0
shaft_d = 6.0
flat_depth = 0.5  # D-shape flat
grip_count = 24
grip_depth = 0.8

body = cq.Workplane("XY").circle(diameter / 2.0).extrude(height)

# Knurl-like flutes
for i in range(grip_count):
    theta = 360.0 / grip_count * i
    cutter = (
        cq.Workplane("XY", origin=(diameter / 2.0, 0, 0))
        .circle(grip_depth)
        .extrude(height)
        .rotate((0, 0, 0), (0, 0, 1), theta)
    )
    body = body.cut(cutter)

# Indicator line on top
indicator = (
    cq.Workplane("XY", origin=(0, 0, height - 1))
    .rect(1.5, diameter / 2.0)
    .extrude(1.1)
    .translate((0, diameter / 4.0, 0))
)
body = body.cut(indicator)

# Shaft bore with D-flat
shaft_cut = cq.Workplane("XY").circle(shaft_d / 2.0).extrude(height)
body = body.cut(shaft_cut)
flat = (
    cq.Workplane("XY")
    .rect(shaft_d, flat_depth * 2)
    .extrude(height)
    .translate((0, shaft_d / 2.0 - flat_depth, 0))
)
body = body.cut(flat)

try:
    body = body.edges(">Z").fillet(1.0)
except Exception:
    pass

result = body
'''
