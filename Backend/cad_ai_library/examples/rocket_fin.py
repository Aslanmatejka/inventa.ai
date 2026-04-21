from ..core.metadata import ExampleMetadata

metadata = ExampleMetadata(
    id="rocket_fin",
    name="Rocket Fin",
    category="aerospace",
    keywords=["rocket", "fin", "aerospace", "model rocket", "stabilizer"],
    description="Model-rocket stabilizer fin with swept leading edge and root tab.",
    techniques=["polyline_profile", "guarded_fillet"],
    nominal_dimensions_mm={"root_chord": 80.0, "tip_chord": 40.0, "span": 60.0, "thickness": 3.0},
    difficulty="easy",
)

code = '''import cadquery as cq

root_c = 80.0
tip_c = 40.0
span = 60.0
sweep = 30.0
thick = 3.0
tab_h = 4.0
tab_l = root_c * 0.8

# Fin outline + root tab (below Y=0)
profile = (
    cq.Workplane("XY")
    .moveTo(0, 0)
    .lineTo(root_c, 0)
    .lineTo(root_c - (root_c - tip_c - sweep) - tip_c, span)  # simplified — see trailing edge
    # Rebuild explicitly:
)
# cleaner explicit outline
profile = (
    cq.Workplane("XY")
    .moveTo(-tab_l / 2.0, -tab_h)
    .lineTo(tab_l / 2.0, -tab_h)
    .lineTo(root_c / 2.0, 0)
    .lineTo(root_c / 2.0 - sweep, span)
    .lineTo(root_c / 2.0 - sweep - tip_c, span)
    .lineTo(-root_c / 2.0, 0)
    .close()
)
body = profile.extrude(thick).translate((0, 0, -thick / 2.0))

try:
    body = body.edges("|Z").fillet(min(1.0, thick * 0.4))
except Exception:
    pass

# Stand it up (span along Z)
body = body.rotate((0, 0, 0), (1, 0, 0), 90).translate((0, 0, tab_h))

result = body
'''
