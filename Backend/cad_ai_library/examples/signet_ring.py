from ..core.metadata import ExampleMetadata

metadata = ExampleMetadata(
    id="signet_ring",
    name="Signet Ring",
    category="wearable",
    keywords=["signet", "ring", "jewelry", "seal", "band"],
    description="Band ring with an oval flat signet face for engraving.",
    techniques=["safe_revolve", "guarded_fillet"],
    nominal_dimensions_mm={"inner_diameter": 18.5, "band_width": 6.0, "signet_length": 16.0},
    difficulty="medium",
)

code = '''import cadquery as cq

id_ = 18.5
band_w = 6.0
band_t = 2.2
signet_l = 16.0
signet_w = 12.0
signet_t = 3.5

r_in = id_ / 2.0
r_out = r_in + band_t

# Band (revolved)
profile = (
    cq.Workplane("XZ")
    .moveTo(r_in, -band_w / 2.0)
    .lineTo(r_out, -band_w / 2.0)
    .lineTo(r_out, band_w / 2.0)
    .lineTo(r_in, band_w / 2.0)
    .close()
)
band = profile.revolve(360)

# Signet plate on top (+Z in plane sense: above the ring along +X actually)
# Place signet along +X on top of the band
signet = (
    cq.Workplane("XY", origin=(r_out - 0.2, 0, 0))
    .ellipse(signet_l / 2.0, signet_w / 2.0)
    .extrude(signet_t)
    .translate((0, 0, -signet_t / 2.0))
)
try:
    signet = signet.edges("|Z").fillet(1.0)
except Exception:
    pass

body = band.union(signet)

# Orient so band axis is vertical (wear orientation)
body = body.rotate((0, 0, 0), (0, 1, 0), 90).translate((0, 0, r_out))

result = body
'''
