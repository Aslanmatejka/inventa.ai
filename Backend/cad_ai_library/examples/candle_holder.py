from ..core.metadata import ExampleMetadata

metadata = ExampleMetadata(
    id="candle_holder",
    name="Tea Light Candle Holder",
    category="decorative",
    keywords=["candle", "tealight", "holder", "votive", "decor", "home"],
    description="Stepped cylindrical holder sized for a 38mm tealight.",
    techniques=["shell_cavity", "polar_array"],
    nominal_dimensions_mm={"outer_diameter": 70.0, "height": 40.0, "tealight_diameter": 39.0, "tealight_depth": 14.0},
    difficulty="easy",
)

code = '''import cadquery as cq

outer_d = 70.0
height = 40.0
tealight_d = 39.0
tealight_depth = 14.0
vent_count = 6
vent_d = 5.0

body = cq.Workplane("XY").circle(outer_d / 2.0).extrude(height)

# Tealight cavity from the top
cavity = (
    cq.Workplane("XY", origin=(0, 0, height - tealight_depth))
    .circle(tealight_d / 2.0)
    .extrude(tealight_depth + 1)
)
body = body.cut(cavity)

# Decorative vent holes around the side
for i in range(vent_count):
    theta = 360.0 / vent_count * i
    vent = (
        cq.Workplane("YZ", origin=(0, 0, height * 0.35))
        .circle(vent_d / 2.0)
        .extrude(outer_d)
        .rotate((0, 0, 0), (0, 0, 1), theta)
        .translate((0, 0, 0))
    )
    body = body.cut(vent)

try:
    body = body.edges(">Z").fillet(1.5)
except Exception:
    pass

result = body
'''
