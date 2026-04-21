from ..core.metadata import ExampleMetadata

metadata = ExampleMetadata(
    id="myoelectric_forearm",
    name="Myoelectric Forearm Shell",
    category="prosthetic",
    keywords=["prosthetic", "forearm", "myoelectric", "bionic arm", "arm shell", "transradial", "prosthesis"],
    description="Transradial myoelectric forearm shell: tapered tube with electrode recesses and wrist coupler.",
    techniques=["revolve", "boolean_cut"],
    nominal_dimensions_mm={"length": 240.0, "proximal_dia": 95.0, "distal_dia": 60.0},
    difficulty="medium",
)

code = '''import cadquery as cq

# Tapered outer profile (revolved)
outer_pts = [
    (0, 0),
    (47.5, 0),       # elbow end rim
    (47.5, 15),
    (40, 50),        # proximal fat
    (32, 180),       # taper toward wrist
    (30, 230),
    (30, 240),
    (0, 240),
]
outer = cq.Workplane("XZ").polyline(outer_pts).close().revolve(360, (0, 0, 0), (0, 1, 0))

# Inner cavity
inner_pts = [
    (0, 3),
    (45, 3),
    (45, 15),
    (38, 50),
    (30, 180),
    (28, 230),
    (0, 230),
]
inner = cq.Workplane("XZ").polyline(inner_pts).close().revolve(360, (0, 0, 0), (0, 1, 0))
body = outer.cut(inner)

# Two electrode window recesses (one front, one back)
for y_sign in (1, -1):
    window = (cq.Workplane("XZ").workplane(offset=y_sign * 35)
              .center(0, 80).rect(28, 42).extrude(6))
    body = body.cut(window)

# Wrist coupler ring at distal end
ring = (cq.Workplane("XY").workplane(offset=240)
        .circle(25).circle(20).extrude(8))
body = body.union(ring)

# Cable/battery pass-through slot on back
pass_slot = (cq.Workplane("XZ").workplane(offset=-40)
             .center(0, 200).rect(14, 30).extrude(20))
body = body.cut(pass_slot)

result = body
'''
