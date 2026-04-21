from ..core.metadata import ExampleMetadata

metadata = ExampleMetadata(
    id="whistle",
    name="Emergency Whistle",
    category="accessory",
    keywords=["whistle", "safety", "emergency", "signal", "hiking"],
    description="Compact whistle with chamber, mouthpiece and lanyard hole.",
    techniques=["guarded_fillet", "cbore_hole"],
    nominal_dimensions_mm={"length": 55.0, "width": 18.0, "height": 14.0, "chamber_diameter": 10.0},
    difficulty="medium",
)

code = '''import cadquery as cq

length = 55.0
width = 18.0
height = 14.0
chamber_d = 10.0
mouth_w = 8.0
mouth_h = 2.5
lanyard_d = 3.0

body = cq.Workplane("XY").box(length, width, height, centered=(True, True, False))
try:
    body = body.edges("|X or |Y").fillet(2.5)
except Exception:
    pass

# Resonance chamber (cylinder cut across Y)
chamber = (
    cq.Workplane("XZ", origin=(0, width / 2.0 + 0.1, height / 2.0))
    .circle(chamber_d / 2.0)
    .extrude(width + 0.2)
)
body = body.cut(chamber)

# Mouthpiece slot on one short end
mouth = (
    cq.Workplane("YZ", origin=(length / 2.0 + 0.1, 0, height / 2.0))
    .rect(mouth_w, mouth_h)
    .extrude(-(length / 2.0 - 2.0))
)
body = body.cut(mouth)

# Lanyard hole
body = (
    body.faces(">X")
    .workplane()
    .center(0, 0)
    .hole(lanyard_d)
)

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
