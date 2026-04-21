from ..core.metadata import ExampleMetadata

metadata = ExampleMetadata(
    id="garden_stake",
    name="Garden Label Stake",
    category="outdoor",
    keywords=["garden", "stake", "label", "plant", "marker", "outdoor"],
    description="Plant label stake with flat label plate and pointed ground spike.",
    techniques=["polyline_profile"],
    nominal_dimensions_mm={"total_height": 180.0, "label_width": 70.0, "label_height": 50.0, "thickness": 3.0},
    difficulty="easy",
)

code = '''import cadquery as cq

total_h = 180.0
label_w = 70.0
label_h = 50.0
thick = 3.0
stem_w = 12.0
tip_h = 25.0

# Outline in XZ: flat label top, narrow stem, pointed tip
profile = (
    cq.Workplane("XZ")
    .moveTo(-label_w / 2.0, total_h)
    .lineTo(label_w / 2.0, total_h)
    .lineTo(label_w / 2.0, total_h - label_h)
    .lineTo(stem_w / 2.0, total_h - label_h - 5.0)
    .lineTo(stem_w / 2.0, tip_h)
    .lineTo(0, 0)
    .lineTo(-stem_w / 2.0, tip_h)
    .lineTo(-stem_w / 2.0, total_h - label_h - 5.0)
    .lineTo(-label_w / 2.0, total_h - label_h)
    .close()
)
body = profile.extrude(thick).translate((0, -thick / 2.0, 0))

try:
    body = body.edges("|Y").fillet(min(1.5, thick * 0.45))
except Exception:
    pass

result = body
'''
