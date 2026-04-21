from ..core.metadata import ExampleMetadata

metadata = ExampleMetadata(
    id="thermostat_ring",
    name="Smart Thermostat",
    category="electronics",
    keywords=["thermostat", "smart thermostat", "nest", "hvac", "ring", "climate"],
    description="Round smart thermostat with outer rotating ring and recessed display face.",
    techniques=["revolve", "boolean_cut"],
    nominal_dimensions_mm={"diameter": 85.0, "depth": 28.0},
    difficulty="easy",
)

code = '''import cadquery as cq

r_outer = 42.5
r_inner = 34.0
d = 28.0

# Outer ring
body = cq.Workplane("XY").circle(r_outer).extrude(d)

# Inner recess for display
recess = (cq.Workplane("XY").workplane(offset=d - 5)
          .circle(r_inner).extrude(6))
body = body.cut(recess)

# Display disk (slightly inset)
disp = (cq.Workplane("XY").workplane(offset=d - 4)
        .circle(r_inner - 1).extrude(1.5))
body = body.union(disp)

# Outer bevel
try:
    body = body.edges(">Z").fillet(4.0)
except Exception:
    pass
try:
    body = body.edges("<Z").fillet(2.0)
except Exception:
    pass

# Back mounting recess
back = (cq.Workplane("XY").circle(r_outer - 6).extrude(4))
body = body.cut(back)

result = body
'''
