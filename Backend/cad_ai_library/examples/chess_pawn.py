from ..core.metadata import ExampleMetadata

metadata = ExampleMetadata(
    id="chess_pawn",
    name="Chess Pawn",
    category="toy",
    keywords=["chess", "pawn", "piece", "game", "board", "figure"],
    description="Classic chess pawn silhouette revolved from a stepped spline profile.",
    techniques=["safe_revolve"],
    nominal_dimensions_mm={"base_diameter": 28.0, "height": 48.0, "head_diameter": 15.0},
    difficulty="medium",
)

code = '''import cadquery as cq

base_d = 28.0
height = 48.0
head_d = 15.0
collar_d = 18.0

r_base = base_d / 2.0
r_head = head_d / 2.0
r_collar = collar_d / 2.0

profile = (
    cq.Workplane("XZ")
    .moveTo(0, 0)
    .lineTo(r_base, 0)
    .lineTo(r_base, 4)
    .lineTo(r_base * 0.55, 8)
    .lineTo(r_base * 0.45, 14)
    .lineTo(r_base * 0.45, 18)
    .lineTo(r_collar, 20)
    .lineTo(r_collar, 22)
    .lineTo(r_base * 0.4, 24)
    .spline([(r_base * 0.32, 30), (r_head * 1.1, height * 0.78), (r_head, height * 0.9), (0, height)])
    .close()
)
body = profile.revolve(360)

result = body
'''
