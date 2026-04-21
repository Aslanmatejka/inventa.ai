from ..core.metadata import ExampleMetadata

metadata = ExampleMetadata(
    id="osseointegrated_implant",
    name="Osseointegrated Implant Abutment",
    category="prosthetic",
    keywords=["osseointegrated", "osseointegration", "implant", "abutment", "bone-anchored", "titanium", "direct skeletal attachment", "prosthetic"],
    description="Bone-anchored prosthesis abutment: threaded intramedullary fixture, transcutaneous post, and external connector.",
    techniques=["revolve", "boolean_cut"],
    nominal_dimensions_mm={"length": 130.0, "fixture_dia": 15.0},
    difficulty="medium",
)

code = '''import cadquery as cq

# Intramedullary fixture (threaded rod look via stacked rings)
fixture = cq.Workplane("XY").circle(7.5).extrude(60)

# Thread ridges (stacked rings, no helix)
for z in range(5, 55, 5):
    ring = (cq.Workplane("XY").workplane(offset=z)
            .circle(8).circle(7.5).extrude(2))
    fixture = fixture.union(ring)

# Transition collar
collar = (cq.Workplane("XY").workplane(offset=60)
          .circle(12).circle(7.5).extrude(8))

# Transcutaneous post (polished cylinder through skin)
post = (cq.Workplane("XY").workplane(offset=68)
        .circle(9).extrude(35))

# External connector (hex coupler)
import math
hex_pts = [(10 * math.cos(math.radians(a)), 10 * math.sin(math.radians(a)))
           for a in range(0, 360, 60)]
hex_cpl = (cq.Workplane("XY").workplane(offset=103)
           .polyline(hex_pts).close().extrude(18))

# Pyramid adapter on very top
pyramid = (cq.Workplane("XY").workplane(offset=121)
           .rect(18, 18).workplane(offset=8).rect(9, 9).loft(combine=False))

body = fixture.union(collar).union(post).union(hex_cpl).union(pyramid)

# Central cannulation bore (for bone marrow / cable)
bore = cq.Workplane("XY").circle(2).extrude(130)
body = body.cut(bore)

# Anti-rotation flats on post
flat1 = (cq.Workplane("XY").workplane(offset=75)
         .center(7, 0).rect(6, 16).extrude(20))
flat2 = (cq.Workplane("XY").workplane(offset=75)
         .center(-7, 0).rect(6, 16).extrude(20))
body = body.cut(flat1).cut(flat2)

result = body
'''
