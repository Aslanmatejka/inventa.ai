from ..core.metadata import ExampleMetadata

metadata = ExampleMetadata(
    id="cranial_plate",
    name="Cranial Plate Implant",
    category="prosthetic",
    keywords=["cranial", "skull", "plate", "cranioplasty", "patient-specific", "titanium mesh", "neurosurgery", "implant", "prosthetic"],
    description="Patient-specific cranial plate: curved shell matching skull contour with ventilation holes and fixation tabs.",
    techniques=["revolve", "polar_pattern", "boolean_cut"],
    nominal_dimensions_mm={"diameter": 95.0, "curvature_height": 18.0, "thickness": 2.0},
    difficulty="medium",
)

code = '''import cadquery as cq
import math

# Build as a spherical cap: difference between two spheres
R_outer = 75.0
R_inner = 73.0

outer = cq.Workplane("XY").sphere(R_outer)
inner = cq.Workplane("XY").sphere(R_inner)
shell = outer.cut(inner)

# Keep only the cap (top slice)
cap_keep = (cq.Workplane("XY").workplane(offset=55)
            .box(200, 200, 40, centered=(True, True, False)))
cap = shell.intersect(cap_keep)
# Lower it so the cap sits at z>=0
cap = cap.translate((0, 0, -55))

body = cap

# Ventilation holes (pattern of small through-holes)
for i in range(6):
    ang = i * 60
    x = 25 * math.cos(math.radians(ang))
    y = 25 * math.sin(math.radians(ang))
    hole = (cq.Workplane("XY").center(x, y).circle(2.5).extrude(30))
    body = body.cut(hole)

# Center drain hole
body = body.cut(cq.Workplane("XY").circle(3).extrude(30))

# Fixation tabs around the rim (6 flat ears with screw holes)
for i in range(6):
    ang = i * 60
    tab_x = 48 * math.cos(math.radians(ang))
    tab_y = 48 * math.sin(math.radians(ang))
    tab = (cq.Workplane("XY").workplane(offset=2)
           .center(tab_x, tab_y).circle(5).extrude(2))
    tab = tab.cut(cq.Workplane("XY").workplane(offset=0)
                  .center(tab_x, tab_y).circle(1.5).extrude(6))
    body = body.union(tab)

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
