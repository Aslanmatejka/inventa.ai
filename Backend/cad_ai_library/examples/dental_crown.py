from ..core.metadata import ExampleMetadata

metadata = ExampleMetadata(
    id="dental_crown",
    name="Dental Crown",
    category="prosthetic",
    keywords=["dental", "crown", "tooth", "molar", "cap", "dentistry", "prosthesis", "prosthetic tooth"],
    description="Molar dental crown: cuspal occlusal surface on a tapered hollow shell that fits over a prepared tooth.",
    techniques=["loft", "boolean_cut"],
    nominal_dimensions_mm={"width": 11.0, "length": 10.0, "height": 9.0},
    difficulty="medium",
)

code = '''import cadquery as cq

# Outer tooth body: loft from a larger crown top to a smaller gingival base
crown = (cq.Workplane("XY")
         .rect(10.5, 10.5)
         .workplane(offset=8)
         .rect(11.0, 10.0)
         .loft(combine=True))
try:
    crown = crown.edges("|Z").fillet(2.5)
except Exception:
    pass
try:
    crown = crown.edges(">Z").fillet(1.2)
except Exception:
    pass

# Four cusps (small bumps on occlusal surface)
cusp_positions = [(-2.6, -2.6), (2.6, -2.6), (2.6, 2.6), (-2.6, 2.6)]
for (x, y) in cusp_positions:
    cusp = (cq.Workplane("XY").workplane(offset=8)
            .center(x, y).sphere(1.6))
    crown = crown.union(cusp)

# Central fossa (groove cross on top)
groove_x = (cq.Workplane("XY").workplane(offset=8.2)
            .rect(8, 0.8).extrude(0.8))
groove_y = (cq.Workplane("XY").workplane(offset=8.2)
            .rect(0.8, 8).extrude(0.8))
crown = crown.cut(groove_x).cut(groove_y)

# Hollow inside (where prepared tooth seats)
inside = (cq.Workplane("XY").workplane(offset=0.8)
          .rect(8.5, 8.0).extrude(7))
try:
    inside = inside.edges("|Z").fillet(1.8)
except Exception:
    pass
body = crown.cut(inside)

result = body
'''
