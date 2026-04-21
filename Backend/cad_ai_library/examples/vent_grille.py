from ..core.metadata import ExampleMetadata

metadata = ExampleMetadata(
    id="vent_grille",
    name="HVAC Vent Grille",
    category="hvac",
    keywords=["vent", "grille", "hvac", "air", "register", "duct", "louvered"],
    description="Rectangular HVAC vent grille with angled louvers and mounting flange.",
    techniques=["polar_array", "polyline_profile"],
    nominal_dimensions_mm={"length": 250.0, "width": 150.0, "thickness": 10.0, "louver_count": 8},
    difficulty="medium",
)

code = '''import cadquery as cq

length = 250.0
width = 150.0
thick = 10.0
flange = 12.0
louver_count = 8
louver_tilt = 25.0  # degrees

# Outer flange
body = cq.Workplane("XY").box(length, width, thick, centered=(True, True, False))
try:
    body = body.edges("|Z").fillet(3.0)
except Exception:
    pass

# Inner opening (through-hole that we will fill with louvers)
opening_l = length - 2 * flange
opening_w = width - 2 * flange
opening = (
    cq.Workplane("XY", origin=(0, 0, -1))
    .rect(opening_l, opening_w)
    .extrude(thick + 2)
)
body = body.cut(opening)

# Louvers: thin angled slats spanning the opening along X, arrayed along Y
louver_t = 1.5
louver_h = 6.0
spacing = opening_w / louver_count
for i in range(louver_count):
    y = -opening_w / 2.0 + spacing * (i + 0.5)
    slat = (
        cq.Workplane("XY", origin=(0, y, thick / 2.0))
        .box(opening_l, louver_t, louver_h, centered=(True, True, True))
        .rotate((0, y, thick / 2.0), (1, y, thick / 2.0), louver_tilt)
    )
    body = body.union(slat)

# Mount holes in the four flange corners
mount_pts = []
for sx in (-1, 1):
    for sy in (-1, 1):
        mount_pts.append((sx * (length / 2.0 - flange / 2.0),
                          sy * (width / 2.0 - flange / 2.0)))
cutter = (
    cq.Workplane("XY", origin=(0, 0, -1))
    .pushPoints(mount_pts)
    .circle(2.0)
    .extrude(thick + 2)
)
body = body.cut(cutter)

result = body
'''
