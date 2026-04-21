from ..core.metadata import ExampleMetadata

metadata = ExampleMetadata(
    id="screwdriver",
    name="Phillips Screwdriver",
    category="tool",
    keywords=["screwdriver", "phillips", "driver", "tool", "handle", "shaft"],
    description="Screwdriver with ergonomic revolved grip, steel shaft, and Phillips tip.",
    techniques=["revolve", "boolean_union"],
    nominal_dimensions_mm={"length": 200.0, "handle_dia": 32.0, "shaft_dia": 6.0},
    difficulty="medium",
)

code = '''import cadquery as cq

handle_len = 90.0
handle_r = 16.0
shaft_len = 110.0
shaft_r = 3.0

# Revolve handle profile (ergonomic bulge)
handle_pts = [
    (0, 0), (handle_r * 0.6, 0), (handle_r, handle_len * 0.25),
    (handle_r, handle_len * 0.75), (handle_r * 0.7, handle_len),
    (0, handle_len),
]
handle = cq.Workplane("XZ").polyline(handle_pts).close().revolve(360, (0, 0, 0), (0, 1, 0))

# Shaft
shaft = (cq.Workplane("XY").workplane(offset=handle_len)
         .circle(shaft_r).extrude(shaft_len))

# Phillips tip (tapered + cross cuts)
tip = (cq.Workplane("XY").workplane(offset=handle_len + shaft_len)
       .circle(shaft_r).workplane(offset=6).circle(0.5).loft(combine=False))

body = handle.union(shaft).union(tip)

# Phillips cross cut
cut1 = (cq.Workplane("XY").workplane(offset=handle_len + shaft_len)
        .rect(shaft_r * 2.2, 0.8).extrude(8))
cut2 = (cq.Workplane("XY").workplane(offset=handle_len + shaft_len)
        .rect(0.8, shaft_r * 2.2).extrude(8))
body = body.cut(cut1).cut(cut2)

result = body
'''
