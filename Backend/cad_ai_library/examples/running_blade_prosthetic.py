from ..core.metadata import ExampleMetadata

metadata = ExampleMetadata(
    id="running_blade_prosthetic",
    name="Running Blade Prosthesis",
    category="prosthetic",
    keywords=["prosthetic", "running blade", "blade", "carbon fiber", "paralympic", "sprint", "flex foot", "sport prosthesis", "cheetah"],
    description="Carbon-fiber sprinter's running blade: J-curve spring profile with socket coupler at top.",
    techniques=["sweep", "boolean_union"],
    nominal_dimensions_mm={"height": 480.0, "width": 85.0, "thickness": 18.0},
    difficulty="advanced",
)

code = '''import cadquery as cq

# J-curve blade profile (side view, XZ plane) as a thick polyline extrusion
# Approximates the cheetah-flex curve: tall upper straight, hook at bottom
blade_outer = [
    (0, 480), (18, 480), (22, 400), (24, 300), (22, 200),
    (14, 130), (0, 80), (-30, 50), (-70, 30), (-110, 15),
    (-150, 10), (-180, 20), (-180, 32), (-148, 24),
    (-108, 28), (-72, 44), (-38, 62), (-14, 92),
    (6, 140), (14, 210), (14, 300), (12, 400), (12, 480),
]
blade = (cq.Workplane("XZ").polyline(blade_outer).close()
         .extrude(18, both=True))

# Socket coupler on top
coupler = (cq.Workplane("XY").workplane(offset=475)
           .center(10, 0).circle(22).extrude(40))

# Pyramid adapter on top of coupler
pyramid = (cq.Workplane("XY").workplane(offset=515)
           .center(10, 0).rect(34, 34).workplane(offset=12).rect(18, 18).loft(combine=False))

# Sole tread pad near the bottom hook
tread = (cq.Workplane("XY").workplane(offset=8)
         .center(-145, 0).box(70, 40, 8, centered=(True, True, False)))
try:
    tread = tread.edges("|Z").fillet(6.0)
except Exception:
    pass

body = blade.union(coupler).union(pyramid).union(tread)

try:
    body = body.edges("|Y").fillet(1.5)
except Exception:
    pass

result = body
'''
