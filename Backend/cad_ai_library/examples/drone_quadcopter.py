from ..core.metadata import ExampleMetadata

metadata = ExampleMetadata(
    id="drone_quadcopter",
    name="Quadcopter Drone Frame",
    category="vehicle",
    keywords=["drone", "quadcopter", "uav", "frame", "arm", "motor mount"],
    description="Central body plus four arms arranged in an X with motor-mount bosses at each tip.",
    techniques=["central body", "X-arm layout via rotations", "motor-mount bosses"],
    nominal_dimensions_mm={"span": 240.0, "body_size": 70.0},
    difficulty="intermediate",
)

code = '''\
import cadquery as cq

body_size = 70.0
body_height = 15.0
arm_length = 85.0
arm_width = 18.0
arm_thickness = 10.0
motor_mount_diameter = 28.0
motor_mount_thickness = 6.0

body = cq.Workplane("XY").box(body_size, body_size, body_height, centered=(True, True, False))
try:
    body = body.edges("|Z").fillet(6.0)
except Exception:
    pass

frame = body

# Four arms at 45° offsets (X layout)
arm_template = (
    cq.Workplane("XY", origin=(body_size / 2.0 + arm_length / 2.0, 0, (body_height - arm_thickness) / 2.0))
    .box(arm_length, arm_width, arm_thickness, centered=(True, True, False))
)

for angle in (45, 135, 225, 315):
    arm = arm_template.rotate((0, 0, 0), (0, 0, 1), angle)
    frame = frame.union(arm)

    # Motor-mount boss at the tip of each arm
    import math
    tip_distance = body_size / 2.0 + arm_length
    x = tip_distance * math.cos(math.radians(angle))
    y = tip_distance * math.sin(math.radians(angle))
    boss = (
        cq.Workplane("XY", origin=(x, y, (body_height - arm_thickness) / 2.0 + arm_thickness))
        .circle(motor_mount_diameter / 2.0)
        .extrude(motor_mount_thickness)
    )
    frame = frame.union(boss)

result = frame
'''
