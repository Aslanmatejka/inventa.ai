from ..core.metadata import ExampleMetadata

metadata = ExampleMetadata(
    id="watering_can",
    name="Watering Can",
    category="outdoor",
    keywords=["watering", "can", "garden", "plant", "spout", "outdoor"],
    description="Watering can with tapered body, long spout, and top loop handle.",
    techniques=["safe_revolve", "shell_cavity"],
    nominal_dimensions_mm={"body_diameter": 140.0, "body_height": 140.0, "spout_length": 180.0},
    difficulty="advanced",
)

code = '''import cadquery as cq

body_d = 140.0
body_h = 140.0
wall = 2.5
spout_d = 22.0
spout_l = 180.0

r = body_d / 2.0

# Tapered body (revolve)
profile = (
    cq.Workplane("XZ")
    .moveTo(0, 0)
    .lineTo(r * 0.9, 0)
    .lineTo(r, body_h * 0.2)
    .lineTo(r, body_h * 0.8)
    .lineTo(r * 0.85, body_h)
    .lineTo(0, body_h)
    .close()
)
body = profile.revolve(360)
body = body.faces(">Z").shell(-wall)

# Spout coming out of the side, angled up
spout_origin = (r * 0.9, 0, body_h * 0.35)
spout = (
    cq.Workplane("YZ", origin=spout_origin)
    .circle(spout_d / 2.0)
    .workplane(offset=spout_l)
    .center(0, spout_l * 0.3)
    .circle(spout_d * 0.45)
    .loft(combine=True)
)
spout_bore = (
    cq.Workplane("YZ", origin=spout_origin)
    .circle(spout_d / 2.0 - wall)
    .workplane(offset=spout_l)
    .center(0, spout_l * 0.3)
    .circle(spout_d * 0.45 - wall)
    .loft(combine=True)
)
spout = spout.cut(spout_bore)
body = body.union(spout)

# Top loop handle
handle_outer = (
    cq.Workplane("XZ", origin=(0, 0, body_h + 25))
    .ellipse(r * 0.85, 28)
    .extrude(10)
    .translate((0, -5, 0))
)
handle_inner = (
    cq.Workplane("XZ", origin=(0, 0, body_h + 25))
    .ellipse(r * 0.7, 18)
    .extrude(11)
    .translate((0, -5, 0))
)
handle = handle_outer.cut(handle_inner)
body = body.union(handle)

result = body
'''
