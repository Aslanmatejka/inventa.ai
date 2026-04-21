from ..core.metadata import ExampleMetadata

metadata = ExampleMetadata(
    id="magnifying_glass",
    name="Magnifying Glass",
    category="photography",
    keywords=["magnifying", "glass", "loupe", "lens", "magnifier", "detective"],
    description="Classic magnifying glass: round lens in a thin ring frame with a straight handle.",
    techniques=["safe_revolve"],
    nominal_dimensions_mm={"lens_diameter": 70.0, "handle_length": 120.0, "handle_diameter": 15.0},
    difficulty="easy",
)

code = '''import cadquery as cq

lens_d = 70.0
handle_l = 120.0
handle_d = 15.0
frame_t = 6.0
lens_t = 4.0

# Frame ring
ring = (
    cq.Workplane("XY")
    .circle(lens_d / 2.0 + 4)
    .extrude(frame_t)
)
ring_hole = (
    cq.Workplane("XY", origin=(0, 0, -0.1))
    .circle(lens_d / 2.0)
    .extrude(frame_t + 0.2)
)
frame = ring.cut(ring_hole)

# Lens (domed) — must have Z >= 0 for profile, then position
lens_profile = (
    cq.Workplane("XZ")
    .moveTo(0, 0)
    .lineTo(lens_d / 2.0, 0)
    .spline([(lens_d / 2.0 * 0.7, lens_t * 0.8),
             (0, lens_t)])
    .close()
)
lens = lens_profile.revolve(360).translate((0, 0, frame_t / 2.0 - lens_t / 2.0))

# Handle (cylinder along +X, built via revolve of a rectangle around X axis)
handle_start_x = lens_d / 2.0 + 2
handle = (
    cq.Workplane("YZ", origin=(handle_start_x, 0, frame_t / 2.0))
    .circle(handle_d / 2.0)
    .extrude(handle_l)
)
# Grip cap
cap = cq.Workplane("XY", origin=(handle_start_x + handle_l, 0, frame_t / 2.0)).sphere(handle_d * 0.7)

body = frame.union(lens).union(handle).union(cap)

result = body
'''
