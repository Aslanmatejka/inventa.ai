from ..core.metadata import ExampleMetadata

metadata = ExampleMetadata(
    id="rubber_duck",
    name="Rubber Duck",
    category="toy",
    keywords=["rubber", "duck", "bath", "toy", "yellow", "ducky"],
    description="Stylized rubber bath duck: body, head, tail fin, and beak from simple primitives.",
    techniques=["sphere_union"],
    nominal_dimensions_mm={"length": 90.0, "height": 90.0, "width": 60.0},
    difficulty="easy",
)

code = '''import cadquery as cq

# Body (sphere, stretched along +X by unioning a cylinder and a tail sphere)
body_r = 28.0
body = cq.Workplane("XY", origin=(0, 0, body_r)).sphere(body_r)
stretch = (
    cq.Workplane("YZ", origin=(-25, 0, body_r))
    .circle(body_r * 0.95)
    .extrude(40)
)
body = body.union(stretch)
tail_cap = cq.Workplane("XY", origin=(-25, 0, body_r)).sphere(body_r * 0.9)
body = body.union(tail_cap)

# Head
head = cq.Workplane("XY", origin=(25, 0, body_r * 1.6)).sphere(body_r * 0.7)
body = body.union(head)

# Beak (small box on +X side of head)
beak = (
    cq.Workplane("XY", origin=(25 + body_r * 0.55, 0, body_r * 1.55))
    .box(12, 10, 5, centered=(False, True, False))
)
try:
    beak = beak.edges("|Y").fillet(1.5)
except Exception:
    pass
body = body.union(beak)

# Tail fin (wedge)
tail = (
    cq.Workplane("XZ", origin=(-35, 0, body_r * 1.1))
    .moveTo(0, 0)
    .lineTo(-15, 10)
    .lineTo(0, 15)
    .close()
    .extrude(6)
    .translate((0, -3, 0))
)
body = body.union(tail)

# Two small eye sockets on head
for sy in (-body_r * 0.25, body_r * 0.25):
    eye = (
        cq.Workplane("YZ", origin=(25 + body_r * 0.4, sy, body_r * 1.75))
        .circle(2.0)
        .extrude(-3)
    )
    body = body.cut(eye)

result = body
'''
