from ..core.metadata import ExampleMetadata

metadata = ExampleMetadata(
    id="garden_gnome",
    name="Stylized Garden Gnome",
    category="decorative",
    keywords=["gnome", "garden", "figurine", "decor", "statue", "whimsy"],
    description="Stylized gnome figurine: round body, conical hat, spherical head — all simple primitives.",
    techniques=["safe_revolve"],
    nominal_dimensions_mm={"total_height": 180.0, "body_diameter": 80.0, "hat_height": 70.0},
    difficulty="easy",
)

code = '''import cadquery as cq

body_d = 80.0
body_h = 80.0
head_d = 55.0
hat_h = 70.0
hat_base_d = 60.0

# Body (stubby cone)
body_profile = (
    cq.Workplane("XZ")
    .moveTo(0, 0)
    .lineTo(body_d / 2.0, 0)
    .spline([(body_d / 2.0 * 0.95, body_h * 0.3),
             (body_d / 2.0 * 0.8, body_h * 0.6),
             (head_d / 2.0 + 5, body_h)])
    .lineTo(0, body_h)
    .close()
)
body = body_profile.revolve(360)

# Head (sphere)
head = (
    cq.Workplane("XY", origin=(0, 0, body_h + head_d / 2.0 - 4))
    .sphere(head_d / 2.0)
)
body = body.union(head)

# Hat (cone)
hat_profile = (
    cq.Workplane("XZ")
    .moveTo(0, body_h + head_d - 10)
    .lineTo(hat_base_d / 2.0, body_h + head_d - 10)
    .lineTo(hat_base_d / 2.0, body_h + head_d - 6)
    .lineTo(hat_base_d / 2.0 * 0.3, body_h + head_d + hat_h * 0.7)
    .lineTo(0, body_h + head_d + hat_h)
    .close()
)
hat = hat_profile.revolve(360)
body = body.union(hat)

# Beard (smaller sphere offset forward)
beard = (
    cq.Workplane("XY", origin=(0, -head_d / 2.0 + 4, body_h + head_d / 2.0 - 12))
    .sphere(head_d / 2.0 * 0.55)
)
body = body.union(beard)

result = body
'''
