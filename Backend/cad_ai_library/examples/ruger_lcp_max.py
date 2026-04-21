from ..core.metadata import ExampleMetadata

metadata = ExampleMetadata(
    id="ruger_lcp_max",
    name="Ruger LCP Max",
    category="firearm",
    keywords=[
        "ruger", "lcp", "lcp max", "380", ".380", "380 acp", "double-stack",
        "pocket", "pistol", "subcompact", "concealed carry", "firearm", "handgun",
    ],
    description=(
        "Stylized prop model of the Ruger LCP Max double-stack .380 ACP pocket pistol: "
        "tiny polymer frame, stubby slide, and vestigial sights."
    ),
    techniques=["boolean_union", "boolean_cut", "guarded_fillet"],
    nominal_dimensions_mm={"length": 135.0, "height": 100.0, "thickness": 26.0},
    difficulty="medium",
)

code = '''import cadquery as cq

# Compact double-stack frame profile
frame_pts = [
    (-6, 0),
    (24, 0),
    (38, 55),       # trigger guard front
    (78, 55),
    (88, 75),
    (-2, 75),
    (-10, 55),
    (-4, 25),
]
frame = (cq.Workplane("XZ").polyline(frame_pts).close()
         .extrude(26, both=False))
frame = frame.translate((0, -13, 0))

# Short slide
slide = (cq.Workplane("XY").workplane(offset=75)
         .center(42, 0).box(105, 24, 20, centered=(True, True, False)))
try:
    slide = slide.edges("|Y").fillet(3.0)
except Exception:
    pass

# Front sight
fsight = (cq.Workplane("XY").workplane(offset=95)
          .center(85, 0).box(5, 4, 4, centered=(True, True, False)))
# Rear sight
rsight = (cq.Workplane("XY").workplane(offset=95)
          .center(0, 0).box(10, 6, 5, centered=(True, True, False)))
slide = slide.union(fsight).union(rsight)

# Ejection port
port = (cq.Workplane("XZ").workplane(offset=-13)
        .center(55, 87).rect(26, 12).extrude(28))
slide = slide.cut(port)

# Barrel tip
barrel = (cq.Workplane("YZ").workplane(offset=94)
          .center(0, 85).circle(4).extrude(4))

# Trigger guard opening
guard = (cq.Workplane("YZ").workplane(offset=-2)
         .center(0, 45).circle(10).extrude(30))
frame = frame.cut(guard)

# Texturing dimples on grip
for z in [15, 35]:
    for y_off in [-14, 11]:
        dot = (cq.Workplane("YZ").workplane(offset=y_off)
               .center(0, z).rect(8, 12).extrude(3))
        frame = frame.cut(dot)

body = frame.union(slide).union(barrel)

try:
    body = body.edges("|Y").fillet(1.5)
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
