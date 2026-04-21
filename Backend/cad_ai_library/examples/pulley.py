from ..core.metadata import ExampleMetadata

metadata = ExampleMetadata(
    id="pulley",
    name="V-Belt Pulley",
    category="mechanical",
    keywords=["pulley", "belt", "wheel", "drive", "sheave"],
    description="Grooved pulley revolved from a V-belt profile, with central bore and set-screw hole.",
    techniques=["safe_revolve", "cbore_hole"],
    nominal_dimensions_mm={"outer_diameter": 50.0, "bore_diameter": 8.0, "thickness": 14.0, "groove_depth": 4.0},
    difficulty="medium",
)

code = '''import cadquery as cq

outer_r = 25.0
bore_r = 4.0
thick = 14.0
groove_depth = 4.0
set_screw_d = 3.2

# Revolve profile (all X >= 0) — V-groove on the rim
profile = (
    cq.Workplane("XZ")
    .moveTo(bore_r, 0)
    .lineTo(outer_r, 0)
    .lineTo(outer_r, thick * 0.25)
    .lineTo(outer_r - groove_depth, thick * 0.5)
    .lineTo(outer_r, thick * 0.75)
    .lineTo(outer_r, thick)
    .lineTo(bore_r, thick)
    .close()
)
body = profile.revolve(360)

# Set-screw radial hole into the hub
set_cut = (
    cq.Workplane("XZ", origin=(0, -outer_r - 1, thick / 2.0))
    .circle(set_screw_d / 2.0)
    .extrude(outer_r * 2 + 2)
)
body = body.cut(set_cut)

result = body
'''
