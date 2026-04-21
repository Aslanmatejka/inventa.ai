from ..core.metadata import ExampleMetadata

metadata = ExampleMetadata(
    id="pipe_elbow",
    name="90-Degree Pipe Elbow",
    category="plumbing",
    keywords=["pipe", "elbow", "fitting", "plumbing", "90 degree", "bend"],
    description="Two perpendicular cylindrical sockets joined at a 90-degree corner with sweep.",
    techniques=["safe_revolve", "guarded_fillet"],
    nominal_dimensions_mm={"outer_diameter": 32.0, "inner_diameter": 25.0, "leg_length": 50.0},
    difficulty="medium",
)

code = '''import cadquery as cq

od = 32.0
id_ = 25.0
leg = 50.0
bend_r = od * 0.8

# Sweep path: L-shape in XZ then a Y-extrusion across gives us two legs + corner
# Build each leg as a tube, then union a quarter-torus at the corner
r_out = od / 2.0
r_in = id_ / 2.0

# Horizontal leg along +X
leg_x = (
    cq.Workplane("YZ", origin=(0, 0, 0))
    .circle(r_out).circle(r_in)
    .extrude(leg)
)

# Vertical leg along +Z
leg_z = (
    cq.Workplane("XY", origin=(0, 0, 0))
    .circle(r_out).circle(r_in)
    .extrude(leg)
)

# Corner sphere joiner (simple but safe)
corner = (
    cq.Workplane("XY", origin=(0, 0, 0))
    .sphere(r_out)
)
corner_bore = (
    cq.Workplane("XY", origin=(0, 0, 0))
    .sphere(r_in)
)
corner = corner.cut(corner_bore)

body = leg_x.union(leg_z).union(corner)

result = body
'''
