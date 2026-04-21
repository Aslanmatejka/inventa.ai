from ..core.metadata import ExampleMetadata

metadata = ExampleMetadata(
    id="prosthetic_leg",
    name="Prosthetic Leg Pylon",
    category="prosthetic",
    keywords=["prosthetic", "leg", "limb", "pylon", "amputee", "prosthesis", "artificial leg"],
    description="Transtibial prosthesis: socket, tubular pylon, and foot plate.",
    techniques=["revolve", "boolean_union"],
    nominal_dimensions_mm={"total_height": 450.0, "socket_dia": 110.0, "foot_length": 240.0},
    difficulty="medium",
)

code = '''import cadquery as cq

# Socket: revolved tapered cup (wider at top)
socket_pts = [
    (0, 0), (45, 0), (55, 30), (55, 120), (50, 150), (0, 150),
]
socket = cq.Workplane("XZ").polyline(socket_pts).close().revolve(360, (0, 0, 0), (0, 1, 0))
# Hollow socket interior
socket_inner = [
    (0, 6), (38, 6), (48, 30), (48, 150), (0, 150),
]
inner = cq.Workplane("XZ").polyline(socket_inner).close().revolve(360, (0, 0, 0), (0, 1, 0))
socket = socket.cut(inner)

# Pylon tube
pylon = (cq.Workplane("XY").workplane(offset=-260)
         .circle(15).circle(11).extrude(260))

# Foot plate
foot = (cq.Workplane("XY").workplane(offset=-270)
        .center(40, 0).box(240, 95, 18, centered=(True, True, False)))
try:
    foot = foot.edges("|Z").fillet(15.0)
except Exception:
    pass

# Ankle coupler
ankle = (cq.Workplane("XY").workplane(offset=-262)
         .circle(22).extrude(10))

body = socket.union(pylon).union(ankle).union(foot)

try:
    body = body.edges(">Z").fillet(3.0)
except Exception:
    pass

result = body
'''
