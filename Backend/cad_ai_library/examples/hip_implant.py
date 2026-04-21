from ..core.metadata import ExampleMetadata

metadata = ExampleMetadata(
    id="hip_implant",
    name="Total Hip Implant",
    category="prosthetic",
    keywords=["hip", "implant", "hip replacement", "femoral stem", "orthopedic", "arthroplasty", "prosthetic", "ball and socket"],
    description="Total hip replacement: tapered femoral stem, neck, ball head, and acetabular cup liner.",
    techniques=["loft", "revolve", "boolean_union"],
    nominal_dimensions_mm={"total_height": 220.0, "ball_dia": 36.0, "cup_dia": 54.0},
    difficulty="medium",
)

code = '''import cadquery as cq

# Femoral stem (tapered, roughly trapezoidal cross-section)
stem = (cq.Workplane("XY")
        .rect(18, 14)
        .workplane(offset=150)
        .center(0, 0)
        .rect(10, 8)
        .loft(combine=True))
try:
    stem = stem.edges("|Z").fillet(3.0)
except Exception:
    pass

# Shoulder transition
shoulder = (cq.Workplane("XY").workplane(offset=150)
            .rect(22, 18).workplane(offset=20).center(-10, 0)
            .rect(26, 22).loft(combine=True))

# Neck (angled cylinder ~ 135°)
neck = (cq.Workplane("YZ").workplane(offset=0)
        .center(0, 185).circle(8).extrude(35))
# Rotate it 45° outward
neck = neck.rotate((0, 0, 185), (0, 1, 0), -45)

# Ball head (modular, on neck)
import math
neck_angle = math.radians(45)
head_x = 35 * math.sin(neck_angle)
head_z = 185 + 35 * math.cos(neck_angle)
head = (cq.Workplane("XY").workplane(offset=head_z)
        .center(head_x, 0).sphere(18))

# Acetabular cup liner (hemispherical bowl, separate, offset above/lateral)
cup_outer = (cq.Workplane("XY").workplane(offset=head_z - 5)
             .center(head_x, 0).sphere(27))
cup_cavity = (cq.Workplane("XY").workplane(offset=head_z - 5)
              .center(head_x, 0).sphere(20))
cup = cup_outer.cut(cup_cavity)
# Trim bottom half of cup (keep hemisphere open downward)
cup_trim = (cq.Workplane("XY").workplane(offset=head_z - 5)
            .center(head_x, 0).box(60, 60, 60, centered=(True, True, False))
            .translate((0, 0, -60)))
cup = cup.cut(cup_trim)

body = stem.union(shoulder).union(neck).union(head).union(cup)

# Porous coating bumps on proximal stem (simplified as ring grooves)
for z in [120, 135, 148]:
    groove = (cq.Workplane("XY").workplane(offset=z)
              .rect(22, 18).rect(20, 16).extrude(2))
    body = body.cut(groove)

result = body
'''
