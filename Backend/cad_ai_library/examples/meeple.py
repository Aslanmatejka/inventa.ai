from ..core.metadata import ExampleMetadata

metadata = ExampleMetadata(
    id="meeple",
    name="Board Game Meeple",
    category="gaming",
    keywords=["meeple", "pawn", "token", "board game", "gaming", "piece"],
    description="Classic meeple board game token silhouette extruded as a flat figure.",
    techniques=["polyline_profile"],
    nominal_dimensions_mm={"height": 25.0, "width": 18.0, "thickness": 8.0},
    difficulty="medium",
)

code = '''import cadquery as cq

h = 25.0
w = 18.0
t = 8.0

# Half silhouette (right side) mirrored for symmetry
pts_right = [
    (0, 0),                     # bottom center between legs
    (w * 0.25, 0),              # right leg outer bottom
    (w * 0.25, h * 0.35),       # right leg top outer
    (w * 0.5, h * 0.35),        # hip right
    (w * 0.5, h * 0.55),        # torso right below arm
    (w * 0.8, h * 0.55),        # arm right outer
    (w * 0.8, h * 0.7),         # arm top
    (w * 0.35, h * 0.72),       # shoulder
    (w * 0.28, h * 0.78),       # neck
    (w * 0.3, h),               # top of head right
    (0, h),                     # top center head
]
pts_left = [(-x, y) for (x, y) in reversed(pts_right)]
all_pts = pts_right + pts_left[1:]  # avoid dup at top-center

body = cq.Workplane("XY").polyline(all_pts).close().extrude(t)

result = body
'''
