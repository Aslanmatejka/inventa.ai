from ..core.metadata import ExampleMetadata

metadata = ExampleMetadata(
    id="binoculars",
    name="Binoculars Body",
    category="photography",
    keywords=["binoculars", "optics", "bird", "watching", "scope", "field glasses"],
    description="Stylized binoculars: two parallel cylindrical barrels joined by a central hinge block.",
    techniques=["safe_revolve"],
    nominal_dimensions_mm={"barrel_length": 140.0, "barrel_diameter": 45.0, "spacing": 60.0},
    difficulty="medium",
)

code = '''import cadquery as cq

barrel_l = 140.0
barrel_d = 45.0
spacing = 60.0
eye_d = 22.0
objective_d = 38.0

def barrel(x_offset):
    profile = (
        cq.Workplane("XZ")
        .moveTo(0, 0)
        .lineTo(eye_d / 2.0, 0)
        .lineTo(eye_d / 2.0, 8)
        .lineTo(barrel_d / 2.0, 14)
        .lineTo(barrel_d / 2.0, barrel_l - 14)
        .lineTo(objective_d / 2.0, barrel_l - 8)
        .lineTo(objective_d / 2.0, barrel_l)
        .lineTo(0, barrel_l)
        .close()
    )
    return profile.revolve(360).translate((x_offset, 0, 0))

left = barrel(-spacing / 2.0)
right = barrel(spacing / 2.0)

# Central hinge block
hinge = (
    cq.Workplane("XY", origin=(0, 0, barrel_l * 0.4))
    .box(spacing, 25, barrel_l * 0.35, centered=(True, True, False))
)
try:
    hinge = hinge.edges("|Y").fillet(6.0)
except Exception:
    pass

# Focus knob on top of hinge
knob = (
    cq.Workplane("XZ", origin=(0, -15, barrel_l * 0.55))
    .circle(7)
    .extrude(30)
    .translate((0, 0, 0))
)

body = left.union(right).union(hinge).union(knob)

result = body
'''
