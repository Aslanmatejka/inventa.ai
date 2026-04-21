from ..core.metadata import ExampleMetadata

metadata = ExampleMetadata(
    id="prosthetic_eye",
    name="Prosthetic Eye",
    category="prosthetic",
    keywords=["prosthetic", "eye", "ocular", "glass eye", "artificial eye", "ocularist", "prosthesis"],
    description="Ocular prosthesis: hemispherical sclera shell with raised iris dome and pupil recess.",
    techniques=["revolve", "boolean_cut"],
    nominal_dimensions_mm={"width": 25.0, "height": 22.0, "depth": 14.0},
    difficulty="easy",
)

code = '''import cadquery as cq

# Sclera shell profile (revolved): hemisphere with flatter back
sclera_pts = [
    (0, 0),
    (12.5, 0),
    (12.5, 4),
    (11, 9),
    (7, 12.5),
    (0, 14),
]
sclera = cq.Workplane("XZ").polyline(sclera_pts).close().revolve(360, (0, 0, 0), (0, 1, 0))

# Hollow the back side
back_cut = cq.Workplane("XY").circle(12).extrude(2)
sclera = sclera.cut(back_cut)

# Iris dome (raised on front)
iris = (cq.Workplane("XY").workplane(offset=13)
        .circle(5).extrude(0.8))
body = sclera.union(iris)

# Pupil recess (small indent in iris)
pupil = (cq.Workplane("XY").workplane(offset=13.5)
         .circle(1.5).extrude(0.6))
body = body.cut(pupil)

result = body
'''
