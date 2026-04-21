from ..core.metadata import ExampleMetadata

metadata = ExampleMetadata(
    id="glock_17",
    name="Glock 17",
    category="firearm",
    keywords=["glock", "glock 17", "g17", "full-size", "9mm", "duty pistol", "striker-fired", "firearm", "handgun", "pistol"],
    description="Stylized prop of the Glock 17: full-size 9mm duty pistol with accessory rail.",
    techniques=["boolean_union", "boolean_cut", "guarded_fillet"],
    nominal_dimensions_mm={"length": 202.0, "height": 139.0, "width": 32.5},
    difficulty="medium",
)

code = '''import cadquery as cq

# ---- Glock 17 parameters ----
SLIDE_LEN = 186.0
SLIDE_H = 24.0
GRIP_H = 139.0
THK = 30.0
BORE = 9.0
HAS_RAIL = True
HAS_FRONT_SERR = False
# -----------------------------

frame_pts = [
    (-6, 0), (26, 0),
    (42, GRIP_H * 0.55),
    (SLIDE_LEN * 0.55, GRIP_H * 0.55),
    (SLIDE_LEN * 0.55, GRIP_H),
    (-4, GRIP_H),
    (-12, GRIP_H * 0.6),
    (-4, GRIP_H * 0.25),
]
frame = cq.Workplane("XZ").polyline(frame_pts).close().extrude(THK, both=False).translate((0, -THK / 2, 0))

slide = (cq.Workplane("XY").workplane(offset=GRIP_H)
         .center(SLIDE_LEN / 2 - 10, 0)
         .box(SLIDE_LEN, THK - 2, SLIDE_H, centered=(True, True, False)))
try:
    slide = slide.edges("|Y").fillet(2.5)
except Exception:
    pass

for i in range(4):
    x = 0 + i * 5
    for y_off in [-(THK / 2) + 0.5, (THK / 2) - 2.5]:
        serr = (cq.Workplane("XZ").workplane(offset=y_off)
                .center(x, GRIP_H + SLIDE_H * 0.55).rect(1.5, SLIDE_H * 0.55).extrude(2))
        slide = slide.cut(serr)

if HAS_FRONT_SERR:
    for i in range(3):
        x = SLIDE_LEN - 25 + i * 4
        for y_off in [-(THK / 2) + 0.5, (THK / 2) - 2.5]:
            serr = (cq.Workplane("XZ").workplane(offset=y_off)
                    .center(x, GRIP_H + SLIDE_H * 0.55).rect(1.5, SLIDE_H * 0.5).extrude(2))
            slide = slide.cut(serr)

port = (cq.Workplane("XZ").workplane(offset=-(THK / 2) - 1)
        .center(SLIDE_LEN * 0.55, GRIP_H + SLIDE_H * 0.6)
        .rect(SLIDE_LEN * 0.22, SLIDE_H * 0.5).extrude(THK + 2))
slide = slide.cut(port)

fsight = cq.Workplane("XY").workplane(offset=GRIP_H + SLIDE_H).center(SLIDE_LEN - 15, 0).box(4, 3.5, 3.5, centered=(True, True, False))
rs = cq.Workplane("XY").workplane(offset=GRIP_H + SLIDE_H).center(6, 0).box(10, THK - 4, 4.5, centered=(True, True, False))
rsn = cq.Workplane("XY").workplane(offset=GRIP_H + SLIDE_H + 1).center(6, 0).box(3, 3, 4, centered=(True, True, False))
slide = slide.union(fsight).union(rs.cut(rsn))

barrel = (cq.Workplane("YZ").workplane(offset=SLIDE_LEN - 10)
          .center(0, GRIP_H + SLIDE_H * 0.5)
          .circle(BORE / 2 + 2).circle(BORE / 2).extrude(4))

guard = cq.Workplane("YZ").workplane(offset=-2).center(0, GRIP_H * 0.42).circle(11).extrude(THK + 4)
frame = frame.cut(guard)

if HAS_RAIL:
    rail = (cq.Workplane("XZ").workplane(offset=-(THK / 2) - 1)
            .center(SLIDE_LEN * 0.5, GRIP_H * 0.62).rect(SLIDE_LEN * 0.18, 5).extrude(THK + 2))
    frame = frame.cut(rail)

for zf in (0.15, 0.28, 0.42):
    z = GRIP_H * zf
    for y_off in (-(THK / 2) + 0.8, (THK / 2) - 3.8):
        d = cq.Workplane("YZ").workplane(offset=y_off).center(0, z).rect(10, GRIP_H * 0.08).extrude(3)
        frame = frame.cut(d)

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
