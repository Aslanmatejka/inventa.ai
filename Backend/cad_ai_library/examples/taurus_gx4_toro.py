from ..core.metadata import ExampleMetadata

metadata = ExampleMetadata(
    id="taurus_gx4_toro",
    name="Taurus GX4 T.O.R.O.",
    category="firearm",
    keywords=[
        "taurus", "gx4", "toro", "micro", "nine", "9mm", "pistol",
        "double-stack", "compact", "optics ready", "concealed carry",
        "firearm", "handgun",
    ],
    description=(
        "Stylized prop model of the Taurus GX4 T.O.R.O. double-stack micro 9mm: "
        "grip frame, slide, barrel, and optics cut on top of the slide."
    ),
    techniques=["boolean_union", "boolean_cut", "guarded_fillet"],
    nominal_dimensions_mm={"length": 165.0, "height": 115.0, "thickness": 28.0},
    difficulty="medium",
)

code = '''import cadquery as cq

# Frame / grip (side profile in XZ)
frame_pts = [
    (-10, 0),      # grip toe
    (30, 0),       # grip heel
    (45, 70),      # trigger guard front bottom
    (95, 70),      # front of frame rail
    (105, 95),     # front beavertail area
    (-5, 95),      # rear beavertail
    (-15, 75),
    (-5, 30),
]
frame = (cq.Workplane("XZ").polyline(frame_pts).close()
         .extrude(28, both=False))
frame = frame.translate((0, -14, 0))

# Slide (sits on top of frame)
slide = (cq.Workplane("XY").workplane(offset=95)
         .center(50, 0).box(130, 26, 22, centered=(True, True, False)))
try:
    slide = slide.edges("|Y").fillet(3.0)
except Exception:
    pass

# Barrel tip peeking out front
barrel = (cq.Workplane("YZ").workplane(offset=120)
          .center(0, 106).circle(5).extrude(6))

# Optics cut (T.O.R.O. plate cut) on top of slide
optic = (cq.Workplane("XY").workplane(offset=112)
         .center(30, 0).rect(32, 18).extrude(6))
slide = slide.cut(optic)

# Ejection port (right side of slide)
port = (cq.Workplane("XZ").workplane(offset=-14)
        .center(70, 108).rect(35, 14).extrude(30))
slide = slide.cut(port)

# Trigger guard opening
guard = (cq.Workplane("YZ").workplane(offset=-2)
         .center(0, 55).circle(13).extrude(32))
frame = frame.cut(guard)

# Grip texturing dimples (simplified: two shallow rect pockets)
for z in [20, 45]:
    pocket = (cq.Workplane("YZ").workplane(offset=-15)
              .center(0, z).rect(10, 18).extrude(4))
    frame = frame.cut(pocket)
    pocket2 = (cq.Workplane("YZ").workplane(offset=11)
               .center(0, z).rect(10, 18).extrude(4))
    frame = frame.cut(pocket2)

body = frame.union(slide).union(barrel)

try:
    body = body.edges("|Y").fillet(1.5)
except Exception:
    pass

result = body
'''
