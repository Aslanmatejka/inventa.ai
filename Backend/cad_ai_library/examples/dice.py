from ..core.metadata import ExampleMetadata

metadata = ExampleMetadata(
    id="dice",
    name="Six-Sided Die",
    category="decorative",
    keywords=["dice", "die", "cube", "game", "board game", "d6"],
    description="Standard d6 with rounded corners and drilled pip markings.",
    techniques=["guarded_fillet", "polar_array"],
    nominal_dimensions_mm={"size": 16.0, "corner_fillet": 2.0, "pip_diameter": 2.2},
    difficulty="medium",
)

code = '''import cadquery as cq

size = 16.0
corner_r = 2.0
pip_d = 2.2
pip_depth = 0.8
s = size / 2.0

body = cq.Workplane("XY").box(size, size, size, centered=(True, True, False))

try:
    body = body.edges().fillet(min(corner_r, size * 0.15))
except Exception:
    pass

# Pip layouts per face (in face-local 2D coords, face half-size 4.0 margin)
m = size * 0.28  # pip offset from center

# Face: +Z -> 1 pip
body = body.faces(">Z").workplane().hole(pip_d, depth=pip_depth)

# Face: -Z -> 6 pips (2 columns x 3 rows)
body = (
    body.faces("<Z").workplane()
    .pushPoints([(-m, -m), (-m, 0), (-m, m), (m, -m), (m, 0), (m, m)])
    .hole(pip_d, depth=pip_depth)
)

# Face: +X -> 2 pips (diagonal)
body = (
    body.faces(">X").workplane()
    .pushPoints([(-m, -m), (m, m)])
    .hole(pip_d, depth=pip_depth)
)

# Face: -X -> 5 pips
body = (
    body.faces("<X").workplane()
    .pushPoints([(-m, -m), (-m, m), (0, 0), (m, -m), (m, m)])
    .hole(pip_d, depth=pip_depth)
)

# Face: +Y -> 3 pips (diagonal)
body = (
    body.faces(">Y").workplane()
    .pushPoints([(-m, -m), (0, 0), (m, m)])
    .hole(pip_d, depth=pip_depth)
)

# Face: -Y -> 4 pips (corners)
body = (
    body.faces("<Y").workplane()
    .pushPoints([(-m, -m), (-m, m), (m, -m), (m, m)])
    .hole(pip_d, depth=pip_depth)
)

result = body
'''
