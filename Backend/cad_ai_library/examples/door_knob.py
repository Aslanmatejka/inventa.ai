from ..core.metadata import ExampleMetadata

metadata = ExampleMetadata(
    id="door_knob",
    name="Door Knob",
    category="accessory",
    keywords=["door", "knob", "handle", "passage", "hardware"],
    description="Rounded door knob with backplate and spindle hole.",
    techniques=["safe_revolve", "cbore_hole"],
    nominal_dimensions_mm={"knob_diameter": 55.0, "total_length": 80.0, "backplate_diameter": 72.0},
    difficulty="medium",
)

code = '''import cadquery as cq

knob_d = 55.0
backplate_d = 72.0
backplate_t = 6.0
stem_d = 22.0
stem_l = 20.0
knob_l = 54.0
spindle_across = 8.0

# Revolve profile (all X >= 0)
profile = (
    cq.Workplane("XZ")
    .moveTo(0, 0)
    .lineTo(backplate_d / 2.0, 0)
    .lineTo(backplate_d / 2.0, backplate_t)
    .lineTo(stem_d / 2.0, backplate_t + 2)
    .lineTo(stem_d / 2.0, backplate_t + stem_l)
    .spline([(knob_d / 2.0, backplate_t + stem_l + 8),
             (knob_d / 2.0, backplate_t + stem_l + knob_l * 0.5),
             (knob_d / 2.0 * 0.4, backplate_t + stem_l + knob_l * 0.95)])
    .lineTo(0, backplate_t + stem_l + knob_l)
    .close()
)
body = profile.revolve(360)

# Square spindle hole through the knob
spindle = (
    cq.Workplane("XY", origin=(0, 0, -1))
    .rect(spindle_across, spindle_across)
    .extrude(backplate_t + stem_l + knob_l + 2)
)
body = body.cut(spindle)

result = body
'''
