from ..core.metadata import ExampleMetadata

metadata = ExampleMetadata(
    id="speaker_cabinet",
    name="Bookshelf Speaker Cabinet",
    category="electronics",
    keywords=["speaker", "cabinet", "audio", "bookshelf", "woofer", "tweeter"],
    description="Two-way bookshelf speaker cabinet with woofer, tweeter, and port openings.",
    techniques=["shell_cavity", "guarded_fillet"],
    nominal_dimensions_mm={"height": 280.0, "width": 180.0, "depth": 220.0, "wall": 12.0},
    difficulty="medium",
)

code = '''import cadquery as cq

h = 280.0
w = 180.0
d = 220.0
wall = 12.0
woofer_d = 130.0
tweeter_d = 40.0
port_d = 32.0

body = cq.Workplane("XY").box(w, d, h, centered=(True, True, False))
try:
    body = body.edges("|Z").fillet(3.0)
except Exception:
    pass

# Hollow interior (open on back for simplicity)
cavity = (
    cq.Workplane("XY", origin=(0, 0, wall))
    .box(w - 2 * wall, d - 2 * wall, h - 2 * wall,
         centered=(True, True, False))
    .translate((0, wall / 2.0, 0))
)
body = body.cut(cavity)

# Front baffle cutouts (facing -Y)
woofer = (
    cq.Workplane("XZ", origin=(0, -d / 2.0 - 1, h * 0.35))
    .circle(woofer_d / 2.0)
    .extrude(wall + 2)
)
tweeter = (
    cq.Workplane("XZ", origin=(0, -d / 2.0 - 1, h * 0.78))
    .circle(tweeter_d / 2.0)
    .extrude(wall + 2)
)
port = (
    cq.Workplane("XZ", origin=(0, -d / 2.0 - 1, h * 0.1))
    .circle(port_d / 2.0)
    .extrude(wall + 2)
)
body = body.cut(woofer).cut(tweeter).cut(port)

result = body

# --- Modern finishing pass (guarded) ---
try:
    result = result.edges("|Z").fillet(1.2)
except Exception:
    pass
try:
    result = result.faces(">Z").edges().chamfer(0.5)
except Exception:
    pass
try:
    result = result.faces("<Z").edges().fillet(0.8)
except Exception:
    pass
'''
