from ..core.metadata import ExampleMetadata

metadata = ExampleMetadata(
    id="prosthetic_hand",
    name="Prosthetic Hand",
    category="prosthetic",
    keywords=["prosthetic", "hand", "artificial", "limb", "bionic", "prosthesis"],
    description="Prosthetic hand with palm housing, four fingers, and an opposable thumb.",
    techniques=["boolean_union", "guarded_fillet"],
    nominal_dimensions_mm={"palm_width": 85.0, "length": 180.0, "thickness": 30.0},
    difficulty="medium",
)

code = '''import cadquery as cq

palm_w = 85.0
palm_l = 95.0
palm_t = 30.0

# Palm
palm = cq.Workplane("XY").box(palm_w, palm_l, palm_t, centered=(True, True, False))
try:
    palm = palm.edges("|Z").fillet(10.0)
except Exception:
    pass

body = palm

# Four fingers
finger_w = 16.0
finger_gap = 3.0
total_fingers = 4 * finger_w + 3 * finger_gap
start_x = -total_fingers / 2 + finger_w / 2
for i in range(4):
    x = start_x + i * (finger_w + finger_gap)
    flen = [70, 82, 80, 65][i]  # index, middle, ring, pinky
    finger = (cq.Workplane("XY")
              .center(x, palm_l / 2 + flen / 2)
              .box(finger_w, flen, palm_t * 0.75, centered=(True, True, False)))
    try:
        finger = finger.edges().fillet(3.0)
    except Exception:
        pass
    body = body.union(finger)

# Thumb (angled off the side)
thumb = (cq.Workplane("XY")
         .center(palm_w / 2 + 10, -palm_l / 4)
         .box(18, 65, palm_t * 0.75, centered=(True, True, False)))
thumb = thumb.rotate((palm_w / 2, -palm_l / 4, 0), (0, 0, 1), 35)
try:
    thumb = thumb.edges().fillet(3.0)
except Exception:
    pass
body = body.union(thumb)

# Wrist coupler (cylinder below palm)
wrist = (cq.Workplane("XY")
         .center(0, -palm_l / 2 - 15)
         .circle(18).extrude(palm_t))
body = body.union(wrist)

result = body
'''
