from ..core.metadata import ExampleMetadata

metadata = ExampleMetadata(
    id="pliers_jaw",
    name="Pliers Jaw (Single Side)",
    category="tool",
    keywords=["pliers", "jaw", "tool", "grip", "mechanic", "hand", "needle", "nose", "plier"],
    description="One half of a needle-nose pliers with pivot hole and grooved jaw.",
    techniques=["polyline_profile", "guarded_fillet"],
    nominal_dimensions_mm={"length": 160.0, "thickness": 6.0, "pivot_hole_diameter": 6.0},
    difficulty="medium",
)

code = '''import cadquery as cq

length = 160.0
thick = 6.0
pivot_d = 6.0

# Outline in XY — nose on +X, handle on -X, pivot near x=30
profile = (
    cq.Workplane("XY")
    .moveTo(length, 0)
    .lineTo(length - 10, 3.5)
    .lineTo(60, 9.0)
    .lineTo(40, 14.0)
    .lineTo(30, 18.0)
    .lineTo(-5, 16.0)
    .lineTo(-length * 0.5, 10.0)
    .lineTo(-length * 0.5, -2.0)
    .lineTo(-30, -6.0)
    .lineTo(10, -4.0)
    .lineTo(40, -2.0)
    .lineTo(length - 10, -3.5)
    .close()
)
body = profile.extrude(thick)

try:
    body = body.edges("|Z").fillet(1.5)
except Exception:
    pass

# Pivot hole
body = (
    body.faces(">Z").workplane(origin=(30, 6.0, 0))
    .hole(pivot_d)
)

# Jaw grooves (3 transverse notches near nose)
for x in (110, 125, 140):
    groove = (
        cq.Workplane("YZ", origin=(x, 2, thick / 2.0))
        .rect(6, 0.8)
        .extrude(0.8)
    )
    body = body.cut(groove)

result = body
'''
