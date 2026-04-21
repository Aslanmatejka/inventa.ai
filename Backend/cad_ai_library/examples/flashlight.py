from ..core.metadata import ExampleMetadata

metadata = ExampleMetadata(
    id="flashlight",
    name="Flashlight Body",
    category="electronics",
    keywords=["flashlight", "torch", "light", "battery", "led", "tube"],
    description="Flashlight housing with knurled grip, lens bezel, and battery cavity.",
    techniques=["safe_revolve", "polar_array", "shell_cavity"],
    nominal_dimensions_mm={"body_length": 120.0, "body_diameter": 22.0, "head_diameter": 32.0},
    difficulty="medium",
)

code = '''import cadquery as cq

body_l = 120.0
body_d = 22.0
head_l = 25.0
head_d = 32.0
tail_d = 24.0
tail_l = 10.0
wall = 2.0

# Revolve a tri-part profile: tail | body | head
r_body = body_d / 2.0
r_head = head_d / 2.0
r_tail = tail_d / 2.0

profile = (
    cq.Workplane("XZ")
    .moveTo(0, 0)
    .lineTo(r_tail, 0)
    .lineTo(r_tail, tail_l)
    .lineTo(r_body, tail_l + 2)
    .lineTo(r_body, tail_l + body_l)
    .lineTo(r_head, tail_l + body_l + 2)
    .lineTo(r_head, tail_l + body_l + head_l)
    .lineTo(0, tail_l + body_l + head_l)
    .close()
)
body = profile.revolve(360)

# Knurl flutes on the body
flute_count = 16
for i in range(flute_count):
    theta = 360.0 / flute_count * i
    cutter = (
        cq.Workplane("XY", origin=(r_body - 0.2, 0, tail_l + 10))
        .circle(0.8)
        .extrude(body_l - 20)
        .rotate((0, 0, 0), (0, 0, 1), theta)
    )
    body = body.cut(cutter)

# Battery cavity from the tail
cavity = (
    cq.Workplane("XY", origin=(0, 0, wall))
    .circle(r_body - wall)
    .extrude(tail_l + body_l - wall)
)
body = body.cut(cavity)

# Lens aperture
lens = (
    cq.Workplane("XY", origin=(0, 0, tail_l + body_l + head_l - 4))
    .circle(r_head - 4)
    .extrude(5)
)
body = body.cut(lens)

result = body
'''
