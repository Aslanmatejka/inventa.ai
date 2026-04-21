from ..core.metadata import ExampleMetadata

metadata = ExampleMetadata(
    id="transradial_socket",
    name="Transradial Socket",
    category="prosthetic",
    keywords=["transradial", "socket", "below elbow", "residual limb", "prosthetic socket", "laminated socket", "trim line", "prosthesis"],
    description="Transradial (below-elbow) prosthetic socket: laminated shell with flexible inner liner opening and wrist coupler threads.",
    techniques=["revolve", "shell", "boolean_cut"],
    nominal_dimensions_mm={"length": 180.0, "proximal_dia": 95.0, "distal_dia": 55.0},
    difficulty="medium",
)

code = '''import cadquery as cq

# Outer shell (tapered oval approximated by revolve)
outer_pts = [
    (0, 0),
    (27.5, 0),
    (30, 10),
    (35, 60),
    (40, 120),
    (45, 170),
    (45, 180),
    (0, 180),
]
outer = cq.Workplane("XZ").polyline(outer_pts).close().revolve(360, (0, 0, 0), (0, 1, 0))

# Inner cavity
inner_pts = [
    (0, 4),
    (25, 4),
    (28, 12),
    (33, 60),
    (38, 120),
    (42, 170),
    (0, 170),
]
inner = cq.Workplane("XZ").polyline(inner_pts).close().revolve(360, (0, 0, 0), (0, 1, 0))
shell = outer.cut(inner)

# Proximal trim line: cut an angled lip on the top (opening where arm enters)
trim = (cq.Workplane("XZ").workplane(offset=0)
        .center(0, 170).box(100, 25, 100, centered=(True, True, False)))
trim = trim.rotate((0, 0, 170), (1, 0, 0), -18)
shell = shell.cut(trim)

body = shell

# Anterior window (cutout for pronation/supination relief)
window = (cq.Workplane("XZ").workplane(offset=40)
          .center(0, 90).rect(30, 50).extrude(15))
body = body.cut(window)

# Wrist coupler threads at distal end (stacked rings look)
for z in [2, 8, 14]:
    ring = (cq.Workplane("XY").workplane(offset=z)
            .circle(29).circle(27).extrude(2))
    body = body.union(ring)

# Distal attachment bore
bore = cq.Workplane("XY").circle(15).extrude(20)
body = body.cut(bore)

result = body
'''
