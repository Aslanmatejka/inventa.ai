from ..core.metadata import ExampleMetadata

metadata = ExampleMetadata(
    id="kettlebell",
    name="Kettlebell",
    category="fitness",
    keywords=["kettlebell", "weight", "gym", "fitness", "exercise", "russian"],
    description="Classic kettlebell: spherical body with a flat base and an arched top handle.",
    techniques=["safe_revolve", "sweep_handle"],
    nominal_dimensions_mm={"ball_diameter": 200.0, "total_height": 280.0, "handle_thickness": 35.0},
    difficulty="medium",
)

code = '''import cadquery as cq

ball_d = 200.0
base_flat_d = 100.0
total_h = 280.0
handle_t = 35.0

r = ball_d / 2.0

# Main body: revolved profile with a flat bottom and a tapered neck
profile = (
    cq.Workplane("XZ")
    .moveTo(0, 0)
    .lineTo(base_flat_d / 2.0, 0)
    .spline([(r * 0.9, r * 0.2),
             (r, r * 0.55),
             (r * 0.85, r * 0.95)])
    .lineTo(r * 0.35, r * 1.15)
    .lineTo(r * 0.3, r * 1.25)
    .lineTo(0, r * 1.25)
    .close()
)
body = profile.revolve(360)

# Handle: ring above the body
handle_center_z = r * 1.25 + (total_h - r * 1.25) / 2.0
handle_r_outer = (total_h - r * 1.25) / 2.0 + 5
handle_outer = (
    cq.Workplane("XZ", origin=(0, 0, handle_center_z))
    .circle(handle_r_outer)
    .extrude(handle_t)
    .translate((0, -handle_t / 2.0, 0))
)
handle_hole = (
    cq.Workplane("XZ", origin=(0, 0, handle_center_z))
    .circle(handle_r_outer - handle_t * 0.8)
    .extrude(handle_t + 2)
    .translate((0, -handle_t / 2.0 - 1, 0))
)
handle = handle_outer.cut(handle_hole)

body = body.union(handle)

result = body
'''
