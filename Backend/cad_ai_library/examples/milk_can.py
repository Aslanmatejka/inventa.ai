from ..core.metadata import ExampleMetadata

metadata = ExampleMetadata(
    id="milk_can",
    name="Old-Style Milk Can",
    category="agriculture",
    keywords=["milk", "can", "dairy", "farm", "container", "agriculture"],
    description="Classic metal milk can with narrow neck, shoulder shoulders, wide body.",
    techniques=["safe_revolve"],
    nominal_dimensions_mm={"body_diameter": 280.0, "neck_diameter": 120.0, "total_height": 600.0},
    difficulty="medium",
)

code = '''import cadquery as cq

body_d = 280.0
neck_d = 120.0
total_h = 600.0
base_h = 20.0
shoulder_h = 90.0
neck_h = 60.0
rim_h = 15.0

r_body = body_d / 2.0
r_neck = neck_d / 2.0

profile = (
    cq.Workplane("XZ")
    .moveTo(0, 0)
    .lineTo(r_body - 20, 0)
    .lineTo(r_body, base_h)
    .lineTo(r_body, total_h - shoulder_h - neck_h - rim_h)
    .lineTo(r_neck + 10, total_h - neck_h - rim_h)
    .lineTo(r_neck, total_h - neck_h - rim_h)
    .lineTo(r_neck, total_h - rim_h)
    .lineTo(r_neck + 5, total_h - rim_h)
    .lineTo(r_neck + 5, total_h)
    .lineTo(0, total_h)
    .close()
)
body = profile.revolve(360)

# Two handle eyes near the shoulder
shoulder_z = total_h - shoulder_h - neck_h + shoulder_h * 0.25
for dx in (-r_body * 0.85, r_body * 0.85):
    handle = (
        cq.Workplane("YZ", origin=(dx, 0, shoulder_z))
        .circle(12)
        .extrude(8)
    )
    hole = (
        cq.Workplane("YZ", origin=(dx, 0, shoulder_z))
        .circle(5)
        .extrude(10)
    )
    body = body.union(handle).cut(hole)

result = body
'''
