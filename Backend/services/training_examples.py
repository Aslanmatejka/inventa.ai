"""
Verified CadQuery Training Examples
Real working code examples for common product categories.
Each example has been validated to produce correct 3D geometry.

Used by claude_service to inject relevant examples into prompts,
giving the AI concrete patterns that are proven to work.
"""

# ── Verified working CadQuery examples by product category ──────
# Each entry: category keywords → working code + description
# These are REAL examples that execute without errors.

TRAINING_EXAMPLES = {

    # ═══════════════════════════════════════════════════════════════
    # ELECTRONICS ENCLOSURE — box + shell + cutouts
    # ═══════════════════════════════════════════════════════════════
    "electronics_enclosure": {
        "keywords": ["enclosure", "electronics box", "project box", "junction box", "control box", "pcb case", "arduino case", "raspberry pi case"],
        "category": "Electronics Enclosure",
        "description": "Hollow box with screw bosses, PCB standoffs, ventilation, and cable entry.",
        "code": """import cadquery as cq
import math

# ═══ PARAMETERS ═══
body_x = 120.0   # width
body_y = 80.0    # depth
body_z = 40.0    # height
wall = 2.5       # wall thickness
corner_r = 3.0   # corner radius
lid_lip = 1.5    # lid overlap lip height
screw_boss_r = 4.0
screw_hole_d = 2.5
standoff_h = 4.0
standoff_r = 2.5
standoff_hole_d = 2.0
vent_slot_l = 15.0
vent_slot_w = 1.5
vent_spacing = 3.5
cable_d = 8.0

# ═══ COORDINATE REFERENCE ═══
left_x = -body_x / 2
right_x = body_x / 2
front_y = -body_y / 2
back_y = body_y / 2
bottom_z = 0
top_z = body_z

# ═══ MAIN BODY ═══
body = cq.Workplane("XY").box(body_x, body_y, body_z, centered=(True, True, False))
try:
    body = body.edges("|Z").fillet(min(corner_r, min(body_x, body_y) * 0.15))
except:
    pass
body = body.faces(">Z").shell(-wall)

# ═══ SCREW BOSSES (4 corners) ═══
boss_inset_x = body_x / 2 - wall - screw_boss_r - 1
boss_inset_y = body_y / 2 - wall - screw_boss_r - 1
for bx, by in [(boss_inset_x, boss_inset_y), (-boss_inset_x, boss_inset_y),
               (boss_inset_x, -boss_inset_y), (-boss_inset_x, -boss_inset_y)]:
    boss = cq.Workplane("XY").cylinder(body_z - wall, screw_boss_r)
    boss = boss.translate((bx, by, (body_z - wall) / 2))
    body = body.union(boss)
    hole = cq.Workplane("XY").cylinder(body_z, screw_hole_d / 2)
    hole = hole.translate((bx, by, body_z / 2))
    body = body.cut(hole)

# ═══ PCB STANDOFFS (4 positions) ═══
pcb_inset_x = body_x / 2 - wall - 12
pcb_inset_y = body_y / 2 - wall - 10
for sx, sy in [(pcb_inset_x, pcb_inset_y), (-pcb_inset_x, pcb_inset_y),
               (pcb_inset_x, -pcb_inset_y), (-pcb_inset_x, -pcb_inset_y)]:
    standoff = cq.Workplane("XY").cylinder(standoff_h, standoff_r)
    standoff = standoff.translate((sx, sy, wall + standoff_h / 2))
    body = body.union(standoff)
    shole = cq.Workplane("XY").cylinder(standoff_h + 1, standoff_hole_d / 2)
    shole = shole.translate((sx, sy, wall + standoff_h / 2))
    body = body.cut(shole)

# ═══ VENTILATION SLOTS (side) ═══
num_vents = 5
vent_start_z = body_z * 0.3
for i in range(num_vents):
    vent = cq.Workplane("YZ").slot2D(vent_slot_l, vent_slot_w).extrude(wall * 3)
    vent = vent.translate((right_x, 0, vent_start_z + i * vent_spacing))
    body = body.cut(vent)

# ═══ CABLE ENTRY (back) ═══
cable_hole = cq.Workplane("XZ").cylinder(wall * 3, cable_d / 2)
cable_hole = cable_hole.translate((0, back_y, body_z * 0.3))
body = body.cut(cable_hole)

# ═══ LID LIP ═══
lip = cq.Workplane("XY").box(
    body_x - wall * 2 - 0.4, body_y - wall * 2 - 0.4, lid_lip,
    centered=(True, True, False)
).translate((0, 0, body_z - lid_lip))
body = body.union(lip)

# ═══ LABEL RECESS (bottom) ═══
label_w, label_d, label_depth = 40.0, 20.0, 0.5
label = cq.Workplane("XY").box(label_w, label_d, label_depth, centered=(True, True, False))
label = label.translate((0, 0, -label_depth + 0.01))
body = body.cut(label)

# ═══ RUBBER FEET ═══
foot_r, foot_h = 4.0, 1.5
foot_inset = 12.0
for fx, fy in [(body_x/2 - foot_inset, body_y/2 - foot_inset),
               (-body_x/2 + foot_inset, body_y/2 - foot_inset),
               (body_x/2 - foot_inset, -body_y/2 + foot_inset),
               (-body_x/2 + foot_inset, -body_y/2 + foot_inset)]:
    foot = cq.Workplane("XY").cylinder(foot_h, foot_r)
    foot = foot.translate((fx, fy, -foot_h / 2))
    body = body.union(foot)

result = body
"""
    },

    # ═══════════════════════════════════════════════════════════════
    # MUG — revolve profile
    # ═══════════════════════════════════════════════════════════════
    "mug": {
        "keywords": ["mug", "coffee mug", "cup", "coffee cup", "tea cup", "tea mug", "travel mug"],
        "category": "Drinkware",
        "description": "Cylindrical mug with smooth profile via revolve, handle via sweep.",
        "code": """import cadquery as cq
import math

# ═══ PARAMETERS ═══
base_r = 38.0     # base radius
top_r = 40.0      # top/rim radius
body_h = 95.0     # total height
wall = 3.0        # wall thickness
handle_w = 25.0   # handle width (distance from body)
handle_h = 50.0   # handle height span
handle_t = 8.0    # handle tube diameter

# ═══ OUTER BODY (revolve) ═══
outer = (
    cq.Workplane("XZ")
    .moveTo(0, 0)
    .lineTo(base_r, 0)
    .lineTo(base_r + 1, body_h * 0.05)
    .lineTo(top_r, body_h * 0.85)
    .lineTo(top_r, body_h)
    .lineTo(0, body_h)
    .close()
    .revolve(360, (0, 0, 0), (0, 1, 0))
)

# ═══ INNER CAVITY ═══
inner_base_r = base_r - wall
inner_top_r = top_r - wall
inner = (
    cq.Workplane("XZ")
    .moveTo(0, wall)
    .lineTo(inner_base_r, wall)
    .lineTo(inner_base_r + 1, wall + body_h * 0.05)
    .lineTo(inner_top_r, body_h * 0.85)
    .lineTo(inner_top_r, body_h + 0.1)
    .lineTo(0, body_h + 0.1)
    .close()
    .revolve(360, (0, 0, 0), (0, 1, 0))
)
body = outer.cut(inner)

# ═══ HANDLE (sweep arc) ═══
handle_center_z = body_h * 0.55
handle_path = (
    cq.Workplane("XZ")
    .moveTo(top_r, handle_center_z + handle_h / 2)
    .threePointArc((top_r + handle_w, handle_center_z), (top_r, handle_center_z - handle_h / 2))
)
handle_profile = (
    cq.Workplane("YZ")
    .center(top_r, handle_center_z + handle_h / 2)
    .circle(handle_t / 2)
)
try:
    handle = handle_profile.sweep(handle_path)
    body = body.union(handle)
except:
    pass

# ═══ BOTTOM RECESS ═══
recess = cq.Workplane("XY").cylinder(1.5, base_r - 5)
recess = recess.translate((0, 0, -0.75))
body = body.cut(recess)

result = body
"""
    },

    # ═══════════════════════════════════════════════════════════════
    # DESK ORGANIZER — box + compartments
    # ═══════════════════════════════════════════════════════════════
    "desk_organizer": {
        "keywords": ["desk organizer", "pen holder", "desk caddy", "office organizer", "pencil holder", "stationery holder", "desk tidy"],
        "category": "Desk Accessories",
        "description": "Multi-compartment desk organizer with pen slots, phone stand, card holder.",
        "code": """import cadquery as cq
import math

# ═══ PARAMETERS ═══
body_x = 250.0    # total width
body_y = 120.0    # total depth
body_z = 100.0    # total height (tallest section)
wall = 3.0        # wall thickness
corner_r = 5.0    # corner fillet
pen_section_x = 60.0
pen_section_z = 100.0
card_section_x = 80.0
card_section_z = 30.0
phone_section_x = 80.0
phone_angle = 70.0  # phone lean angle in degrees
pen_hole_d = 12.0
pen_hole_depth = 80.0

# ═══ COORDINATE REFERENCE ═══
left_x = -body_x / 2
right_x = body_x / 2

# ═══ BASE PLATFORM ═══
base_h = 5.0
base = cq.Workplane("XY").box(body_x, body_y, base_h, centered=(True, True, False))
try:
    base = base.edges("|Z").fillet(min(corner_r, body_y * 0.1))
except:
    pass

# ═══ PEN/PENCIL SECTION (left) ═══
pen_x_center = left_x + pen_section_x / 2 + wall
pen_block = cq.Workplane("XY").box(pen_section_x, body_y - wall * 2, pen_section_z, centered=(True, True, False))
pen_block = pen_block.translate((pen_x_center, 0, base_h))

# Hollow it out
pen_inner = cq.Workplane("XY").box(
    pen_section_x - wall * 2, body_y - wall * 4, pen_section_z - wall,
    centered=(True, True, False)
).translate((pen_x_center, 0, base_h + wall))
pen_block = pen_block.cut(pen_inner)

base = base.union(pen_block)

# Pen holes (circular) in the top
for i in range(3):
    for j in range(2):
        hx = pen_x_center - 15 + i * 15
        hy = -12 + j * 24
        hole = cq.Workplane("XY").cylinder(wall + 1, pen_hole_d / 2)
        hole = hole.translate((hx, hy, base_h + pen_section_z - wall))
        base = base.cut(hole)

# ═══ CARD/NOTE SECTION (center) ═══
card_x_center = pen_x_center + pen_section_x / 2 + card_section_x / 2 + wall
card_block = cq.Workplane("XY").box(card_section_x, body_y - wall * 2, card_section_z, centered=(True, True, False))
card_block = card_block.translate((card_x_center, 0, base_h))

card_inner = cq.Workplane("XY").box(
    card_section_x - wall * 2, body_y - wall * 4, card_section_z + 1,
    centered=(True, True, False)
).translate((card_x_center, 0, base_h + wall))
card_block = card_block.cut(card_inner)

base = base.union(card_block)

# ═══ PHONE STAND SECTION (right) ═══
phone_x_center = card_x_center + card_section_x / 2 + phone_section_x / 2 + wall
phone_back_h = 70.0
phone_back = cq.Workplane("XY").box(phone_section_x, wall * 2, phone_back_h, centered=(True, True, False))
phone_back = phone_back.translate((phone_x_center, body_y / 2 - wall * 3, base_h))
base = base.union(phone_back)

# Phone ledge
ledge_d = 20.0
ledge_h = 8.0
phone_ledge = cq.Workplane("XY").box(phone_section_x, ledge_d, ledge_h, centered=(True, True, False))
phone_ledge = phone_ledge.translate((phone_x_center, body_y / 2 - wall * 3 - ledge_d / 2, base_h))
base = base.union(phone_ledge)

# ═══ RUBBER FEET ═══
foot_r = 5.0
foot_h = 2.0
foot_inset = 15.0
for fx, fy in [(left_x + foot_inset, body_y / 2 - foot_inset),
               (right_x - foot_inset, body_y / 2 - foot_inset),
               (left_x + foot_inset, -body_y / 2 + foot_inset),
               (right_x - foot_inset, -body_y / 2 + foot_inset)]:
    foot = cq.Workplane("XY").cylinder(foot_h, foot_r)
    foot = foot.translate((fx, fy, -foot_h / 2))
    base = base.union(foot)

# ═══ EDGE FILLETS ═══
try:
    base = base.edges().fillet(min(1.5, wall * 0.3))
except:
    pass

result = base
"""
    },

    # ═══════════════════════════════════════════════════════════════
    # BOTTLE — revolve with spline profile
    # ═══════════════════════════════════════════════════════════════
    "bottle": {
        "keywords": ["bottle", "water bottle", "drink bottle", "thermos", "flask", "tumbler"],
        "category": "Drinkware",
        "description": "Water bottle with smooth revolved body, threaded neck, and base.",
        "code": """import cadquery as cq
import math

# ═══ PARAMETERS ═══
base_r = 35.0     # bottom radius
body_r = 33.0     # main body radius
neck_r = 14.0     # neck opening radius
body_h = 230.0    # total height
wall = 2.5        # wall thickness
neck_h = 20.0     # neck height

# ═══ OUTER PROFILE ═══
outer = (
    cq.Workplane("XZ")
    .moveTo(0, 0)
    .lineTo(base_r, 0)
    .lineTo(base_r, 3)
    .lineTo(body_r, body_h * 0.08)
    .lineTo(body_r, body_h * 0.7)
    .lineTo(neck_r + 8, body_h * 0.88)
    .lineTo(neck_r, body_h - neck_h)
    .lineTo(neck_r, body_h)
    .lineTo(0, body_h)
    .close()
    .revolve(360, (0, 0, 0), (0, 1, 0))
)

# ═══ INNER CAVITY ═══
inner = (
    cq.Workplane("XZ")
    .moveTo(0, wall)
    .lineTo(base_r - wall, wall)
    .lineTo(body_r - wall, body_h * 0.08)
    .lineTo(body_r - wall, body_h * 0.7)
    .lineTo(neck_r - wall + 8, body_h * 0.88)
    .lineTo(neck_r - wall, body_h - neck_h)
    .lineTo(neck_r - wall, body_h + 0.1)
    .lineTo(0, body_h + 0.1)
    .close()
    .revolve(360, (0, 0, 0), (0, 1, 0))
)
body = outer.cut(inner)

# ═══ THREAD RINGS on neck ═══
thread_pitch = 3.0
num_threads = int(neck_h / thread_pitch)
for i in range(num_threads):
    tz = body_h - neck_h + i * thread_pitch + thread_pitch / 2
    ring = cq.Workplane("XY").cylinder(thread_pitch * 0.4, neck_r + 1.0)
    ring_inner = cq.Workplane("XY").cylinder(thread_pitch * 0.5, neck_r - 0.1)
    ring = ring.cut(ring_inner)
    ring = ring.translate((0, 0, tz))
    body = body.union(ring)

# ═══ BASE INDENT ═══
indent = cq.Workplane("XY").cylinder(2.0, base_r - 5)
indent = indent.translate((0, 0, -1.0))
body = body.cut(indent)

result = body
"""
    },

    # ═══════════════════════════════════════════════════════════════
    # BRACKET/MOUNT — profile extrude + holes
    # ═══════════════════════════════════════════════════════════════
    "bracket": {
        "keywords": ["bracket", "mount", "wall mount", "shelf bracket", "L bracket", "angle bracket", "mounting bracket", "holder"],
        "category": "Hardware",
        "description": "L-shaped mounting bracket with screw holes and reinforcement rib.",
        "code": """import cadquery as cq
import math

# ═══ PARAMETERS ═══
arm_h = 80.0       # vertical arm height
arm_w = 60.0       # horizontal arm length
thickness = 4.0    # material thickness
depth = 40.0       # bracket depth (extrusion)
hole_d = 5.0       # mounting hole diameter
fillet_r = 1.0     # edge fillet
rib_thickness = 3.0

# ═══ L-PROFILE (simple right-angle, no arc) ═══
body = (
    cq.Workplane("XZ")
    .moveTo(0, 0)
    .lineTo(arm_w, 0)
    .lineTo(arm_w, thickness)
    .lineTo(thickness, thickness)
    .lineTo(thickness, arm_h)
    .lineTo(0, arm_h)
    .close()
    .extrude(depth)
)

# Center in Y
body = body.translate((0, -depth / 2, 0))

# ═══ MOUNTING HOLES (vertical arm) ═══
hole_spacing = (arm_h - thickness - 20) / 2
for i in range(3):
    hz = thickness + 10 + i * hole_spacing
    hole = cq.Workplane("YZ").cylinder(thickness + 1, hole_d / 2)
    hole = hole.translate((thickness / 2, 0, hz))
    body = body.cut(hole)

# ═══ MOUNTING HOLES (horizontal arm) ═══
h_hole_spacing = (arm_w - thickness - 15) / 2
for i in range(2):
    hx = thickness + 8 + i * h_hole_spacing
    hole = cq.Workplane("XY").cylinder(thickness + 1, hole_d / 2)
    hole = hole.translate((hx, 0, thickness / 2))
    body = body.cut(hole)

# ═══ REINFORCEMENT RIB (diagonal) ═══
rib_h = min(arm_h, arm_w) * 0.5
rib = (
    cq.Workplane("XZ")
    .moveTo(thickness, thickness)
    .lineTo(thickness + rib_h * 0.7, thickness)
    .lineTo(thickness, thickness + rib_h * 0.7)
    .close()
    .extrude(rib_thickness)
)
rib = rib.translate((0, -rib_thickness / 2, 0))
body = body.union(rib)

# ═══ EDGE FILLETS ═══
try:
    body = body.edges().fillet(min(fillet_r, thickness * 0.2))
except:
    pass

result = body
"""
    },

    # ═══════════════════════════════════════════════════════════════
    # GEAR — polygon approximation
    # ═══════════════════════════════════════════════════════════════
    "gear": {
        "keywords": ["gear", "spur gear", "cog", "cogwheel", "gear wheel", "pinion"],
        "category": "Mechanical",
        "description": "Spur gear with involute-approximated teeth, center bore, and keyway.",
        "code": """import cadquery as cq
import math

# ═══ PARAMETERS ═══
module_val = 2.0       # gear module (tooth size)
num_teeth = 20         # number of teeth
face_width = 10.0      # gear thickness
bore_d = 8.0           # center bore diameter
hub_d = 16.0           # hub diameter
hub_h = 5.0            # hub extension height
keyway_w = 3.0         # keyway width
keyway_d = 1.5         # keyway depth
pressure_angle = 20.0  # degrees

# ═══ DERIVED DIMENSIONS ═══
pitch_r = module_val * num_teeth / 2.0
outer_r = pitch_r + module_val
root_r = pitch_r - 1.25 * module_val
tooth_angle = 360.0 / num_teeth

# ═══ GEAR BLANK (cylinder) ═══
gear = cq.Workplane("XY").cylinder(face_width, outer_r, centered=(True, True, False))

# ═══ TOOTH VALLEYS (cut between teeth) ═══
for i in range(num_teeth):
    angle = i * tooth_angle + tooth_angle / 2
    rad = math.radians(angle)

    # Valley cutter — approximate with angled box
    valley_w = module_val * 0.8
    valley_depth = outer_r - root_r
    cutter = cq.Workplane("XY").box(valley_w, valley_depth + 2, face_width + 1, centered=(True, True, False))
    cutter = cutter.translate((0, 0, -0.5))

    # Rotate and position at the correct angle on the pitch circle
    cutter = cutter.translate((0, outer_r - valley_depth / 2, 0))
    cutter = cutter.rotate((0, 0, 0), (0, 0, 1), angle)
    gear = gear.cut(cutter)

# ═══ CENTER BORE ═══
bore = cq.Workplane("XY").cylinder(face_width + hub_h + 1, bore_d / 2)
bore = bore.translate((0, 0, (face_width + hub_h) / 2 - 0.5))
gear = gear.cut(bore)

# ═══ HUB (extended boss) ═══
hub = cq.Workplane("XY").cylinder(hub_h, hub_d / 2, centered=(True, True, False))
hub = hub.translate((0, 0, face_width))
gear = gear.union(hub)

# Re-cut bore through hub
bore2 = cq.Workplane("XY").cylinder(face_width + hub_h + 1, bore_d / 2)
bore2 = bore2.translate((0, 0, (face_width + hub_h) / 2))
gear = gear.cut(bore2)

# ═══ KEYWAY ═══
keyway = cq.Workplane("XY").box(keyway_w, bore_d, face_width + hub_h + 1, centered=(True, True, False))
keyway = keyway.translate((-keyway_w / 2, bore_d / 2 - keyway_d, -0.5))
gear = gear.cut(keyway)

# ═══ CHAMFER TOP EDGES ═══
try:
    gear = gear.faces(">Z").edges().chamfer(min(0.5, face_width * 0.05))
except:
    pass

result = gear
"""
    },

    # ═══════════════════════════════════════════════════════════════
    # SIMPLE BOX/CONTAINER — beginner pattern
    # ═══════════════════════════════════════════════════════════════
    "storage_box": {
        "keywords": ["box", "storage box", "container", "bin", "tray", "organizer box", "toolbox", "simple box"],
        "category": "Storage",
        "description": "Simple storage box with lid, dividers, and handle.",
        "code": """import cadquery as cq
import math

# ═══ PARAMETERS ═══
body_x = 200.0    # width
body_y = 150.0    # depth
body_z = 80.0     # height
wall = 3.0        # wall thickness
corner_r = 5.0    # corner fillet
divider_count = 2 # number of internal dividers
handle_w = 80.0   # handle width
handle_h = 15.0   # handle arch height
handle_t = 6.0    # handle thickness

# ═══ COORDINATE REFERENCE ═══
left_x = -body_x / 2
right_x = body_x / 2
front_y = -body_y / 2
back_y = body_y / 2

# ═══ MAIN BOX ═══
body = cq.Workplane("XY").box(body_x, body_y, body_z, centered=(True, True, False))
try:
    body = body.edges("|Z").fillet(min(corner_r, min(body_x, body_y) * 0.1))
except:
    pass
body = body.faces(">Z").shell(-wall)

# ═══ INTERNAL DIVIDERS ═══
if divider_count > 0:
    spacing = body_x / (divider_count + 1)
    for i in range(1, divider_count + 1):
        dx = left_x + i * spacing
        divider = cq.Workplane("XY").box(wall, body_y - wall * 4, body_z - wall * 2, centered=(True, True, False))
        divider = divider.translate((dx, 0, wall))
        body = body.union(divider)

# ═══ HANDLE ═══
handle_base = cq.Workplane("XY").box(handle_w, handle_t, handle_h + handle_t, centered=(True, True, False))
handle_base = handle_base.translate((0, 0, body_z))

# Cut the arch opening
arch = cq.Workplane("XZ").slot2D(handle_w - handle_t * 2, handle_h * 2).extrude(handle_t + 1)
arch = arch.translate((0, 0, body_z + handle_t))
handle_base = handle_base.cut(arch)

body = body.union(handle_base)

# ═══ GRIP INDENT (sides) ═══
grip_w = body_x * 0.3
grip_h = body_z * 0.3
grip_depth = 1.5
for side_y in [front_y, back_y]:
    grip = cq.Workplane("XZ").slot2D(grip_w, grip_h).extrude(grip_depth)
    dir_sign = 1 if side_y > 0 else -1
    grip = grip.translate((0, side_y + dir_sign * grip_depth / 2, body_z * 0.5))
    body = body.cut(grip)

# ═══ RUBBER FEET ═══
foot_r = 5.0
foot_h = 2.0
foot_inset = 15.0
for fx, fy in [(right_x - foot_inset, back_y - foot_inset),
               (left_x + foot_inset, back_y - foot_inset),
               (right_x - foot_inset, front_y + foot_inset),
               (left_x + foot_inset, front_y + foot_inset)]:
    foot = cq.Workplane("XY").cylinder(foot_h, foot_r)
    foot = foot.translate((fx, fy, -foot_h / 2))
    body = body.union(foot)

# ═══ EDGE FILLETS ═══
try:
    body = body.edges().fillet(min(1.0, wall * 0.25))
except:
    pass

result = body
"""
    },

    # ═══════════════════════════════════════════════════════════════
    # LAMP — revolve base + shade
    # ═══════════════════════════════════════════════════════════════
    "lamp": {
        "keywords": ["lamp", "desk lamp", "table lamp", "bedside lamp", "lampshade", "light"],
        "category": "Home",
        "description": "Table lamp with weighted base, stem, and conical shade.",
        "code": """import cadquery as cq
import math

# ═══ PARAMETERS ═══
base_r = 75.0      # base radius
base_h = 15.0      # base height
stem_r = 8.0       # stem radius
stem_h = 280.0     # stem height
shade_top_r = 60.0 # shade top radius
shade_bot_r = 125.0 # shade bottom radius
shade_h = 160.0    # shade height
shade_wall = 2.0   # shade wall thickness
bulb_r = 25.0      # bulb socket radius

# ═══ BASE (weighted, revolved profile) ═══
base = (
    cq.Workplane("XZ")
    .moveTo(0, 0)
    .lineTo(base_r, 0)
    .spline([(base_r, base_h * 0.3), (base_r - 5, base_h * 0.7), (stem_r + 10, base_h)])
    .lineTo(stem_r, base_h)
    .lineTo(0, base_h)
    .close()
    .revolve(360, (0, 0, 0), (0, 1, 0))
)

# Base indent (bottom)
indent = cq.Workplane("XY").cylinder(3.0, base_r - 10)
indent = indent.translate((0, 0, -1.5))
base = base.cut(indent)

# Cable channel in base
cable = cq.Workplane("XY").cylinder(base_h + 1, 3.0)
cable = cable.translate((0, 0, base_h / 2))
base = base.cut(cable)

# ═══ STEM (cylinder) ═══
stem = cq.Workplane("XY").cylinder(stem_h, stem_r, centered=(True, True, False))
stem = stem.translate((0, 0, base_h))
base = base.union(stem)

# Wire channel through stem
wire = cq.Workplane("XY").cylinder(stem_h + 1, 2.5)
wire = wire.translate((0, 0, base_h + stem_h / 2))
base = base.cut(wire)

# ═══ SHADE (conical shell) ═══
shade_z = base_h + stem_h - shade_h * 0.3  # shade overlaps stem top

# Outer cone
shade_outer = (
    cq.Workplane("XZ")
    .moveTo(0, 0)
    .lineTo(shade_bot_r, 0)
    .lineTo(shade_top_r, shade_h)
    .lineTo(0, shade_h)
    .close()
    .revolve(360, (0, 0, 0), (0, 1, 0))
)

# Inner cone
shade_inner = (
    cq.Workplane("XZ")
    .moveTo(0, shade_wall)
    .lineTo(shade_bot_r - shade_wall, shade_wall)
    .lineTo(shade_top_r - shade_wall, shade_h - shade_wall)
    .lineTo(0, shade_h - shade_wall)
    .close()
    .revolve(360, (0, 0, 0), (0, 1, 0))
)
shade = shade_outer.cut(shade_inner)
shade = shade.translate((0, 0, shade_z))
base = base.union(shade)

# ═══ BULB SOCKET (inside shade) ═══
socket = cq.Workplane("XY").cylinder(30.0, bulb_r / 2, centered=(True, True, False))
socket = socket.translate((0, 0, shade_z + shade_h * 0.4))
base = base.union(socket)

# ═══ SWITCH BUMP on base ═══
switch = cq.Workplane("XY").cylinder(3.0, 6.0)
switch = switch.translate((base_r - 15, 0, base_h * 0.5))
base = base.union(switch)

result = base
"""
    },

    # ═══════════════════════════════════════════════════════════════
    # QUADCOPTER DRONE — additive assembly
    # ═══════════════════════════════════════════════════════════════
    "drone_quadcopter": {
        "keywords": ["drone", "quadcopter", "quad", "uav", "flying", "dji", "fpv drone", "racing drone"],
        "category": "Drones & RC",
        "description": "Quadcopter with center body, 4 arms, motors, propellers, canopy, and landing gear.",
        "code": """import cadquery as cq
import math

# ═══ PARAMETERS ═══
body_x = 80.0      # center body width
body_y = 80.0      # center body depth
body_z = 25.0      # center body height
arm_length = 120.0  # arm length from center
arm_w = 15.0       # arm width
arm_h = 8.0        # arm thickness
motor_r = 12.0     # motor radius
motor_h = 15.0     # motor height
prop_r = 63.0      # propeller radius (5 inch)
prop_h = 2.0       # propeller thickness
canopy_r = 35.0    # canopy dome radius
canopy_h = 20.0    # canopy height
leg_h = 40.0       # landing gear height
leg_r = 4.0        # landing gear tube radius
leg_spread = 1.2   # gear spread factor

# ═══ CENTER BODY ═══
body = cq.Workplane("XY").box(body_x, body_y, body_z, centered=(True, True, False))
try:
    body = body.edges("|Z").fillet(min(8.0, body_x * 0.1))
except:
    pass

# ═══ ARMS (4 at 45°, 135°, 225°, 315°) ═══
arm_angles = [45, 135, 225, 315]
motor_positions = []

for angle in arm_angles:
    rad = math.radians(angle)

    # Arm
    arm = cq.Workplane("XY").box(arm_length, arm_w, arm_h, centered=(True, True, False))
    arm = arm.translate((0, 0, body_z / 2 - arm_h / 2))
    arm = arm.rotate((0, 0, 0), (0, 0, 1), angle)

    body = body.union(arm)

    # Motor position (at arm tip)
    mx = (arm_length / 2) * math.cos(rad)
    my = (arm_length / 2) * math.sin(rad)
    motor_positions.append((mx, my))

    # Motor cylinder
    motor = cq.Workplane("XY").cylinder(motor_h, motor_r, centered=(True, True, False))
    motor = motor.translate((mx, my, body_z / 2 + arm_h / 2 - 1))
    body = body.union(motor)

    # Propeller disc
    prop = cq.Workplane("XY").cylinder(prop_h, prop_r, centered=(True, True, False))
    prop = prop.translate((mx, my, body_z / 2 + arm_h / 2 + motor_h - 1))
    body = body.union(prop)

# ═══ CANOPY (dome on top) ═══
canopy = cq.Workplane("XY").cylinder(canopy_h, canopy_r, centered=(True, True, False))
canopy = canopy.translate((0, 0, body_z))
# Round the top
try:
    canopy = canopy.faces(">Z").fillet(min(canopy_r * 0.8, canopy_h * 0.6))
except:
    pass
body = body.union(canopy)

# ═══ BATTERY BAY (bottom recess) ═══
bay_x = body_x * 0.6
bay_y = body_y * 0.8
bay_h = 5.0
bay = cq.Workplane("XY").box(bay_x, bay_y, bay_h, centered=(True, True, False))
bay = bay.translate((0, 0, -0.01))
body = body.cut(bay)

# ═══ LANDING GEAR (4 legs) ═══
gear_positions = [(body_x/2 * leg_spread, body_y/2 * leg_spread),
                  (-body_x/2 * leg_spread, body_y/2 * leg_spread),
                  (body_x/2 * leg_spread, -body_y/2 * leg_spread),
                  (-body_x/2 * leg_spread, -body_y/2 * leg_spread)]

for gx, gy in gear_positions:
    leg = cq.Workplane("XY").cylinder(leg_h, leg_r, centered=(True, True, False))
    leg = leg.translate((gx, gy, -leg_h))
    body = body.union(leg)

# Cross bar connecting front legs
crossbar_front = cq.Workplane("XY").box(body_x * leg_spread * 2 + leg_r * 2, leg_r * 2, leg_r * 2, centered=(True, True, False))
crossbar_front = crossbar_front.translate((0, body_y/2 * leg_spread, -leg_h))
body = body.union(crossbar_front)

crossbar_back = cq.Workplane("XY").box(body_x * leg_spread * 2 + leg_r * 2, leg_r * 2, leg_r * 2, centered=(True, True, False))
crossbar_back = crossbar_back.translate((0, -body_y/2 * leg_spread, -leg_h))
body = body.union(crossbar_back)

# ═══ CAMERA MOUNT (front, under body) ═══
cam_mount = cq.Workplane("XY").box(20, 15, 10, centered=(True, True, False))
cam_mount = cam_mount.translate((0, body_y / 2 - 5, -10))
body = body.union(cam_mount)

# Camera lens
cam_lens = cq.Workplane("XZ").cylinder(15 + 1, 5)
cam_lens = cam_lens.translate((0, body_y / 2 + 1, -5))
body = body.cut(cam_lens)

result = body
"""
    },

    # ═══════════════════════════════════════════════════════════════
    # VASE — revolve with decorative profile
    # ═══════════════════════════════════════════════════════════════
    "vase": {
        "keywords": ["vase", "flower vase", "decorative vase", "flower pot", "planter"],
        "category": "Home Decor",
        "description": "Decorative vase with hourglass shape via revolve and lineTo profile.",
        "code": """import cadquery as cq
import math

# ═══ PARAMETERS ═══
base_r = 40.0      # base radius
waist_r = 28.0     # narrowest point
body_r = 55.0      # widest point
top_r = 35.0       # opening radius
body_h = 250.0     # total height
wall = 3.5         # wall thickness
lip_h = 5.0        # rim lip height
foot_h = 8.0       # base foot height

# ═══ OUTER PROFILE ═══
outer = (
    cq.Workplane("XZ")
    .moveTo(0, 0)
    .lineTo(base_r - 5, 0)
    .lineTo(base_r, foot_h)
    .lineTo(base_r + 2, body_h * 0.1)
    .lineTo(waist_r, body_h * 0.35)
    .lineTo(body_r, body_h * 0.6)
    .lineTo(body_r - 5, body_h * 0.8)
    .lineTo(top_r + 3, body_h * 0.92)
    .lineTo(top_r, body_h - lip_h)
    .lineTo(top_r + 2, body_h)
    .lineTo(0, body_h)
    .close()
    .revolve(360, (0, 0, 0), (0, 1, 0))
)

# ═══ INNER CAVITY ═══
inner = (
    cq.Workplane("XZ")
    .moveTo(0, wall + foot_h)
    .lineTo(base_r - wall - 5, wall + foot_h)
    .lineTo(base_r - wall + 2, body_h * 0.1)
    .lineTo(waist_r - wall, body_h * 0.35)
    .lineTo(body_r - wall, body_h * 0.6)
    .lineTo(body_r - wall - 5, body_h * 0.8)
    .lineTo(top_r - wall + 3, body_h * 0.92)
    .lineTo(top_r - wall, body_h - lip_h)
    .lineTo(top_r - wall + 2, body_h + 0.1)
    .lineTo(0, body_h + 0.1)
    .close()
    .revolve(360, (0, 0, 0), (0, 1, 0))
)
body = outer.cut(inner)

# ═══ DECORATIVE RINGS ═══
for ring_z_frac in [0.25, 0.45, 0.75]:
    rz = body_h * ring_z_frac
    t = ring_z_frac
    if t < 0.35:
        local_r = base_r + (waist_r - base_r) * (t / 0.35)
    elif t < 0.6:
        local_r = waist_r + (body_r - waist_r) * ((t - 0.35) / 0.25)
    else:
        local_r = body_r + (top_r - body_r) * ((t - 0.6) / 0.4)

    ring = cq.Workplane("XY").cylinder(1.5, local_r + 1.5)
    ring_inner = cq.Workplane("XY").cylinder(2.0, local_r - 0.5)
    ring = ring.cut(ring_inner)
    ring = ring.translate((0, 0, rz))
    body = body.union(ring)

result = body
"""
    },

    # ═══════════════════════════════════════════════════════════════
    # STAND/DOCK — phone/tablet stand
    # ═══════════════════════════════════════════════════════════════
    "stand": {
        "keywords": ["stand", "phone stand", "tablet stand", "dock", "charging dock", "display stand", "laptop stand", "ipad stand"],
        "category": "Desk Accessories",
        "description": "Angled stand/dock with cable routing and anti-slip pads.",
        "code": """import cadquery as cq
import math

# ═══ PARAMETERS ═══
base_x = 100.0     # base width
base_y = 80.0      # base depth
base_h = 8.0       # base height
back_h = 120.0     # back support height
back_t = 5.0       # back support thickness
lean_angle = 75.0   # device lean angle (degrees from horizontal)
ledge_d = 15.0     # front ledge depth
ledge_h = 10.0     # front ledge height
cable_d = 10.0     # cable routing hole diameter
grip_depth = 1.0   # anti-slip groove depth

# ═══ BASE ═══
body = cq.Workplane("XY").box(base_x, base_y, base_h, centered=(True, True, False))
try:
    body = body.edges("|Z").fillet(min(5.0, base_x * 0.05))
except:
    pass

# ═══ BACK SUPPORT (angled) ═══
# Create angled back plate
back = cq.Workplane("XY").box(base_x - 10, back_t, back_h, centered=(True, True, False))
back = back.translate((0, base_y / 2 - back_t - 2, base_h))

# Tilt it to lean_angle
tilt = 90 - lean_angle
back = back.rotate((0, base_y / 2 - back_t - 2, base_h), (1, 0, 0), -tilt)

body = body.union(back)

# ═══ FRONT LEDGE (holds bottom of device) ═══
ledge = cq.Workplane("XY").box(base_x - 10, ledge_d, ledge_h, centered=(True, True, False))
ledge = ledge.translate((0, -base_y / 2 + ledge_d / 2, base_h))
body = body.union(ledge)

# Ledge slot (device sits in this groove)
slot = cq.Workplane("XY").box(base_x - 20, 4.0, ledge_h + 1, centered=(True, True, False))
slot = slot.translate((0, -base_y / 2 + ledge_d / 2 + 2, base_h + 3))
body = body.cut(slot)

# ═══ CABLE ROUTING HOLE ═══
cable_hole = cq.Workplane("XZ").cylinder(base_h + 1, cable_d / 2)
cable_hole = cable_hole.translate((0, 0, base_h / 2))
body = body.cut(cable_hole)

# ═══ ANTI-SLIP BOTTOM ═══
for i in range(3):
    groove = cq.Workplane("XY").box(base_x * 0.7, 2.0, grip_depth + 0.1, centered=(True, True, False))
    groove = groove.translate((0, -base_y * 0.3 + i * base_y * 0.3, -0.05))
    body = body.cut(groove)

# ═══ RUBBER FEET ═══
foot_r = 5.0
foot_h = 2.0
for fx, fy in [(base_x/2 - 12, base_y/2 - 12),
               (-base_x/2 + 12, base_y/2 - 12),
               (base_x/2 - 12, -base_y/2 + 12),
               (-base_x/2 + 12, -base_y/2 + 12)]:
    foot = cq.Workplane("XY").cylinder(foot_h, foot_r)
    foot = foot.translate((fx, fy, -foot_h / 2))
    body = body.union(foot)

result = body
"""
    }
}


# ═══════════════════════════════════════════════════════════════════════════
# CADQUERY TECHNIQUE REFERENCE — extracted from official CadQuery documentation
# Compact reference of patterns the AI should know for generating correct code.
# ═══════════════════════════════════════════════════════════════════════════

CADQUERY_TECHNIQUE_REFERENCE = """
═══ CADQUERY SELECTOR REFERENCE ═══
Face selectors (based on face normal direction):
  ">Z"  → topmost face        "<Z"  → bottommost face
  ">X"  → rightmost face      "<X"  → leftmost face
  ">Y"  → backmost face       "<Y"  → frontmost face
  "+Z"  → faces with normal in +Z direction
  "-Z"  → faces with normal in -Z direction
  "|Z"  → faces parallel to Z   "#Z" → faces perpendicular to Z
  "%Plane" → faces of type plane
  ">>Z[-2]" → 2nd farthest face in Z dir (CenterNthSelector)
  "<<Z[0]"  → closest face in Z dir

Edge selectors (based on edge direction):
  "|Z"  → edges parallel to Z axis
  "#Z"  → edges perpendicular to Z axis
  ">Z"  → topmost edges          "<Z"  → bottommost edges
  ">Z[1]" → 2nd closest edge in +Z (DirectionNthSelector)
  ">>Z[-2]" → 2nd farthest edge in Z (CenterNthSelector)

Combining selectors:
  "|Z and >Y"  → edges parallel to Z AND farthest in Y
  "not(<X or >X or <Y or >Y)" → exclude side edges
  ">(-1, 1, 0)" → user-defined direction vector

═══ WORKPLANE TECHNIQUES ═══
# Creating workplane on a face:
result = cq.Workplane("XY").box(10, 10, 10).faces(">Z").workplane().hole(5)

# Offset workplane (floating above/below a face):
result = cq.Workplane("front").box(3, 2, 0.5)
result = result.faces("<X").workplane(offset=0.75).circle(1.0).extrude(0.5)

# Rotated/transformed workplane:
result = (cq.Workplane("front").box(4.0, 4.0, 0.25)
    .faces(">Z").workplane()
    .transformed(offset=cq.Vector(0, -1.5, 1.0), rotate=cq.Vector(60, 0, 0))
    .rect(1.5, 1.5, forConstruction=True).vertices().hole(0.25))

# Tagging workplanes for later reuse:
result = (cq.Workplane("XY").box(10, 10, 10)
    .faces(">Z").workplane().tag("baseplane")
    .center(-3, 0).circle(1).extrude(3)
    .workplaneFromTagged("baseplane")
    .center(3, 0).circle(1).extrude(2))

# Copy workplane from another object:
result = (cq.Workplane("front").circle(1).extrude(10)
    .copyWorkplane(cq.Workplane("right", origin=(-5, 0, 0)))
    .circle(1).extrude(10))

═══ SHELLING (HOLLOW OBJECTS) ═══
# Shell inward (negative = hollow inside):
result = cq.Workplane("front").box(2, 2, 2).shell(-0.1)

# Shell with open top face:
result = cq.Workplane("front").box(2, 2, 2).faces("+Z").shell(0.1)

# Shell removing multiple faces:
result = cq.Workplane("front").box(2, 2, 2).faces("+Z or -X or +X").shell(0.1)

═══ LOFTING (SMOOTH TRANSITIONS BETWEEN PROFILES) ═══
# Loft from rectangle base to circle:
result = (cq.Workplane("front").box(4.0, 4.0, 0.25)
    .faces(">Z").circle(1.5)
    .workplane(offset=3.0).rect(0.75, 0.5)
    .loft(combine=True))

═══ CONSTRUCTION GEOMETRY ═══
# Use forConstruction=True to place features at vertices:
result = (cq.Workplane("front").box(2, 2, 0.5)
    .faces(">Z").workplane()
    .rect(1.5, 1.5, forConstruction=True).vertices().hole(0.125))

# Point lists for multiple features:
r = cq.Workplane("front").circle(2.0)
r = r.pushPoints([(1.5, 0), (0, 1.5), (-1.5, 0), (0, -1.5)])
r = r.circle(0.25)
result = r.extrude(0.125)

# Rectangular array:
s = (s.faces(">Z").workplane()
    .rarray(pitch, pitch, cols, rows, True)
    .circle(bumpDiam / 2.0).extrude(bumpHeight))

═══ PROFILES WITH LINES AND ARCS ═══
# Lines + three-point arc + close:
result = (cq.Workplane("front")
    .lineTo(2.0, 0).lineTo(2.0, 1.0)
    .threePointArc((1.0, 1.5), (0.0, 1.0))
    .close().extrude(0.25))

# Horizontal/vertical lines for easy coding:
r = cq.Workplane("front").hLine(1.0)
r = r.vLine(0.5).hLine(-0.25).vLine(-0.25).hLineTo(0.0)
result = r.mirrorY().extrude(0.25)

# Polyline for complex shapes:
pts = [(0, H/2.0), (W/2.0, H/2.0), (W/2.0, (H/2.0-t)),
       (t/2.0, (H/2.0-t)), (t/2.0, (t-H/2.0))]
result = cq.Workplane("front").polyline(pts).mirrorY().extrude(L)

═══ SPLINES ═══
s = cq.Workplane("XY")
sPnts = [(2.75, 1.5), (2.5, 1.75), (2.0, 1.5), (1.5, 1.0)]
r = s.lineTo(3.0, 0).lineTo(3.0, 1.0).spline(sPnts, includeCurrent=True).close()
result = r.extrude(0.5)

═══ MIRRORING ═══
# 2D mirror before extrude:
result = cq.Workplane("front").polyline(pts).mirrorY().extrude(L)

# 3D mirror about a plane:
result = result.mirror(mirrorPlane="XY", basePointVector=(0, 0, 30))

# Mirror from a selected face and union:
result = cq.Workplane("XY").line(0,1).line(1,0).line(0,-0.5).close().extrude(1)
result = result.mirror(result.faces(">X"), union=True)

═══ COUNTER-BORED & COUNTERSUNK HOLES ═══
result = (cq.Workplane(cq.Plane.XY()).box(4, 2, 0.5)
    .faces(">Z").workplane()
    .rect(3.5, 1.5, forConstruction=True).vertices()
    .cboreHole(0.125, 0.25, 0.125, depth=None))

═══ SPLITTING OBJECTS ═══
c = cq.Workplane("XY").box(1,1,1).faces(">Z").workplane().circle(0.25).cutThruAll()
result = c.faces(">Y").workplane(-0.5).split(keepTop=True)

═══ CLASSIC OCC BOTTLE (profile + arc + mirror + shell) ═══
(L, w, t) = (20.0, 6.0, 3.0)
s = cq.Workplane("XY")
p = (s.center(-L/2.0, 0).vLine(w/2.0)
    .threePointArc((L/2.0, w/2.0 + t), (L, w/2.0))
    .vLine(-w/2.0).mirrorX().extrude(30.0, True))
p = p.faces(">Z").workplane(centerOption="CenterOfMass").circle(3.0).extrude(2.0, True)
result = p.faces(">Z").shell(0.3)

═══ FILLET ORDERING (important!) ═══
# Fillet side edges BEFORE top/bottom edges to avoid geometry failures:
if p_sideRadius > p_topAndBottomRadius:
    oshell = oshell.edges("|Z").fillet(p_sideRadius)
    oshell = oshell.edges("#Z").fillet(p_topAndBottomRadius)
else:
    oshell = oshell.edges("#Z").fillet(p_topAndBottomRadius)
    oshell = oshell.edges("|Z").fillet(p_sideRadius)

═══ TAGGING FOR COMPLEX MULTI-FEATURE BUILDS ═══
result = (cq.Workplane("XY")
    .polygon(3, 5).extrude(4).tag("prism")
    .sphere(10)  # sphere obscures the prism
    .faces("<X", tag="prism").workplane().circle(1).cutThruAll()
    .faces(">X", tag="prism").faces(">Y").workplane().circle(1).cutThruAll())

═══ EXTRUDE UNTIL FACE ═══
result = (cq.Workplane(origin=(20, 0, 0)).circle(2)
    .revolve(180, (-20, 0, 0), (-20, -1, 0))
    .center(-20, 0).workplane().rect(20, 4)
    .extrude("next"))

═══ KEY 3D OPERATIONS REFERENCE ═══
Workplane.box(length, width, height, centered=(True,True,True))
Workplane.cylinder(height, radius)
Workplane.sphere(radius)
Workplane.hole(diameter, depth=None)
Workplane.cboreHole(diameter, cboreDiameter, cboreDepth, depth=None)
Workplane.cskHole(diameter, cskDiameter, cskAngle, depth=None)
Workplane.extrude(until, combine=True, taper=0)
Workplane.cutBlind(until, taper=0) — cut into solid
Workplane.cutThruAll() — cut completely through
Workplane.shell(thickness) — negative=inward, positive=outward
Workplane.fillet(radius) — round selected edges
Workplane.chamfer(length) — bevel selected edges
Workplane.loft(ruled=False, combine=True) — smooth between profiles
Workplane.sweep(path) — sweep profile along path
Workplane.revolve(angleDegrees=360, axisStart, axisEnd)
Workplane.twistExtrude(distance, angleDegrees) — helical extrusion
Workplane.split(keepTop, keepBottom) — split solid with workplane
Workplane.union(toUnion) — boolean add
Workplane.cut(toCut) — boolean subtract
Workplane.intersect(toIntersect) — boolean intersect
Workplane.mirror(mirrorPlane, basePointVector, union=False)
Workplane.rotate(axisStart, axisEnd, angleDegrees)
Workplane.translate(vec)
Workplane.text(txt, fontsize, distance) — 3D embossed text

═══ KEY 2D OPERATIONS REFERENCE ═══
Workplane.center(x, y) — shift local coords
Workplane.moveTo(x, y) — move without drawing
Workplane.lineTo(x, y) — line to absolute point
Workplane.line(xDist, yDist) — line relative
Workplane.hLine(distance) / .vLine(distance) — horizontal/vertical
Workplane.hLineTo(x) / .vLineTo(y) — to absolute coord
Workplane.circle(radius)
Workplane.rect(xLen, yLen, centered=True)
Workplane.ellipse(x_radius, y_radius)
Workplane.polygon(nSides, diameter)
Workplane.polyline(pts) — open polyline from point list
Workplane.spline(pts, includeCurrent=False, tangents=None)
Workplane.threePointArc(point1, point2) — arc through 3 points
Workplane.sagittaArc(endPoint, sag)
Workplane.radiusArc(endPoint, radius)
Workplane.tangentArcPoint(endpoint)
Workplane.slot2D(length, diameter, angle=0)
Workplane.offset2D(d, kind="arc")
Workplane.close() — close open wire
Workplane.mirrorY() / .mirrorX() — mirror 2D profile
Workplane.pushPoints(pts) — place multiple features
Workplane.rarray(xSpace, ySpace, xCount, yCount) — rectangular array
Workplane.polarArray(radius, startAngle, angle, count) — polar array
"""


def find_relevant_example(prompt: str, max_examples: int = 1) -> list:
    """
    Find the most relevant training example(s) for a given prompt.
    Returns list of (category_key, example_dict) tuples, best match first.
    """
    prompt_lower = prompt.lower()
    scored = []

    for key, example in TRAINING_EXAMPLES.items():
        score = 0.0

        # Exact keyword phrase match
        for kw in example["keywords"]:
            if kw in prompt_lower:
                score += 100.0 + len(kw.split())

        # Partial word overlap
        prompt_words = set(prompt_lower.split())
        for kw in example["keywords"]:
            kw_words = set(kw.split())
            overlap = len(prompt_words & kw_words)
            if overlap > 0:
                score += overlap * 10.0

        # Category match
        if example["category"].lower() in prompt_lower:
            score += 15.0

        if score > 0:
            scored.append((score, key, example))

    # Sort by score descending
    scored.sort(key=lambda x: -x[0])
    return [(key, ex) for _, key, ex in scored[:max_examples]]


def format_training_example(key: str, example: dict) -> str:
    """
    Format a training example as a prompt-injectable block.
    """
    return f"""
═══ VERIFIED WORKING EXAMPLE — {example['category'].upper()} ═══
Category: {example['category']}
Description: {example['description']}

This code has been VERIFIED to produce correct 3D geometry with no errors.
Use it as a TEMPLATE — adapt dimensions and features to match the user's request.

```python
{example['code'].strip()}
```

KEY PATTERNS FROM THIS EXAMPLE:
• Uses centered=(True, True, False) on main .box() for Z=0 ground
• All positions computed from body dimensions (no hardcoded coordinates)
• Every .fillet()/.chamfer() wrapped in try/except
• Features use correct shapes (cylinder for round, slot2D for slots)
• Parts overlap before .union() — no floating disconnected solids
═══ END VERIFIED EXAMPLE ═══
"""


def get_training_context(prompt: str) -> str:
    """
    Main entry point: find relevant training example and return formatted text
    for injection into the system prompt or user message.
    Returns empty string if no relevant example found.
    """
    matches = find_relevant_example(prompt, max_examples=1)
    if not matches:
        return ""

    key, example = matches[0]
    return format_training_example(key, example)


def get_cadquery_reference() -> str:
    """
    Return compact CadQuery API technique reference from official documentation.
    Always injected into system prompt for correct API usage patterns.
    """
    return CADQUERY_TECHNIQUE_REFERENCE
