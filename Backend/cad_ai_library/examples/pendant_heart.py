from ..core.metadata import ExampleMetadata

metadata = ExampleMetadata(
    id="pendant_heart",
    name="Heart Pendant",
    category="wearable",
    keywords=["pendant", "heart", "jewelry", "necklace", "charm"],
    description="Flat heart-shaped pendant with bail loop for a chain.",
    techniques=["polyline_profile", "guarded_fillet"],
    nominal_dimensions_mm={"width": 26.0, "height": 24.0, "thickness": 2.5},
    difficulty="easy",
)

code = '''import cadquery as cq

w = 26.0
h = 24.0
t = 2.5

# Heart outline using two arcs and two straight lines meeting at bottom
heart = (
    cq.Workplane("XY")
    .moveTo(0, -h / 2.0)
    .threePointArc((w / 2.0, -h * 0.05), (w / 4.0, h / 2.0))
    .threePointArc((0, h / 2.0 - 4), (-w / 4.0, h / 2.0))
    .threePointArc((-w / 2.0, -h * 0.05), (0, -h / 2.0))
    .close()
    .extrude(t)
)
try:
    heart = heart.edges(">Z or <Z").fillet(0.5)
except Exception:
    pass

# Bail loop at top
bail_outer = (
    cq.Workplane("XY", origin=(0, h / 2.0 - 2, 0))
    .circle(3.5)
    .extrude(t)
)
bail_inner = (
    cq.Workplane("XY", origin=(0, h / 2.0 - 2, -0.1))
    .circle(2.0)
    .extrude(t + 0.2)
)
bail = bail_outer.cut(bail_inner)
body = heart.union(bail)

result = body
'''
