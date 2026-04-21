from ..core.metadata import ExampleMetadata

metadata = ExampleMetadata(
    id="revolver",
    name="Revolver Handgun",
    category="firearm",
    keywords=["revolver", "gun", "firearm", "pistol", "handgun", "weapon", "prop"],
    description="Stylized six-shooter prop: grip, frame, cylinder, and barrel (display model, not functional).",
    techniques=["boolean_union", "polar_pattern"],
    nominal_dimensions_mm={"length": 260.0, "height": 150.0, "thickness": 35.0},
    difficulty="medium",
)

code = '''import cadquery as cq
import math

# Frame body (flat plate profile)
frame_pts = [(-40, 0), (120, 0), (120, 50), (-20, 50),
             (-40, 120), (-60, 120), (-80, 40)]
frame = (cq.Workplane("XZ").polyline(frame_pts).close()
         .extrude(35, both=False))
frame = frame.translate((0, -17.5, 0))

# Barrel (cylinder along +X)
barrel = (cq.Workplane("YZ").workplane(offset=120)
          .center(0, 30).circle(10).extrude(130))
# Bore
bore = (cq.Workplane("YZ").workplane(offset=119)
        .center(0, 30).circle(4).extrude(132))
barrel = barrel.cut(bore)

# Cylinder (revolving chamber)
cyl = (cq.Workplane("YZ").workplane(offset=40)
       .center(0, 28).circle(20).extrude(40))
# Six chambers
for i in range(6):
    ang = i * 60
    cx = 13 * math.cos(math.radians(ang))
    cy = 28 + 13 * math.sin(math.radians(ang))
    chamber = (cq.Workplane("YZ").workplane(offset=38)
               .center(cx, cy).circle(3).extrude(42))
    cyl = cyl.cut(chamber)

# Grip (angled block)
grip_pts = [(-80, 0), (-20, 0), (-20, 50), (-60, 60), (-90, 30)]
grip = (cq.Workplane("XZ").polyline(grip_pts).close().extrude(30, both=False))
grip = grip.translate((0, -15, -60))

# Trigger guard
guard = (cq.Workplane("YZ").workplane(offset=-5)
         .center(0, 5).circle(15).circle(11).extrude(20))

body = frame.union(barrel).union(cyl).union(grip).union(guard)

try:
    body = body.edges("|Y").fillet(1.5)
except Exception:
    pass

result = body
'''
