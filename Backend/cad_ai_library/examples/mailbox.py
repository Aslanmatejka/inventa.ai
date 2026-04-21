from ..core.metadata import ExampleMetadata

metadata = ExampleMetadata(
    id="mailbox",
    name="Curbside Mailbox",
    category="outdoor",
    keywords=["mailbox", "mail", "post", "letters", "curbside", "tunnel"],
    description="Classic tunnel-style curbside mailbox with flag and rear door.",
    techniques=["polyline_profile", "guarded_fillet"],
    nominal_dimensions_mm={"length": 480.0, "width": 180.0, "height": 220.0},
    difficulty="medium",
)

code = '''import cadquery as cq

length = 480.0
width = 180.0
height = 220.0
wall = 2.5

# Tunnel cross-section in YZ: flat bottom, rounded top via three-point arc
profile = (
    cq.Workplane("YZ")
    .moveTo(-width / 2.0, 0)
    .lineTo(width / 2.0, 0)
    .lineTo(width / 2.0, height * 0.45)
    .threePointArc((0, height), (-width / 2.0, height * 0.45))
    .close()
)
outer = profile.extrude(length).translate((-length / 2.0, 0, 0))

# Hollow interior
inner_profile = (
    cq.Workplane("YZ")
    .moveTo(-width / 2.0 + wall, wall)
    .lineTo(width / 2.0 - wall, wall)
    .lineTo(width / 2.0 - wall, height * 0.45)
    .threePointArc((0, height - wall), (-width / 2.0 + wall, height * 0.45))
    .close()
)
inner = inner_profile.extrude(length - 2 * wall).translate((-length / 2.0 + wall, 0, 0))
body = outer.cut(inner)

# Front opening (partial door) on -X face
front_open = (
    cq.Workplane("YZ", origin=(-length / 2.0 - 1, 0, height * 0.5))
    .rect(width - 2 * wall - 4, height * 0.6)
    .extrude(wall + 2)
)
body = body.cut(front_open)

# Flag on the right side (a thin rectangular plate on a small post)
flag_post = (
    cq.Workplane("XY", origin=(-length * 0.15, width / 2.0 - 2, height * 0.35))
    .box(4, 4, 80, centered=(True, True, False))
)
flag = (
    cq.Workplane("XZ", origin=(-length * 0.15, width / 2.0 + 2, height * 0.35 + 50))
    .rect(45, 25)
    .extrude(2)
    .translate((0, -1, 0))
)
body = body.union(flag_post).union(flag)

result = body
'''
