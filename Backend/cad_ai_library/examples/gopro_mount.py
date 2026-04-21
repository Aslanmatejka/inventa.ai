from ..core.metadata import ExampleMetadata

metadata = ExampleMetadata(
    id="gopro_mount",
    name="GoPro-Style Mount",
    category="accessory",
    keywords=["gopro", "mount", "camera", "action", "adapter", "finger"],
    description="GoPro-compatible two-finger mount with shared pin hole.",
    techniques=["polyline_profile", "guarded_fillet"],
    nominal_dimensions_mm={"finger_thickness": 3.0, "finger_gap": 3.0, "pin_diameter": 5.0, "base_length": 30.0},
    difficulty="medium",
)

code = '''import cadquery as cq

finger_t = 3.0
finger_gap = 3.0
pin_d = 5.0
base_l = 30.0
base_w = 20.0
base_h = 6.0
finger_h = 18.0
finger_r = 7.0  # radius of the rounded finger top

# Base
base = cq.Workplane("XY").box(base_l, base_w, base_h, centered=(True, True, False))
try:
    base = base.edges("|Z").fillet(2.0)
except Exception:
    pass

body = base

# Finger profile in XZ: vertical stub with a half-circle top, pin hole at center
total_finger_w = 2 * finger_t + finger_gap
for i, y_off in enumerate((-total_finger_w / 2.0, total_finger_w / 2.0 - finger_t)):
    finger_profile = (
        cq.Workplane("XZ")
        .moveTo(-finger_r, base_h)
        .lineTo(finger_r, base_h)
        .lineTo(finger_r, base_h + finger_h - finger_r)
        .threePointArc((0, base_h + finger_h), (-finger_r, base_h + finger_h - finger_r))
        .lineTo(-finger_r, base_h)
        .close()
    )
    f = finger_profile.extrude(finger_t).translate((0, y_off, 0))
    body = body.union(f)

# Pin hole through both fingers
pin_cut = (
    cq.Workplane("XZ", origin=(0, -total_finger_w / 2.0 - 1, base_h + finger_h - finger_r))
    .circle(pin_d / 2.0)
    .extrude(total_finger_w + 2)
)
body = body.cut(pin_cut)

result = body
'''
