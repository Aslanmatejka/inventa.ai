from ..core.metadata import ExampleMetadata

metadata = ExampleMetadata(
    id="bird_house",
    name="Bird House",
    category="outdoor",
    keywords=["bird", "house", "nest", "garden", "outdoor", "aviary"],
    description="Classic peaked-roof bird house with entry hole and perch.",
    techniques=["polyline_profile", "guarded_fillet"],
    nominal_dimensions_mm={"body_length": 150.0, "body_width": 120.0, "body_height": 140.0, "roof_overhang": 20.0},
    difficulty="medium",
)

code = '''import cadquery as cq

body_l = 150.0
body_w = 120.0
body_h = 140.0
wall = 6.0
roof_overhang = 20.0
roof_thick = 8.0
entry_d = 32.0
perch_d = 8.0
perch_len = 30.0

# House body (hollow box, no top)
body = cq.Workplane("XY").box(body_l, body_w, body_h, centered=(True, True, False))
inner = (
    cq.Workplane("XY", origin=(0, 0, wall))
    .box(body_l - 2 * wall, body_w - 2 * wall, body_h, centered=(True, True, False))
)
body = body.cut(inner)

# Front entry hole + perch
body = (
    body.faces(">Y").workplane()
    .center(0, 15.0)
    .hole(entry_d)
)
perch = (
    cq.Workplane("XZ", origin=(0, body_w / 2.0, body_h * 0.55 - 20.0))
    .circle(perch_d / 2.0)
    .extrude(perch_len)
)
body = body.union(perch)

# Peaked roof: triangular prism via polyline in XZ
peak_h = 45.0
roof_profile = (
    cq.Workplane("YZ")
    .moveTo(-(body_w / 2.0 + roof_overhang), body_h)
    .lineTo(body_w / 2.0 + roof_overhang, body_h)
    .lineTo(body_w / 2.0 + roof_overhang, body_h + roof_thick)
    .lineTo(0, body_h + peak_h + roof_thick)
    .lineTo(-(body_w / 2.0 + roof_overhang), body_h + roof_thick)
    .close()
)
roof = roof_profile.extrude(body_l + 2 * roof_overhang).translate((-(body_l / 2.0 + roof_overhang), 0, 0))
body = body.union(roof)

result = body
'''
