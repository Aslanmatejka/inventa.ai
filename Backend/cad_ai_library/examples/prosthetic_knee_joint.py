from ..core.metadata import ExampleMetadata

metadata = ExampleMetadata(
    id="prosthetic_knee_joint",
    name="Prosthetic Knee Joint",
    category="prosthetic",
    keywords=["prosthetic", "knee", "joint", "hinge", "above knee", "transfemoral", "amputee", "prosthesis"],
    description="Single-axis prosthetic knee joint: upper clevis, lower lug, and pin axle for hinge motion.",
    techniques=["boolean_union", "boolean_cut"],
    nominal_dimensions_mm={"height": 110.0, "width": 60.0, "depth": 50.0},
    difficulty="medium",
)

code = '''import cadquery as cq

W = 60.0
D = 50.0

# Upper socket coupler (hollow cylinder on top)
upper_cyl = (cq.Workplane("XY").workplane(offset=70)
             .circle(22).circle(18).extrude(40))

# Upper clevis (yoke) — block with a slot
yoke = cq.Workplane("XY").workplane(offset=40).box(W, D, 30, centered=(True, True, False))
slot = (cq.Workplane("XY").workplane(offset=40)
        .center(0, 0).rect(26, D + 2).extrude(30))
yoke = yoke.cut(slot)
try:
    yoke = yoke.edges("|Z").fillet(4.0)
except Exception:
    pass

# Lower lug (tongue fitting in the slot)
lug = cq.Workplane("XY").workplane(offset=30).box(24, D - 6, 24, centered=(True, True, False))
try:
    lug = lug.edges("|Y").fillet(6.0)
except Exception:
    pass

# Lower pylon coupler (cylinder below lug)
lower_cyl = cq.Workplane("XY").circle(18).circle(15).extrude(30)

# Hinge pin bore through yoke + lug
pin_bore = (cq.Workplane("YZ").workplane(offset=-W/2 - 1)
            .center(0, 45).circle(4).extrude(W + 2))

body = upper_cyl.union(yoke).union(lug).union(lower_cyl).cut(pin_bore)

# Hinge pin itself (shorter so it shows as axle)
pin = (cq.Workplane("YZ").workplane(offset=-W/2 + 4)
       .center(0, 45).circle(3.8).extrude(W - 8))
body = body.union(pin)

result = body
'''
