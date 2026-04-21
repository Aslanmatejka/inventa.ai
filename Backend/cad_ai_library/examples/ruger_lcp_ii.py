from ..core.metadata import ExampleMetadata

metadata = ExampleMetadata(
    id="ruger_lcp_ii",
    name="Ruger LCP II",
    category="firearm",
    keywords=[
        "ruger", "lcp", "lcp ii", "lcp 2", "22lr", ".22", "22 lr", "single-stack",
        "rimfire", "pocket", "pistol", "subcompact", "concealed carry",
        "firearm", "handgun",
    ],
    description=(
        "Stylized prop model of the Ruger LCP II single-stack .22 LR pocket pistol: "
        "ultra-slim polymer frame, short slide, and rimfire-scale barrel."
    ),
    techniques=["boolean_union", "boolean_cut", "guarded_fillet"],
    nominal_dimensions_mm={"length": 132.0, "height": 95.0, "thickness": 20.0},
    difficulty="medium",
)

code = '''import cadquery as cq

# Ultra-slim single-stack frame profile
frame_pts = [
    (-6, 0),
    (20, 0),
    (32, 52),       # trigger guard front
    (74, 52),
    (84, 70),
    (-2, 70),
    (-10, 52),
    (-4, 22),
]
frame = (cq.Workplane("XZ").polyline(frame_pts).close()
         .extrude(20, both=False))
frame = frame.translate((0, -10, 0))

# Short slim slide
slide = (cq.Workplane("XY").workplane(offset=70)
         .center(40, 0).box(100, 18, 18, centered=(True, True, False)))
try:
    slide = slide.edges("|Y").fillet(2.5)
except Exception:
    pass

# Front cocking serrations (distinctive on LCP II)
for i in range(4):
    x = 70 + i * 4
    for y_off in [-9, 9]:
        serr = (cq.Workplane("XZ").workplane(offset=y_off)
                .center(x, 79).rect(1.5, 10).extrude(2))
        slide = slide.cut(serr)

# Rear cocking serrations
for i in range(4):
    x = 0 + i * 4
    for y_off in [-9, 9]:
        serr = (cq.Workplane("XZ").workplane(offset=y_off)
                .center(x, 79).rect(1.5, 10).extrude(2))
        slide = slide.cut(serr)

# Ejection port
port = (cq.Workplane("XZ").workplane(offset=-10)
        .center(50, 81).rect(22, 10).extrude(22))
slide = slide.cut(port)

# Rimfire barrel tip (smaller)
barrel = (cq.Workplane("YZ").workplane(offset=90)
          .center(0, 80).circle(3.2).extrude(4))

# Trigger guard opening
guard = (cq.Workplane("YZ").workplane(offset=-2)
         .center(0, 42).circle(10).extrude(24))
frame = frame.cut(guard)

# Slim grip checkering panels
for y_off in [-11, 8]:
    panel = (cq.Workplane("YZ").workplane(offset=y_off)
             .center(0, 18).rect(16, 30).extrude(2.5))
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
