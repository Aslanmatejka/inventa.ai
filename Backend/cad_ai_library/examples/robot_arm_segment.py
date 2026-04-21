from ..core.metadata import ExampleMetadata

metadata = ExampleMetadata(
    id="robot_arm_segment",
    name="Robot Arm Segment",
    category="robotics",
    keywords=["robot", "arm", "segment", "link", "servo", "bracket"],
    description="Aluminum-style robot arm segment with servo mount holes and weight-saving cutout.",
    techniques=["polyline_profile", "cbore_hole", "guarded_fillet"],
    nominal_dimensions_mm={"length": 120.0, "width": 28.0, "height": 40.0, "wall": 3.0},
    difficulty="medium",
)

code = '''import cadquery as cq

length = 120.0
width = 28.0
height = 40.0
wall = 3.0
servo_hole_d = 3.2

# U-channel profile in YZ
profile = (
    cq.Workplane("YZ")
    .moveTo(-width / 2.0, 0)
    .lineTo(width / 2.0, 0)
    .lineTo(width / 2.0, height)
    .lineTo(width / 2.0 - wall, height)
    .lineTo(width / 2.0 - wall, wall)
    .lineTo(-width / 2.0 + wall, wall)
    .lineTo(-width / 2.0 + wall, height)
    .lineTo(-width / 2.0, height)
    .close()
)
body = profile.extrude(length).translate((-length / 2.0, 0, 0))

try:
    body = body.edges("|X").fillet(1.5)
except Exception:
    pass

# Weight-saving oval cutouts on each side wall
oval = (
    cq.Workplane("XZ", origin=(0, -width / 2.0 - 0.1, height / 2.0 + wall / 2.0))
    .ellipse(length * 0.3, height * 0.28)
    .extrude(width + 0.2)
)
body = body.cut(oval)

# Servo mount holes on both short ends
for xc in (-length / 2.0 + wall, length / 2.0 - wall):
    body = (
        body.faces("<X" if xc < 0 else ">X")
        .workplane()
        .pushPoints([(0, height * 0.25), (0, height * 0.75)])
        .hole(servo_hole_d)
    )

result = body
'''
