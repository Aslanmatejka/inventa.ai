from ..core.metadata import ExampleMetadata

metadata = ExampleMetadata(
    id="piston",
    name="Engine Piston",
    category="automotive",
    keywords=["piston", "engine", "car", "cylinder", "automotive", "motor"],
    description="Cylindrical engine piston with ring grooves, wrist pin bore, and concave crown.",
    techniques=["revolve", "boolean_cut"],
    nominal_dimensions_mm={"diameter": 80.0, "height": 70.0},
    difficulty="medium",
)

code = '''import cadquery as cq

r = 40.0
h = 70.0

# Main piston body
body = cq.Workplane("XY").circle(r).extrude(h)

# Three ring grooves
for z in [h - 8, h - 16, h - 24]:
    groove = (cq.Workplane("XY").workplane(offset=z)
              .circle(r + 0.5).circle(r - 2.5).extrude(2))
    body = body.cut(groove)

# Concave crown (dished top)
dish = (cq.Workplane("XY").workplane(offset=h - 4)
        .circle(r - 4).extrude(6))
body = body.cut(dish)

# Wrist pin bore (through, horizontal)
pin = (cq.Workplane("YZ").workplane(offset=-r - 1)
       .center(0, h * 0.35).circle(9).extrude(2 * r + 2))
body = body.cut(pin)

# Internal skirt hollow
hollow = (cq.Workplane("XY").circle(r - 6).extrude(h * 0.55))
body = body.cut(hollow)

try:
    body = body.edges(">Z").fillet(1.5)
except Exception:
    pass

result = body
'''
