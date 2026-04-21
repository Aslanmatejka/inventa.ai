from ..core.metadata import ExampleMetadata

metadata = ExampleMetadata(
    id="bebionic_hand",
    name="Multi-Articulating Bionic Hand",
    category="prosthetic",
    keywords=["prosthetic", "bionic", "bebionic", "multi-articulating", "myoelectric hand", "robotic hand", "i-limb", "modern prosthesis"],
    description="Modern multi-articulating bionic hand: palm chassis with five individually actuated fingers and opposable thumb.",
    techniques=["boolean_union", "boolean_cut", "guarded_fillet"],
    nominal_dimensions_mm={"palm_width": 88.0, "length": 200.0, "thickness": 34.0},
    difficulty="advanced",
)

code = '''import cadquery as cq

palm_w = 88.0
palm_l = 105.0
palm_t = 34.0

# Palm chassis
palm = cq.Workplane("XY").box(palm_w, palm_l, palm_t, centered=(True, True, False))
try:
    palm = palm.edges("|Z").fillet(8.0)
except Exception:
    pass

# Knuckle row recesses (four MCP joint cutouts along distal edge)
for i in range(4):
    x = -palm_w / 2 + 14 + i * ((palm_w - 28) / 3)
    knuckle = (cq.Workplane("YZ").workplane(offset=x - 5)
               .center(palm_l / 2 - 4, palm_t / 2).circle(5).extrude(10))
    palm = palm.cut(knuckle)

body = palm

# Four segmented fingers (2 phalanges each, articulated look)
finger_w = 15.0
gap = 4.0
total = 4 * finger_w + 3 * gap
start_x = -total / 2 + finger_w / 2
finger_lens = [78, 90, 88, 72]  # index, middle, ring, pinky

for i in range(4):
    x = start_x + i * (finger_w + gap)
    flen = finger_lens[i]
    # Proximal phalanx
    p1_len = flen * 0.55
    p1 = (cq.Workplane("XY")
          .center(x, palm_l / 2 + p1_len / 2)
          .box(finger_w, p1_len, palm_t * 0.7, centered=(True, True, False)))
    # Distal phalanx
    p2_len = flen - p1_len - 2
    p2 = (cq.Workplane("XY")
          .center(x, palm_l / 2 + p1_len + 2 + p2_len / 2)
          .box(finger_w - 2, p2_len, palm_t * 0.6, centered=(True, True, False)))
    try:
        p1 = p1.edges().fillet(2.5)
        p2 = p2.edges().fillet(3.0)
    except Exception:
        pass
    # Knuckle pin between them (visible pivot)
    pin = (cq.Workplane("YZ").workplane(offset=x - finger_w / 2 - 1)
           .center(palm_l / 2 + p1_len + 1, palm_t * 0.35)
           .circle(1.5).extrude(finger_w + 2))
    body = body.union(p1).union(p2).union(pin)

# Opposable thumb (rotated 35°)
thumb_base = (cq.Workplane("XY")
              .center(palm_w / 2 + 6, -palm_l / 4)
              .box(20, 38, palm_t * 0.75, centered=(True, True, False)))
thumb_tip = (cq.Workplane("XY")
             .center(palm_w / 2 + 6, -palm_l / 4 + 30)
             .box(16, 32, palm_t * 0.6, centered=(True, True, False)))
try:
    thumb_base = thumb_base.edges().fillet(3.0)
    thumb_tip = thumb_tip.edges().fillet(3.0)
except Exception:
    pass
thumb = thumb_base.union(thumb_tip)
thumb = thumb.rotate((palm_w / 2, -palm_l / 4, 0), (0, 0, 1), 35)
body = body.union(thumb)

# Wrist quick-disconnect coupler
wrist = (cq.Workplane("XY")
         .center(0, -palm_l / 2 - 16)
         .circle(20).circle(16).extrude(palm_t))
body = body.union(wrist)

# Electrode/sensor window on back of palm
window = (cq.Workplane("XY").workplane(offset=palm_t - 2)
          .center(0, -palm_l / 4).rect(40, 22).extrude(3))
body = body.cut(window)

# LED status slot
led = (cq.Workplane("XY").workplane(offset=palm_t - 0.5)
       .center(palm_w / 2 - 8, palm_l / 2 - 8).circle(2.5).extrude(1))
body = body.cut(led)

result = body

# --- Modern finishing pass (guarded) ---
try:
    result = result.edges("|Z").fillet(1.2)
except Exception:
    pass
try:
    result = result.faces(">Z").edges().chamfer(0.5)
except Exception:
    pass
try:
    result = result.faces("<Z").edges().fillet(0.8)
except Exception:
    pass
'''
