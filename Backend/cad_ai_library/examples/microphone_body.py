from ..core.metadata import ExampleMetadata

metadata = ExampleMetadata(
    id="microphone_body",
    name="Studio Microphone Body",
    category="electronics",
    keywords=["microphone", "mic", "studio", "audio", "recording", "podcast"],
    description="Cylindrical studio microphone body with mesh grille cage and XLR base.",
    techniques=["safe_revolve", "polar_array"],
    nominal_dimensions_mm={"length": 180.0, "body_diameter": 42.0, "grille_diameter": 54.0},
    difficulty="medium",
)

code = '''import cadquery as cq
import math

total_l = 180.0
body_d = 42.0
grille_d = 54.0
xlr_d = 22.0
grille_h = 60.0

# Revolve profile
profile = (
    cq.Workplane("XZ")
    .moveTo(0, 0)
    .lineTo(xlr_d / 2.0, 0)
    .lineTo(xlr_d / 2.0, 8)
    .lineTo(body_d / 2.0, 14)
    .lineTo(body_d / 2.0, total_l - grille_h)
    .lineTo(grille_d / 2.0, total_l - grille_h + 6)
    .lineTo(grille_d / 2.0, total_l - 4)
    .spline([(grille_d / 2.0 * 0.7, total_l - 1), (0, total_l)])
    .close()
)
body = profile.revolve(360)

# Grille ventilation holes (polar array band) — simplified single ring of bores
hole_count = 16
for i in range(hole_count):
    theta = 360.0 / hole_count * i
    x = (grille_d / 2.0 - 0.5) * math.cos(math.radians(theta))
    y = (grille_d / 2.0 - 0.5) * math.sin(math.radians(theta))
    v = (math.cos(math.radians(theta)), math.sin(math.radians(theta)), 0)
    for z in (total_l - grille_h + 20, total_l - grille_h + 40):
        try:
            cutter = (
                cq.Workplane(cq.Plane(origin=(x, y, z),
                                      xDir=(-v[1], v[0], 0),
                                      normal=v))
                .circle(1.2)
                .extrude(6)
            )
            body = body.cut(cutter)
        except Exception:
            pass

result = body
'''
