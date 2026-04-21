from ..core.metadata import ExampleMetadata

metadata = ExampleMetadata(
    id="stethoscope_head",
    name="Stethoscope Chestpiece",
    category="medical",
    keywords=["stethoscope", "chestpiece", "medical", "diaphragm", "doctor"],
    description="Double-sided stethoscope chestpiece with diaphragm rim and stem.",
    techniques=["safe_revolve", "guarded_fillet"],
    nominal_dimensions_mm={"diameter": 48.0, "thickness": 18.0, "stem_diameter": 8.0},
    difficulty="medium",
)

code = '''import cadquery as cq

diameter = 48.0
thickness = 18.0
stem_d = 8.0
stem_l = 22.0
rim_h = 3.0

r = diameter / 2.0

# Revolve profile in XZ
profile = (
    cq.Workplane("XZ")
    .moveTo(0, 0)
    .lineTo(r, 0)
    .lineTo(r, rim_h)
    .lineTo(r - 2, rim_h + 1)
    .lineTo(r - 2, thickness - rim_h - 1)
    .lineTo(r, thickness - rim_h)
    .lineTo(r, thickness)
    .lineTo(0, thickness)
    .close()
)
head = profile.revolve(360)

# Side stem
stem = (
    cq.Workplane("YZ", origin=(r - 0.5, 0, thickness / 2.0))
    .circle(stem_d / 2.0)
    .extrude(stem_l)
)
head = head.union(stem)

try:
    head = head.edges("%CIRCLE").fillet(0.6)
except Exception:
    pass

result = head
'''
