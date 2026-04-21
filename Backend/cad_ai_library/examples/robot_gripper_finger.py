from ..core.metadata import ExampleMetadata

metadata = ExampleMetadata(
    id="robot_gripper_finger",
    name="Robot Gripper Finger",
    category="robotics",
    keywords=["gripper", "finger", "robot", "jaw", "claw", "end-effector"],
    description="Parallel-jaw gripper finger with grooved contact face and mount holes.",
    techniques=["polyline_profile", "guarded_fillet"],
    nominal_dimensions_mm={"length": 70.0, "width": 18.0, "thickness": 8.0},
    difficulty="medium",
)

code = '''import cadquery as cq

length = 70.0
width = 18.0
thick = 8.0
mount_hole_d = 3.2

# Side profile in XZ: angled contact face
profile = (
    cq.Workplane("XZ")
    .moveTo(0, 0)
    .lineTo(length, 0)
    .lineTo(length, width * 0.3)
    .lineTo(length * 0.3, width)
    .lineTo(0, width)
    .close()
)
body = profile.extrude(thick).translate((0, -thick / 2.0, 0))

try:
    body = body.edges("|Y").fillet(1.0)
except Exception:
    pass

# Grooves on the contact face (top Z)
for i in range(5):
    x = length * 0.35 + i * 4.5
    groove = (
        cq.Workplane("YZ", origin=(x, 0, width - 0.5))
        .rect(thick - 1.0, 1.0)
        .extrude(3.0)
    )
    body = body.cut(groove)

# Two mount holes at the base
body = (
    body.faces("<Z").workplane()
    .pushPoints([(length * 0.15, 0), (length * 0.4, 0)])
    .hole(mount_hole_d)
)

result = body
'''
