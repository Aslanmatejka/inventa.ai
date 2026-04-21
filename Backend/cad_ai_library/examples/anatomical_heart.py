from ..core.metadata import ExampleMetadata

metadata = ExampleMetadata(
    id="anatomical_heart",
    name="Stylized Anatomical Heart",
    category="educational",
    keywords=["heart", "anatomy", "anatomical", "medical", "education", "biology", "organ"],
    description="Stylized anatomical heart shape — two spheres merged with a pointed apex, plus stubs for major vessels.",
    techniques=["sphere_union"],
    nominal_dimensions_mm={"width": 100.0, "height": 120.0, "depth": 80.0},
    difficulty="medium",
)

code = '''import cadquery as cq

# Two atria-like spheres merged with an apex cone-ish body
left_sphere = cq.Workplane("XY", origin=(-25, 0, 70)).sphere(40)
right_sphere = cq.Workplane("XY", origin=(28, 0, 70)).sphere(38)

# Apex (pointed bottom) via revolve — all X >= 0
apex_profile = (
    cq.Workplane("XZ")
    .moveTo(0, 0)
    .lineTo(50, 20)
    .spline([(55, 50), (48, 80)])
    .lineTo(0, 95)
    .close()
)
apex = apex_profile.revolve(360)

body = left_sphere.union(right_sphere).union(apex)
try:
    body = body.fillet(8.0)
except Exception:
    pass

# Aorta stub (tube on top)
aorta = (
    cq.Workplane("XY", origin=(-5, 5, 100))
    .circle(8)
    .extrude(25)
)
aorta_hole = (
    cq.Workplane("XY", origin=(-5, 5, 100))
    .circle(5)
    .extrude(26)
)
body = body.union(aorta).cut(aorta_hole)

# Pulmonary vessel stub
pulm = (
    cq.Workplane("XY", origin=(15, -5, 100))
    .circle(6)
    .extrude(20)
)
pulm_hole = (
    cq.Workplane("XY", origin=(15, -5, 100))
    .circle(3.5)
    .extrude(21)
)
body = body.union(pulm).cut(pulm_hole)

result = body
'''
