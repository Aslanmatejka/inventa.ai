from ..core.metadata import ExampleMetadata

metadata = ExampleMetadata(
    id="hammer_head",
    name="Claw Hammer Head",
    category="tool",
    keywords=["hammer", "claw", "tool", "head", "nail", "strike"],
    description="Claw hammer head with striking face, handle eye, and split claw.",
    techniques=["polyline_profile", "guarded_fillet"],
    nominal_dimensions_mm={"length": 110.0, "face_diameter": 28.0, "eye_length": 30.0},
    difficulty="medium",
)

code = '''import cadquery as cq

length = 110.0
width = 26.0
face_d = 28.0
eye_l = 30.0
eye_w = 14.0

# Side profile in XZ
profile = (
    cq.Workplane("XZ")
    .moveTo(0, 0)
    .lineTo(face_d, 0)
    .lineTo(face_d, face_d * 0.85)
    .lineTo(eye_l + 8, face_d * 0.5)
    .lineTo(eye_l + 4, -face_d * 0.15)
    .lineTo(length - 5, -face_d * 0.3)
    .lineTo(length, 0)
    .lineTo(length - 4, face_d * 0.35)
    .lineTo(eye_l + 6, face_d * 0.6)
    .lineTo(face_d * 0.1, face_d * 0.85)
    .close()
)
body = profile.extrude(width).translate((0, -width / 2.0, 0))

try:
    body = body.edges("|Y").fillet(2.0)
except Exception:
    pass

# Handle eye through Y
eye = (
    cq.Workplane("XZ", origin=(face_d * 0.55, -width / 2.0 - 1, face_d * 0.4))
    .rect(eye_w, face_d * 0.45)
    .extrude(width + 2)
)
body = body.cut(eye)

# Claw slot
claw = (
    cq.Workplane("XZ", origin=(length - 10, -2, -face_d * 0.25))
    .rect(22, 4)
    .extrude(4)
)
body = body.cut(claw)

result = body
'''
