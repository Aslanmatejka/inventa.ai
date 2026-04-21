from ..core.metadata import ExampleMetadata

metadata = ExampleMetadata(
    id="capo",
    name="Guitar Capo",
    category="musical",
    keywords=["capo", "guitar", "music", "fret", "clamp", "instrument"],
    description="Simple spring-style guitar capo with padded fret bar and grip lever.",
    techniques=["polyline_profile", "guarded_fillet"],
    nominal_dimensions_mm={"span_mm": 55.0, "bar_length": 75.0, "bar_thickness": 10.0},
    difficulty="medium",
)

code = '''import cadquery as cq

span = 55.0
bar_len = 75.0
bar_thick = 10.0
lever_len = 70.0
lever_thick = 8.0

# C-profile in YZ that wraps the fretboard
profile = (
    cq.Workplane("YZ")
    .moveTo(0, 0)
    .lineTo(bar_thick, 0)
    .lineTo(bar_thick, span + bar_thick)
    .lineTo(-lever_len + bar_thick, span + bar_thick)
    .lineTo(-lever_len + bar_thick, span + bar_thick - lever_thick)
    .lineTo(0, span + bar_thick - lever_thick)
    .lineTo(0, bar_thick)
    .lineTo(-lever_len * 0.6, bar_thick)
    .lineTo(-lever_len * 0.6, 0)
    .close()
)
body = profile.extrude(bar_len).translate((-bar_len / 2.0, 0, 0))

try:
    body = body.edges("|X").fillet(1.2)
except Exception:
    pass

# Rubber pad insert on the fret bar
pad = (
    cq.Workplane("XY", origin=(0, bar_thick / 2.0, span + bar_thick - 1.0))
    .box(bar_len * 0.9, bar_thick * 0.8, 1.2, centered=(True, True, False))
)
body = body.union(pad)

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
