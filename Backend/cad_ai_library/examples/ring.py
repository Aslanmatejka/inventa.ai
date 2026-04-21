from ..core.metadata import ExampleMetadata

metadata = ExampleMetadata(
    id="ring",
    name="Finger Ring",
    category="accessory",
    keywords=["ring", "jewelry", "finger", "band", "wearable"],
    description="Plain jewelry band sized by inner diameter.",
    techniques=["safe_revolve", "guarded_fillet"],
    nominal_dimensions_mm={"inner_diameter": 18.0, "band_width": 6.0, "band_thickness": 2.0},
    difficulty="easy",
)

code = '''import cadquery as cq

inner_d = 18.0
band_w = 6.0
band_t = 2.0

r_in = inner_d / 2.0
r_out = r_in + band_t

# Cross-section in XZ plane (all X >= 0)
profile = (
    cq.Workplane("XZ")
    .moveTo(r_in, -band_w / 2.0)
    .lineTo(r_out, -band_w / 2.0)
    .lineTo(r_out, band_w / 2.0)
    .lineTo(r_in, band_w / 2.0)
    .close()
)
body = profile.revolve(360, (0, 0, 0), (0, 1, 0))

try:
    body = body.edges().fillet(min(0.6, band_t * 0.25))
except Exception:
    pass

# Translate so lowest point is Z=0
body = body.translate((0, 0, band_w / 2.0))

result = body
'''
