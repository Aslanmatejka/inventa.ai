from ..core.metadata import ExampleMetadata

metadata = ExampleMetadata(
    id="drumstick",
    name="Drumstick",
    category="music_accessory",
    keywords=["drum", "drumstick", "stick", "music", "percussion", "drummer"],
    description="Wooden drumstick: tapered shaft with acorn-shaped tip.",
    techniques=["safe_revolve"],
    nominal_dimensions_mm={"length": 400.0, "butt_diameter": 14.0, "tip_diameter": 8.0, "head_diameter": 18.0},
    difficulty="easy",
)

code = '''import cadquery as cq

length = 400.0
butt_d = 14.0
neck_d = 10.0
head_d = 18.0

profile = (
    cq.Workplane("XZ")
    .moveTo(0, 0)
    .lineTo(butt_d / 2.0, 0)
    .lineTo(butt_d / 2.0, length * 0.05)
    .spline([(butt_d / 2.0 * 0.95, length * 0.35),
             (neck_d / 2.0 + 1, length * 0.75),
             (neck_d / 2.0, length * 0.85),
             (head_d / 2.0, length * 0.93),
             (head_d / 2.0 * 0.85, length * 0.98),
             (0, length)])
    .close()
)
body = profile.revolve(360)

result = body
'''
