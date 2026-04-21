from ..core.metadata import ExampleMetadata

metadata = ExampleMetadata(
    id="vase",
    name="Decorative Vase",
    category="decorative",
    keywords=["vase", "flower", "decor", "tapered", "spline"],
    description="Curvy vase using a planar spline profile swept around the Z axis with a safe revolve (profile stays on X>=0).",
    techniques=["revolve with safe profile", "planar spline", "bottom grounding"],
    nominal_dimensions_mm={"max_diameter": 120.0, "height": 220.0},
    difficulty="intermediate",
)

code = '''\
import cadquery as cq

height = 220.0
base_radius = 50.0
belly_radius = 60.0
neck_radius = 28.0
lip_radius = 40.0
wall = 2.8

# Profile in the XZ plane, all X values >= 0 (NEVER cross the Z axis for revolve)
profile = (
    cq.Workplane("XZ")
    .moveTo(0, 0)
    .lineTo(base_radius, 0)
    .spline([
        (belly_radius, height * 0.35),
        (neck_radius, height * 0.75),
        (lip_radius, height),
    ], includeCurrent=False)
    .lineTo(0, height)
    .close()
)

solid = profile.revolve(360)

# Hollow from the top
try:
    solid = solid.faces(">Z").shell(-wall)
except Exception:
    pass

result = solid
'''
