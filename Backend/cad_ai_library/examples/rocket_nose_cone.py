from ..core.metadata import ExampleMetadata

metadata = ExampleMetadata(
    id="rocket_nose_cone",
    name="Rocket Nose Cone",
    category="aerospace",
    keywords=["rocket", "nose", "cone", "tip", "ogive", "aerospace"],
    description="Ogive-style rocket nose cone with attachment shoulder (revolved, X>=0).",
    techniques=["safe_revolve"],
    nominal_dimensions_mm={"base_diameter": 40.0, "length": 90.0, "shoulder_length": 15.0},
    difficulty="medium",
)

code = '''import cadquery as cq

base_d = 40.0
length = 90.0
shoulder_l = 15.0
shoulder_d = base_d - 2.0

r_base = base_d / 2.0
r_shoulder = shoulder_d / 2.0

# Ogive-like profile using a spline (all X >= 0)
profile = (
    cq.Workplane("XZ")
    .moveTo(0, 0)
    .lineTo(r_shoulder, 0)
    .lineTo(r_shoulder, shoulder_l)
    .lineTo(r_base, shoulder_l)
    .spline([(r_base * 0.9, shoulder_l + length * 0.25),
             (r_base * 0.65, shoulder_l + length * 0.55),
             (r_base * 0.3, shoulder_l + length * 0.85),
             (0, shoulder_l + length)])
    .close()
)
body = profile.revolve(360)

result = body
'''
