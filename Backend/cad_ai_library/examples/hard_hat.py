from ..core.metadata import ExampleMetadata

metadata = ExampleMetadata(
    id="hard_hat",
    name="Construction Hard Hat",
    category="safety",
    keywords=["hard", "hat", "helmet", "safety", "construction", "ppe"],
    description="Classic construction hard hat shell with front brim and top ridge.",
    techniques=["safe_revolve", "shell_cavity"],
    nominal_dimensions_mm={"outer_diameter": 220.0, "height": 120.0, "brim_length": 55.0},
    difficulty="medium",
)

code = '''import cadquery as cq

od = 220.0
height = 120.0
brim_l = 55.0
wall = 3.0

r = od / 2.0

# Revolve the shell profile
profile = (
    cq.Workplane("XZ")
    .moveTo(0, 0)
    .lineTo(r, 0)
    .spline([(r * 0.95, height * 0.35),
             (r * 0.78, height * 0.65),
             (r * 0.45, height * 0.92),
             (0, height)])
    .close()
)
shell = profile.revolve(360)

# Hollow out
inner = (
    cq.Workplane("XZ")
    .moveTo(0, wall)
    .lineTo(r - wall, wall)
    .spline([(r * 0.95 - wall, height * 0.35),
             (r * 0.78 - wall, height * 0.65),
             (r * 0.45 - wall, height * 0.92),
             (0, height - wall)])
    .close()
)
cavity = inner.revolve(360)
body = shell.cut(cavity)

# Front brim: a flat extension on one side
brim = (
    cq.Workplane("XY", origin=(r - 2, 0, 0))
    .ellipse(brim_l, r * 0.75)
    .extrude(wall * 1.5)
)
body = body.union(brim)

# Top ridge (small fin along the center)
ridge = (
    cq.Workplane("XZ", origin=(0, 0, 0))
    .moveTo(-r * 0.5, height * 0.55)
    .lineTo(r * 0.5, height * 0.55)
    .lineTo(0, height + 4)
    .close()
    .extrude(3)
    .translate((0, -1.5, 0))
)
body = body.union(ridge)

result = body
'''
