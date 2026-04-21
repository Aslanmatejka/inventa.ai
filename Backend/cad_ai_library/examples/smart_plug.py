from ..core.metadata import ExampleMetadata

metadata = ExampleMetadata(
    id="smart_plug",
    name="Smart Plug",
    category="electronics",
    keywords=["smart", "plug", "outlet", "wifi", "smart plug", "socket"],
    description="WiFi smart plug with rounded housing, front socket, and side button.",
    techniques=["guarded_fillet", "boolean_cut"],
    nominal_dimensions_mm={"width": 55.0, "height": 55.0, "depth": 60.0},
    difficulty="easy",
)

code = '''import cadquery as cq

w = 55.0
h = 55.0
d = 60.0

body = cq.Workplane("XY").box(w, d, h, centered=(True, True, False))
try:
    body = body.edges().fillet(6.0)
except Exception:
    pass

# Front socket face (two slots + ground)
front_z = h - 2
slot_l = (cq.Workplane("XY").workplane(offset=front_z)
          .center(-8, 6).rect(2, 10).extrude(3))
slot_r = (cq.Workplane("XY").workplane(offset=front_z)
          .center(8, 6).rect(2, 10).extrude(3))
gnd = (cq.Workplane("XY").workplane(offset=front_z)
       .center(0, -8).circle(3).extrude(3))
body = body.cut(slot_l).cut(slot_r).cut(gnd)

# Side button
btn = (cq.Workplane("YZ").workplane(offset=w/2)
       .center(0, h/2).circle(5).extrude(3))
body = body.union(btn)

# Back prongs
for x in [-6, 6]:
    prong = (cq.Workplane("XY").workplane(offset=-8)
             .center(x, 0).rect(6, 1.5).extrude(8))
    body = body.union(prong)

result = body
'''
