from ..core.metadata import ExampleMetadata

metadata = ExampleMetadata(
    id="heart_box",
    name="Heart-Shaped Box",
    category="decorative",
    keywords=["heart", "box", "gift", "valentine", "trinket", "love"],
    description="Heart-shaped trinket box formed from two circles + a triangle, then shelled.",
    techniques=["polyline_profile", "shell_cavity", "guarded_fillet"],
    nominal_dimensions_mm={"width": 80.0, "height": 80.0, "depth": 30.0, "wall": 3.0},
    difficulty="medium",
)

code = '''import cadquery as cq

size = 80.0      # outer bounding box X and Y
depth = 30.0
wall = 3.0
r_lobe = size * 0.28

# Heart outline: two circles on top + a V-shape pointing down, mirrored to close properly.
lobe_r = r_lobe
from_y = size * 0.5 - lobe_r  # center height of the two circular lobes
outline = (
    cq.Workplane("XY")
    .moveTo(0, -size / 2.0)
    .lineTo(size / 2.0, from_y)
    .threePointArc((size / 2.0, from_y + lobe_r), (size / 2.0 - lobe_r, from_y + lobe_r))
    .threePointArc((0, from_y + lobe_r * 0.4), (-(size / 2.0 - lobe_r), from_y + lobe_r))
    .threePointArc((-size / 2.0, from_y + lobe_r), (-size / 2.0, from_y))
    .close()
)
body = outline.extrude(depth)

try:
    body = body.edges("|Z").fillet(2.0)
except Exception:
    pass

# Hollow (shell the top face)
body = body.faces(">Z").shell(-wall)

result = body
'''
