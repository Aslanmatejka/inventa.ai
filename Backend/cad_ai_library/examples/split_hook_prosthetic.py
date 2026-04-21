from ..core.metadata import ExampleMetadata

metadata = ExampleMetadata(
    id="split_hook_prosthetic",
    name="Split Hook Prosthetic",
    category="prosthetic",
    keywords=["prosthetic", "hook", "split hook", "body powered", "terminal device", "amputee", "prosthesis", "arm"],
    description="Body-powered split-hook prosthesis terminal device: two curved opposing hook fingers on a base.",
    techniques=["boolean_union", "revolve"],
    nominal_dimensions_mm={"length": 130.0, "width": 60.0, "thickness": 14.0},
    difficulty="medium",
)

code = '''import cadquery as cq

T = 14.0

# Base / wrist coupler cylinder
coupler = cq.Workplane("XY").circle(12).extrude(35)

# Pivot block at top of coupler
block = (cq.Workplane("XY").workplane(offset=35)
         .box(40, T, 20, centered=(True, True, False)))
try:
    block = block.edges("|Y").fillet(3.0)
except Exception:
    pass

body = coupler.union(block)

# Two curved hook fingers (polygon approximation of a 'J' shape)
def hook(mirror):
    pts = [
        (0, 0), (50, 0), (80, 20), (85, 55), (70, 85),
        (55, 90), (55, 75), (65, 55), (60, 35), (40, 25),
        (0, 25),
    ]
    pts = [(x * mirror, y) for (x, y) in pts]
    h = (cq.Workplane("XZ").polyline(pts).close().extrude(T, both=False))
    h = h.translate((0, -T / 2, 45))
    return h

left = hook(1)
right = hook(-1)
body = body.union(left).union(right)

# Pivot pin through both hooks
pin = (cq.Workplane("YZ").workplane(offset=-T - 2)
       .center(0, 50).circle(2.5).extrude(2 * T + 4))
body = body.union(pin)

# Cable attachment loop at base of hooks
loop = (cq.Workplane("YZ").workplane(offset=0)
        .center(0, 35).circle(5).circle(3).extrude(T + 4, both=True))
body = body.union(loop)

result = body
'''
