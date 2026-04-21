from ..core.metadata import ExampleMetadata

metadata = ExampleMetadata(
    id="wine_glass",
    name="Wine Glass",
    category="container",
    keywords=["wine", "glass", "stemware", "goblet", "drink"],
    description="Stemmed wine glass: bowl, stem, and foot — revolved from a spline profile.",
    techniques=["safe_revolve"],
    nominal_dimensions_mm={"total_height": 210.0, "bowl_diameter": 85.0, "foot_diameter": 70.0},
    difficulty="medium",
)

code = '''import cadquery as cq

total_h = 210.0
bowl_d = 85.0
foot_d = 70.0
stem_d = 8.0
wall = 1.5
foot_h = 4.0

r_bowl = bowl_d / 2.0
r_foot = foot_d / 2.0
r_stem = stem_d / 2.0

# Outer profile (all X >= 0) — polyline approximation
outer = (
    cq.Workplane("XZ")
    .moveTo(0, 0)
    .lineTo(r_foot, 0)
    .lineTo(r_foot, foot_h)
    .lineTo(r_stem + 2, foot_h + 6)
    .lineTo(r_stem, foot_h + 15)
    .lineTo(r_stem, total_h * 0.45)
    .lineTo(r_stem + 4, total_h * 0.5)
    .lineTo(r_bowl * 0.9, total_h * 0.6)
    .lineTo(r_bowl, total_h * 0.75)
    .lineTo(r_bowl * 0.85, total_h * 0.92)
    .lineTo(r_bowl * 0.7, total_h)
    .lineTo(0, total_h)
    .close()
)
body = outer.revolve(360)

# Hollow the bowl from the top — simple polyline cavity
hollow_profile = (
    cq.Workplane("XZ")
    .moveTo(0, total_h * 0.6)
    .lineTo(r_bowl * 0.9 - wall, total_h * 0.6)
    .lineTo(r_bowl - wall, total_h * 0.75)
    .lineTo(r_bowl * 0.85 - wall, total_h * 0.92)
    .lineTo(r_bowl * 0.7 - wall, total_h - wall)
    .lineTo(0, total_h - wall)
    .close()
)
cavity = hollow_profile.revolve(360)
body = body.cut(cavity)

result = body
'''
