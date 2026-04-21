from ..core.metadata import ExampleMetadata

metadata = ExampleMetadata(
    id="phone_case_basic",
    name="Phone Case (Basic)",
    category="phone_case",
    keywords=["phone", "case", "cover", "phone case", "phone cover", "mobile", "shell"],
    description="Slim snap-on phone case: rounded-rectangle shell with inner cavity and camera cutout.",
    techniques=["shell", "boolean_cut", "guarded_fillet"],
    nominal_dimensions_mm={"length": 155.0, "width": 75.0, "thickness": 10.0},
    difficulty="easy",
)

code = '''import cadquery as cq

L = 155.0
W = 75.0
T = 10.0
wall = 2.0

# Outer shell
outer = cq.Workplane("XY").box(L, W, T, centered=(True, True, False))
try:
    outer = outer.edges("|Z").fillet(12.0)
except Exception:
    pass

# Inner phone cavity
inner = (cq.Workplane("XY").workplane(offset=wall)
         .box(L - 2 * wall, W - 2 * wall, T, centered=(True, True, False)))
try:
    inner = inner.edges("|Z").fillet(10.0)
except Exception:
    pass

body = outer.cut(inner)

# Screen opening (front face open)
screen = (cq.Workplane("XY").workplane(offset=T - 0.5)
          .box(L - 12, W - 10, 2, centered=(True, True, False)))
try:
    screen = screen.edges("|Z").fillet(8.0)
except Exception:
    pass
body = body.cut(screen)

# Camera cutout (back, top-left square)
cam = (cq.Workplane("XY")
       .center(L / 2 - 25, W / 2 - 25)
       .box(35, 35, T * 2, centered=(True, True, False)))
try:
    cam = cam.edges("|Z").fillet(6.0)
except Exception:
    pass
body = body.cut(cam)

# Charging port cutout (bottom)
port = (cq.Workplane("XY")
        .center(0, -W / 2)
        .box(25, 6, T * 2, centered=(True, True, False)))
body = body.cut(port)

# Side button cutouts
for y in [10, -10]:
    btn = (cq.Workplane("XY")
           .center(L / 2, y)
           .box(4, 15, T * 2, centered=(True, True, False)))
    body = body.cut(btn)

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
