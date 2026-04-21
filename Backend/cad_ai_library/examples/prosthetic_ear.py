from ..core.metadata import ExampleMetadata

metadata = ExampleMetadata(
    id="prosthetic_ear",
    name="Prosthetic Ear",
    category="prosthetic",
    keywords=["prosthetic", "ear", "auricular", "artificial ear", "silicone ear", "prosthesis"],
    description="Auricular prosthesis: stylized outer-ear silhouette with helix ridge and concha bowl.",
    techniques=["boolean_union", "boolean_cut", "guarded_fillet"],
    nominal_dimensions_mm={"height": 65.0, "width": 38.0, "depth": 18.0},
    difficulty="medium",
)

code = '''import cadquery as cq

# Outer ear outline (roughly egg-shaped polygon in XZ plane)
ear_pts = [
    (0, 0), (10, -2), (18, 2), (22, 10), (24, 22),
    (22, 40), (16, 55), (6, 62), (-4, 60), (-8, 48),
    (-6, 28), (-8, 10), (-2, 2),
]
ear = (cq.Workplane("XZ").polyline(ear_pts).close().extrude(18))
try:
    ear = ear.edges("|Y").fillet(3.0)
except Exception:
    pass

# Helix ridge (raised rim)
helix_pts = [
    (-4, 60), (16, 55), (22, 40), (24, 22), (22, 10), (18, 2),
]
helix = (cq.Workplane("XZ").polyline(helix_pts).close().extrude(3)
         .translate((0, 9, 0)))
try:
    helix = helix.edges("|Y").fillet(1.2)
except Exception:
    pass

# Concha bowl (recess on front)
concha = (cq.Workplane("XZ").workplane(offset=9 - 2)
          .center(8, 26).circle(10).extrude(8))
body = ear.union(helix).cut(concha)

# Ear canal opening
canal = (cq.Workplane("XZ").workplane(offset=-1)
         .center(8, 26).circle(3).extrude(20))
body = body.cut(canal)

# Earlobe rounding (trim bottom)
try:
    body = body.edges("<Z").fillet(4.0)
except Exception:
    pass

result = body
'''
