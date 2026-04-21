from ..core.metadata import ExampleMetadata

metadata = ExampleMetadata(
    id="tape_dispenser",
    name="Tape Dispenser",
    category="stationery",
    keywords=["tape", "dispenser", "office", "stationery", "desk", "adhesive"],
    description="Weighted desktop tape dispenser with tape spindle and serrated cutter lip.",
    techniques=["polyline_profile", "guarded_fillet"],
    nominal_dimensions_mm={"length": 150.0, "width": 55.0, "height": 80.0, "spindle_diameter": 26.0},
    difficulty="medium",
)

code = '''import cadquery as cq

length = 150.0
width = 55.0
height = 80.0
spindle_d = 26.0

# Side profile (teardrop-ish) in XZ
profile = (
    cq.Workplane("XZ")
    .moveTo(-length / 2.0, 0)
    .lineTo(length / 2.0, 0)
    .lineTo(length / 2.0 - 10, height * 0.45)
    .threePointArc((length / 2.0 - 35, height), (-length / 2.0 + 10, height * 0.5))
    .close()
)
body = profile.extrude(width).translate((0, -width / 2.0, 0))

try:
    body = body.edges("|Y").fillet(4.0)
except Exception:
    pass

# Tape spindle (pin sticking out one side)
spindle_pos = (-length * 0.1, -width / 2.0 - 4, height * 0.55)
spindle = (
    cq.Workplane("XZ", origin=spindle_pos)
    .circle(spindle_d / 2.0)
    .extrude(width + 8)
)
body = body.union(spindle)

# Hollow out the spindle core slightly so the tape roll can sit
core = (
    cq.Workplane("XZ", origin=(-length * 0.1, -width / 2.0 - 5, height * 0.55))
    .circle(spindle_d / 2.0 - 4)
    .extrude(width + 10)
)
body = body.cut(core)

# Cutter lip: a small triangular plate at the right end
cutter = (
    cq.Workplane("YZ", origin=(length / 2.0 - 6, 0, 6))
    .moveTo(-width / 2.0, 0)
    .lineTo(width / 2.0, 0)
    .lineTo(0, 6)
    .close()
    .extrude(4)
)
body = body.union(cutter)

result = body
'''
