from ..core.metadata import ExampleMetadata

metadata = ExampleMetadata(
    id="snow_shovel_head",
    name="Snow Shovel Head",
    category="winter",
    keywords=["snow", "shovel", "winter", "tool", "scoop", "plow"],
    description="Snow shovel scoop head with curved lip and socket stub for the handle.",
    techniques=["polyline_profile"],
    nominal_dimensions_mm={"width": 500.0, "depth": 320.0, "lip_height": 120.0, "socket_diameter": 32.0},
    difficulty="medium",
)

code = '''import cadquery as cq

width = 500.0
depth = 320.0
lip_h = 120.0
wall = 4.0
socket_d = 32.0

# Side profile (YZ): scoop with back wall rising to lip — simple polyline
profile = (
    cq.Workplane("YZ")
    .moveTo(0, 0)
    .lineTo(depth, 0)
    .lineTo(depth, lip_h)
    .lineTo(depth - wall, lip_h)
    .lineTo(depth - wall, wall)
    .lineTo(0, wall)
    .close()
)
body = profile.extrude(width).translate((-width / 2.0, 0, 0))

# Two side walls
for sx in (-width / 2.0, width / 2.0 - wall):
    side = (
        cq.Workplane("YZ", origin=(sx, 0, 0))
        .moveTo(0, 0)
        .lineTo(depth, 0)
        .lineTo(depth, lip_h)
        .lineTo(0, wall)
        .close()
        .extrude(wall)
    )
    body = body.union(side)

# Handle socket stub (angled up from back)
socket = (
    cq.Workplane("YZ", origin=(0, depth * 0.85, lip_h * 0.7))
    .circle(socket_d / 2.0)
    .extrude(60)
    .rotate((0, depth * 0.85, lip_h * 0.7), (1, depth * 0.85, lip_h * 0.7), 25)
)
socket_hole = (
    cq.Workplane("YZ", origin=(0, depth * 0.85, lip_h * 0.7))
    .circle(socket_d / 2.0 - 3)
    .extrude(62)
    .rotate((0, depth * 0.85, lip_h * 0.7), (1, depth * 0.85, lip_h * 0.7), 25)
)
body = body.union(socket).cut(socket_hole)

result = body
'''
