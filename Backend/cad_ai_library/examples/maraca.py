from ..core.metadata import ExampleMetadata

metadata = ExampleMetadata(
    id="maraca",
    name="Maraca Shaker",
    category="musical",
    keywords=["maraca", "shaker", "music", "percussion", "rattle", "latin"],
    description="Classic maraca: round head with tapered handle.",
    techniques=["safe_revolve"],
    nominal_dimensions_mm={"head_diameter": 75.0, "total_length": 220.0, "handle_diameter": 22.0},
    difficulty="easy",
)

code = '''import cadquery as cq

head_d = 75.0
total_l = 220.0
handle_d = 22.0
grip_d = 28.0

profile = (
    cq.Workplane("XZ")
    .moveTo(0, 0)
    .lineTo(grip_d / 2.0, 0)
    .lineTo(grip_d / 2.0, total_l * 0.1)
    .lineTo(handle_d / 2.0, total_l * 0.18)
    .lineTo(handle_d / 2.0, total_l * 0.55)
    .spline([(head_d / 2.0 * 0.7, total_l * 0.65),
             (head_d / 2.0, total_l * 0.78),
             (head_d / 2.0, total_l * 0.85),
             (head_d / 2.0 * 0.85, total_l * 0.95),
             (0, total_l)])
    .close()
)
body = profile.revolve(360)

result = body
'''
