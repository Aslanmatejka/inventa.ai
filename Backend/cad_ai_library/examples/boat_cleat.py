from ..core.metadata import ExampleMetadata

metadata = ExampleMetadata(
    id="boat_cleat",
    name="Boat Deck Cleat",
    category="marine",
    keywords=["cleat", "boat", "marine", "dock", "rope", "tie"],
    description="Traditional horn cleat with flared ends and two mounting holes.",
    techniques=["safe_revolve", "guarded_fillet"],
    nominal_dimensions_mm={"total_length": 150.0, "horn_diameter": 22.0, "mount_spacing": 100.0},
    difficulty="medium",
)

code = '''import cadquery as cq

total_l = 150.0
horn_d = 22.0
mount_cc = 100.0
base_w = 28.0
base_h = 10.0
hole_d = 7.0

# Base plate
base = cq.Workplane("XY").box(total_l, base_w, base_h, centered=(True, True, False))
try:
    base = base.edges("|Z").fillet(6.0)
except Exception:
    pass
body = base

# Horn bar (horizontal cylinder with flared ends)
r_horn = horn_d / 2.0
flare_r = r_horn * 1.35
bar_z = base_h + r_horn
bar = (
    cq.Workplane("YZ", origin=(-total_l / 2.0 + flare_r, 0, bar_z))
    .circle(r_horn)
    .extrude(total_l - 2 * flare_r)
)
body = body.union(bar)

# Flared end caps (spheres)
for xc in (-total_l / 2.0 + flare_r, total_l / 2.0 - flare_r):
    cap = cq.Workplane("XY", origin=(xc, 0, bar_z)).sphere(flare_r)
    body = body.union(cap)

# Central riser under the horn
riser = (
    cq.Workplane("XY", origin=(0, 0, base_h))
    .box(r_horn * 2.2, base_w * 0.7, r_horn, centered=(True, True, False))
)
try:
    riser = riser.edges("|Y").fillet(3.0)
except Exception:
    pass
body = body.union(riser)

# Two mount holes
body = (
    body.faces(">Z").workplane(offset=-base_h - r_horn - flare_r)  # re-plane onto base top
    .pushPoints([(-mount_cc / 2.0, 0), (mount_cc / 2.0, 0)])
)
# Simpler: just cut straight through
hole_cutter = (
    cq.Workplane("XY", origin=(0, 0, -1))
    .pushPoints([(-mount_cc / 2.0, 0), (mount_cc / 2.0, 0)])
    .circle(hole_d / 2.0)
    .extrude(base_h + 2)
)
body = body.cut(hole_cutter)

result = body
'''
