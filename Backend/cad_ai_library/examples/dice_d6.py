from ..core.metadata import ExampleMetadata

metadata = ExampleMetadata(
    id="dice_d6",
    name="Six-Sided Die",
    category="gaming",
    keywords=["dice", "die", "d6", "gaming", "board", "tabletop", "cube"],
    description="Standard six-sided die (d6) with pip indentations on each face.",
    techniques=["polar_array", "guarded_fillet"],
    nominal_dimensions_mm={"side": 16.0, "pip_diameter": 2.0, "pip_depth": 0.8},
    difficulty="medium",
)

code = '''import cadquery as cq

side = 16.0
pip_d = 2.0
pip_depth = 0.8
pip_spacing = side * 0.28

body = cq.Workplane("XY").box(side, side, side, centered=(True, True, False))
try:
    body = body.edges().fillet(1.8)
except Exception:
    pass

def pips_on_face(face_selector, count, axis):
    if count == 1:
        pts = [(0, 0)]
    elif count == 2:
        pts = [(-pip_spacing, -pip_spacing), (pip_spacing, pip_spacing)]
    elif count == 3:
        pts = [(-pip_spacing, -pip_spacing), (0, 0), (pip_spacing, pip_spacing)]
    elif count == 4:
        pts = [(-pip_spacing, -pip_spacing), (pip_spacing, pip_spacing),
               (-pip_spacing, pip_spacing), (pip_spacing, -pip_spacing)]
    elif count == 5:
        pts = [(-pip_spacing, -pip_spacing), (pip_spacing, pip_spacing),
               (-pip_spacing, pip_spacing), (pip_spacing, -pip_spacing), (0, 0)]
    else:  # 6
        pts = [(-pip_spacing, -pip_spacing), (-pip_spacing, 0), (-pip_spacing, pip_spacing),
               (pip_spacing, -pip_spacing), (pip_spacing, 0), (pip_spacing, pip_spacing)]
    return pts

# Top face = 1
body = (body.faces(">Z").workplane()
        .pushPoints(pips_on_face(">Z", 1, "Z"))
        .circle(pip_d / 2.0).cutBlind(-pip_depth))
# Bottom face = 6
body = (body.faces("<Z").workplane()
        .pushPoints(pips_on_face("<Z", 6, "Z"))
        .circle(pip_d / 2.0).cutBlind(-pip_depth))
# +X = 2
body = (body.faces(">X").workplane()
        .pushPoints(pips_on_face(">X", 2, "X"))
        .circle(pip_d / 2.0).cutBlind(-pip_depth))
# -X = 5
body = (body.faces("<X").workplane()
        .pushPoints(pips_on_face("<X", 5, "X"))
        .circle(pip_d / 2.0).cutBlind(-pip_depth))
# +Y = 3
body = (body.faces(">Y").workplane()
        .pushPoints(pips_on_face(">Y", 3, "Y"))
        .circle(pip_d / 2.0).cutBlind(-pip_depth))
# -Y = 4
body = (body.faces("<Y").workplane()
        .pushPoints(pips_on_face("<Y", 4, "Y"))
        .circle(pip_d / 2.0).cutBlind(-pip_depth))

result = body
'''
