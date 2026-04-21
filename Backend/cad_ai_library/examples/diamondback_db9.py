from ..core.metadata import ExampleMetadata

metadata = ExampleMetadata(
    id="diamondback_db9",
    name="Diamondback DB9",
    category="firearm",
    keywords=[
        "diamondback", "db9", "single-stack", "9mm", "pocket", "pistol",
        "slim", "subcompact", "concealed carry", "firearm", "handgun",
    ],
    description=(
        "Stylized prop model of the Diamondback DB9 single-stack 9mm pocket pistol: "
        "slim polymer frame, slide with serrations, and short barrel."
    ),
    techniques=["boolean_union", "boolean_cut", "guarded_fillet"],
    nominal_dimensions_mm={"length": 145.0, "height": 105.0, "thickness": 22.0},
    difficulty="medium",
)

code = '''import cadquery as cq

# Slim frame profile (single-stack -> thinner than GX4)
frame_pts = [
    (-8, 0),
    (22, 0),
    (35, 60),      # trigger guard front
    (80, 60),
    (90, 80),
    (-5, 80),
    (-12, 60),
    (-5, 25),
]
frame = (cq.Workplane("XZ").polyline(frame_pts).close()
         .extrude(22, both=False))
frame = frame.translate((0, -11, 0))

# Slide on top
slide = (cq.Workplane("XY").workplane(offset=80)
         .center(42, 0).box(115, 20, 20, centered=(True, True, False)))
try:
    slide = slide.edges("|Y").fillet(2.5)
except Exception:
    pass

# Rear cocking serrations (3 slots on each side of slide)
for i in range(3):
    x = 85 + i * 6
    for y_off in [-10, 10]:
        serr = (cq.Workplane("XZ").workplane(offset=y_off)
                .center(x, 92).rect(2, 12).extrude(2))
        slide = slide.cut(serr)

# Ejection port
port = (cq.Workplane("XZ").workplane(offset=-11)
        .center(55, 92).rect(28, 12).extrude(24))
slide = slide.cut(port)

# Short barrel tip
barrel = (cq.Workplane("YZ").workplane(offset=100)
          .center(0, 90).circle(4.5).extrude(5))

# Trigger guard opening
guard = (cq.Workplane("YZ").workplane(offset=-2)
         .center(0, 48).circle(11).extrude(26))
frame = frame.cut(guard)

# Slim grip side panels
for y_off in [-12, 9]:
    panel = (cq.Workplane("YZ").workplane(offset=y_off)
             .center(0, 20).rect(18, 35).extrude(3))
    frame = frame.cut(panel)

body = frame.union(slide).union(barrel)

try:
    body = body.edges("|Y").fillet(1.2)
except Exception:
    pass

result = body

# --- Modern finishing pass (guarded) ---
try:
    result = result.edges("|Z").fillet(1.2)
except Exception:
    pass
try:
    result = result.faces(">Z").edges().chamfer(0.5)
except Exception:
    pass
try:
    result = result.faces("<Z").edges().fillet(0.8)
except Exception:
    pass
'''
