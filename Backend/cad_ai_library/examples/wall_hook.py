from ..core.metadata import ExampleMetadata

metadata = ExampleMetadata(
    id="wall_hook",
    name="Wall Hook",
    category="accessory",
    keywords=["hook", "wall", "coat", "hanger", "key", "mount"],
    description="Wall-mount hook with angled arm and two screw holes.",
    techniques=["polyline_profile", "cbore_hole", "guarded_fillet"],
    nominal_dimensions_mm={"plate_height": 80.0, "plate_width": 25.0, "hook_reach": 40.0, "thickness": 5.0},
    difficulty="medium",
)

code = '''import cadquery as cq

plate_h = 80.0
plate_w = 25.0
reach = 40.0
thick = 5.0
screw_d = 4.2

# Side profile: vertical plate + angled arm + upturned tip
profile = (
    cq.Workplane("XZ")
    .moveTo(0, 0)
    .lineTo(thick, 0)
    .lineTo(thick, plate_h * 0.55)
    .lineTo(thick + reach, plate_h * 0.35)
    .lineTo(thick + reach, plate_h * 0.35 + 10.0)
    .lineTo(thick + reach - 6.0, plate_h * 0.35 + 10.0)
    .lineTo(thick, plate_h * 0.65)
    .lineTo(thick, plate_h)
    .lineTo(0, plate_h)
    .close()
)
body = profile.extrude(plate_w).translate((0, -plate_w / 2.0, 0))

# Screw holes in the plate
body = (
    body.faces("<X")
    .workplane()
    .pushPoints([(0, plate_h * 0.15), (0, plate_h * 0.85)])
    .hole(screw_d)
)

try:
    body = body.edges("|Y").fillet(1.5)
except Exception:
    pass

result = body
'''
