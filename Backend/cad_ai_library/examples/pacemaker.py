from ..core.metadata import ExampleMetadata

metadata = ExampleMetadata(
    id="pacemaker",
    name="Cardiac Pacemaker",
    category="prosthetic",
    keywords=["pacemaker", "cardiac", "icd", "implantable", "heart", "medical implant", "pulse generator", "prosthetic", "cardiology"],
    description="Implantable pulse generator (pacemaker): rounded titanium can with header block and lead ports.",
    techniques=["boolean_union", "guarded_fillet"],
    nominal_dimensions_mm={"width": 45.0, "height": 45.0, "thickness": 7.5},
    difficulty="easy",
)

code = '''import cadquery as cq

W = 45.0
H = 45.0
T = 7.5

# Can body (rounded rectangle)
can = cq.Workplane("XY").box(W, H, T, centered=(True, True, False))
try:
    can = can.edges("|Z").fillet(8.0)
except Exception:
    pass
try:
    can = can.edges(">Z or <Z").fillet(2.5)
except Exception:
    pass

# Header block (epoxy connector header on top)
header = (cq.Workplane("XY").workplane(offset=T)
          .center(0, H/2 - 6).box(W - 8, 12, 8, centered=(True, True, False)))
try:
    header = header.edges("|Y").fillet(3.0)
except Exception:
    pass

body = can.union(header)

# Lead ports (two bores into header)
for x_off in [-8, 8]:
    port = (cq.Workplane("XZ").workplane(offset=(H/2 - 6) + 6)
            .center(x_off, T + 4).circle(2).extrude(10))
    body = body.cut(port)

# Setscrew access holes on top of header
for x_off in [-8, 8]:
    scr = (cq.Workplane("XY").workplane(offset=T + 8 - 1)
           .center(x_off, H/2 - 6).circle(1.2).extrude(2))
    body = body.cut(scr)

# Suture loop (small tab at bottom)
suture_tab = (cq.Workplane("XY").workplane(offset=(T - 1.5) / 2)
              .center(0, -H/2 - 5).circle(4).extrude(1.5))
suture_hole = (cq.Workplane("XY").workplane(offset=0)
               .center(0, -H/2 - 5).circle(1.5).extrude(T))
body = body.union(suture_tab).cut(suture_hole)

# Laser-engraved model text indicator (small rectangular recess)
label = (cq.Workplane("XY").workplane(offset=T - 0.3)
         .center(0, -8).rect(18, 6).extrude(0.4))
body = body.cut(label)

result = body
'''
