from ..core.metadata import ExampleMetadata

metadata = ExampleMetadata(
    id="exoskeleton_joint",
    name="Exoskeleton Joint Actuator",
    category="prosthetic",
    keywords=["exoskeleton", "exosuit", "powered prosthetic", "robotic joint", "actuator", "rehabilitation", "assistive", "motorized knee", "modern prosthesis"],
    description="Powered exoskeleton knee actuator: two structural brackets, central gearbox housing, and harmonic-drive output.",
    techniques=["boolean_union", "boolean_cut", "guarded_fillet"],
    nominal_dimensions_mm={"diameter": 110.0, "width": 60.0, "arm_length": 160.0},
    difficulty="advanced",
)

code = '''import cadquery as cq
import math

W = 60.0
R = 55.0

# Central gearbox cylinder
gearbox = cq.Workplane("YZ").circle(R).extrude(W, both=True)
# Lightening pocket on front face
pocket = (cq.Workplane("YZ").workplane(offset=W + 1)
          .circle(R - 12).extrude(6))
gearbox = gearbox.cut(pocket)
# Center output shaft hole
shaft = cq.Workplane("YZ").circle(8).extrude(W + 20, both=True)
gearbox = gearbox.cut(shaft)

# Mounting bolt circle (8 bolts on face)
for i in range(8):
    ang = i * 45
    bz = (R - 20) * math.sin(math.radians(ang))
    by = (R - 20) * math.cos(math.radians(ang))
    bolt = (cq.Workplane("YZ").workplane(offset=W + 1)
            .center(by, bz).circle(2).extrude(4))
    gearbox = gearbox.cut(bolt)

# Upper structural bracket (thigh side, pointing +Z from joint)
upper_pts = [(-15, 0), (15, 0), (10, 160), (-10, 160)]
upper = (cq.Workplane("XZ").polyline(upper_pts).close()
         .extrude(W * 0.6, both=True))
upper = upper.translate((0, 0, R - 5))
try:
    upper = upper.edges("|Y").fillet(4.0)
except Exception:
    pass

# Lower structural bracket (shin side, pointing -Z)
lower_pts = [(-15, 0), (15, 0), (10, -160), (-10, -160)]
lower = (cq.Workplane("XZ").polyline(lower_pts).close()
         .extrude(W * 0.6, both=True))
lower = lower.translate((0, 0, -(R - 5)))
try:
    lower = lower.edges("|Y").fillet(4.0)
except Exception:
    pass

# Strap mount holes at far ends of each bracket
for z in [160 + R - 5, -(160 + R - 5)]:
    mount = (cq.Workplane("XY").workplane(offset=z - 10)
             .rect(W * 0.5, 6).extrude(20))
    mount = mount.cut(cq.Workplane("XY").workplane(offset=z - 10)
                      .rect(W * 0.35, 2.5).extrude(20))

body = gearbox.union(upper).union(lower)

# Motor can protrusion on side
motor = (cq.Workplane("YZ").workplane(offset=-(W + 1))
         .circle(22).extrude(40))
motor_bore = (cq.Workplane("YZ").workplane(offset=-(W + 1))
              .circle(18).extrude(40))
motor = motor.cut(motor_bore)
body = body.union(motor)

# Cable port on top-back
cable = (cq.Workplane("XZ").workplane(offset=-(W + 1))
         .center(-30, 30).circle(4).extrude(6))
body = body.cut(cable)

try:
    body = body.edges("|Y").fillet(1.5)
except Exception:
    pass

result = body
'''
