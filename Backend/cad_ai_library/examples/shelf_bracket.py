from ..core.metadata import ExampleMetadata

metadata = ExampleMetadata(
    id="shelf_bracket",
    name="Shelf Bracket",
    category="mechanical",
    keywords=["shelf", "bracket", "wall", "support", "mount", "triangular"],
    description="Triangular wall shelf bracket with gusset and countersunk mount holes.",
    techniques=["polyline_profile", "cbore_hole"],
    nominal_dimensions_mm={"wall_height": 150.0, "shelf_depth": 120.0, "thickness": 6.0},
    difficulty="medium",
)

code = '''import cadquery as cq

wall_h = 150.0
shelf_d = 120.0
thick = 6.0
screw_d = 4.5
screw_head_d = 8.5
cbore_depth = 2.5

# Triangular gusset profile in XZ (wall on -X side, shelf on +Z side)
profile = (
    cq.Workplane("XZ")
    .moveTo(0, 0)
    .lineTo(0, wall_h)
    .lineTo(thick, wall_h)
    .lineTo(thick, thick)
    .lineTo(shelf_d, thick)
    .lineTo(shelf_d, 0)
    .close()
)
flat = profile.extrude(thick).translate((0, -thick / 2.0, 0))

# Web / gusset between the two flanges (diagonal plate)
web_profile = (
    cq.Workplane("XZ")
    .moveTo(thick, thick)
    .lineTo(shelf_d, thick)
    .lineTo(thick, wall_h)
    .close()
)
web = web_profile.extrude(thick).translate((0, -thick / 2.0, 0))

body = flat.union(web)

# Countersunk mount holes in the vertical leg (two of them)
body = (
    body.faces("<X").workplane()
    .pushPoints([(0, wall_h * 0.25), (0, wall_h * 0.75)])
    .cboreHole(screw_d, screw_head_d, cbore_depth)
)

result = body
'''
