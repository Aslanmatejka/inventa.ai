from ..core.metadata import ExampleMetadata

metadata = ExampleMetadata(
    id="headphone_stand",
    name="Headphone Stand",
    category="accessory",
    keywords=["headphone", "headset", "stand", "hanger", "desk", "audio"],
    description="Desk-top headphone stand with weighted base and padded hook.",
    techniques=["loft_frustum", "guarded_fillet"],
    nominal_dimensions_mm={"base_diameter": 130.0, "height": 260.0, "hook_width": 120.0},
    difficulty="medium",
)

code = '''import cadquery as cq

base_d = 130.0
base_h = 18.0
stem_h = 240.0
stem_bot = 28.0
stem_top = 18.0
hook_w = 120.0
hook_thick = 22.0

# Base
base = cq.Workplane("XY").circle(base_d / 2.0).extrude(base_h)
try:
    base = base.edges(">Z or <Z").fillet(3.0)
except Exception:
    pass

# Stem (tapered)
stem = (
    cq.Workplane("XY", origin=(0, 0, base_h))
    .circle(stem_bot / 2.0)
    .workplane(offset=stem_h)
    .circle(stem_top / 2.0)
    .loft(combine=True)
)

body = base.union(stem)

# Hook crossbar at the top
hook_z = base_h + stem_h
hook = (
    cq.Workplane("YZ", origin=(-hook_w / 2.0, 0, hook_z))
    .circle(hook_thick / 2.0)
    .extrude(hook_w)
    .rotate((0, 0, 0), (0, 1, 0), 90)
)
# Simpler: build along Y
hook = (
    cq.Workplane("XZ", origin=(0, -hook_w / 2.0, hook_z))
    .circle(hook_thick / 2.0)
    .extrude(hook_w)
)
try:
    hook = hook.edges().fillet(hook_thick * 0.3)
except Exception:
    pass

body = body.union(hook)

# Soft-curve caps on the hook ends
for yc in (-hook_w / 2.0, hook_w / 2.0):
    cap = (
        cq.Workplane("XY", origin=(0, yc, hook_z))
        .sphere(hook_thick / 2.0 * 1.05)
    )
    body = body.union(cap)

result = body
'''
