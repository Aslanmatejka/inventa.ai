from ..core.metadata import ExampleMetadata

metadata = ExampleMetadata(
    id="drawer_pull",
    name="Drawer Pull Handle",
    category="furniture",
    keywords=["drawer", "pull", "handle", "cabinet", "furniture", "knob"],
    description="Bar-style drawer pull with two mounting posts.",
    techniques=["loft_frustum", "guarded_fillet"],
    nominal_dimensions_mm={"bar_length": 96.0, "bar_diameter": 12.0, "standoff": 25.0, "hole_center_distance": 96.0},
    difficulty="medium",
)

code = '''import cadquery as cq

bar_len = 128.0
bar_d = 12.0
hole_cc = 96.0
standoff = 25.0
post_d = 10.0
thread_d = 4.0

# Horizontal bar along X
bar = (
    cq.Workplane("YZ", origin=(-bar_len / 2.0, 0, standoff))
    .circle(bar_d / 2.0)
    .extrude(bar_len)
)
try:
    bar = bar.edges().fillet(bar_d * 0.2)
except Exception:
    pass

body = bar

# Two mounting posts from bar down to Z=0
for xc in (-hole_cc / 2.0, hole_cc / 2.0):
    post = (
        cq.Workplane("XY", origin=(xc, 0, 0))
        .circle(post_d / 2.0)
        .workplane(offset=standoff)
        .circle(post_d / 2.0 * 0.85)
        .loft(combine=True)
    )
    body = body.union(post)

    # Threaded stud sticking down (for fastener)
    stud = (
        cq.Workplane("XY", origin=(xc, 0, -8.0))
        .circle(thread_d / 2.0)
        .extrude(8.0)
    )
    body = body.union(stud)

result = body
'''
