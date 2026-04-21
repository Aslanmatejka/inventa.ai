from ..core.metadata import ExampleMetadata

metadata = ExampleMetadata(
    id="frisbee",
    name="Flying Disc",
    category="sports",
    keywords=["frisbee", "disc", "flying", "ultimate", "throw", "toy"],
    description="Flying disc with curved rim profile, revolved from a safe (X>=0) spline.",
    techniques=["safe_revolve"],
    nominal_dimensions_mm={"diameter": 230.0, "rim_height": 28.0, "thickness": 3.0},
    difficulty="medium",
)

code = '''import cadquery as cq

d = 230.0
r = d / 2.0
rim_h = 28.0
wall = 3.0

# Outer profile in XZ (all X >= 0)
outer = (
    cq.Workplane("XZ")
    .moveTo(0, rim_h * 0.15)
    .spline([(r * 0.3, rim_h * 0.2), (r * 0.75, rim_h * 0.4), (r, rim_h)])
    .lineTo(r, rim_h - wall * 0.3)
    .spline([(r * 0.75, rim_h * 0.4 - wall), (r * 0.3, rim_h * 0.2 - wall), (0, rim_h * 0.15 - wall)])
    .close()
)
body = outer.revolve(360)

result = body
'''
