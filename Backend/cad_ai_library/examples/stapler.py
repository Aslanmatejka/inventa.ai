from ..core.metadata import ExampleMetadata

metadata = ExampleMetadata(
    id="stapler",
    name="Desktop Stapler",
    category="stationery",
    keywords=["stapler", "office", "stationery", "staples", "desk"],
    description="Desktop stapler base with anvil plate and upper arm.",
    techniques=["polyline_profile", "guarded_fillet"],
    nominal_dimensions_mm={"length": 170.0, "width": 45.0, "height": 55.0},
    difficulty="medium",
)

code = '''import cadquery as cq

length = 170.0
width = 45.0
base_h = 16.0
arm_h = 24.0
pivot_x = -length / 2.0 + 15

# Base
base = cq.Workplane("XY").box(length, width, base_h, centered=(True, True, False))
try:
    base = base.edges("|Z").fillet(6.0)
except Exception:
    pass

# Anvil slot on top of base
anvil = (
    cq.Workplane("XY", origin=(length * 0.15, 0, base_h - 1.2))
    .box(length * 0.35, width * 0.5, 1.5, centered=(True, True, False))
)
base = base.cut(anvil)

# Arm (profile in XZ, extruded along Y)
arm_profile = (
    cq.Workplane("XZ")
    .moveTo(pivot_x, base_h + 2)
    .lineTo(length / 2.0 - 8, base_h + 4)
    .threePointArc((length / 2.0 - 4, base_h + 4 + arm_h * 0.3),
                   (length / 2.0 - 8, base_h + arm_h))
    .lineTo(pivot_x, base_h + arm_h)
    .close()
)
arm = arm_profile.extrude(width * 0.7).translate((0, -width * 0.35, 0))
try:
    arm = arm.edges("|Y").fillet(3.0)
except Exception:
    pass

body = base.union(arm)

result = body
'''
