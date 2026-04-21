from ..core.metadata import ExampleMetadata

metadata = ExampleMetadata(
    id="guitar_pick",
    name="Guitar Pick",
    category="musical",
    keywords=["guitar", "pick", "plectrum", "music", "instrument"],
    description="Standard 351-shape guitar pick extruded from a 3-point-arc outline.",
    techniques=["polyline_profile", "guarded_fillet"],
    nominal_dimensions_mm={"width": 26.0, "height": 31.0, "thickness": 0.88},
    difficulty="easy",
)

code = '''import cadquery as cq

w = 26.0
h = 31.0
thick = 0.88
tip_r = 3.0

# Rounded-triangle outline via three arcs
outline = (
    cq.Workplane("XY")
    .moveTo(0, h * 0.55)
    .threePointArc((w / 2.0, h * 0.15), (w * 0.25, -h * 0.3))
    .threePointArc((0, -h * 0.45 + tip_r), (-w * 0.25, -h * 0.3))
    .threePointArc((-w / 2.0, h * 0.15), (0, h * 0.55))
    .close()
)
body = outline.extrude(thick)

try:
    body = body.edges(">Z or <Z").fillet(min(0.3, thick * 0.4))
except Exception:
    pass

result = body
'''
