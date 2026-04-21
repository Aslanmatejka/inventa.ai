from ..core.metadata import ExampleMetadata

metadata = ExampleMetadata(
    id="airplane_wing",
    name="Simple Airplane Wing",
    category="aerospace",
    keywords=["airplane", "wing", "airfoil", "plane", "aircraft", "toy"],
    description="Simplified trapezoidal airplane wing lofted from two rounded-rect airfoil sections.",
    techniques=["loft_frustum"],
    nominal_dimensions_mm={"root_chord": 140.0, "tip_chord": 80.0, "span": 250.0, "root_thickness": 16.0},
    difficulty="medium",
)

code = '''import cadquery as cq

root_c = 140.0
tip_c = 80.0
span = 250.0
root_t = 16.0
tip_t = 10.0
sweep = 25.0

# Loft between two rounded rectangles (airfoil stand-in)
wing = (
    cq.Workplane("XY")
    .rect(root_c, root_t)
    .workplane(offset=span)
    .moveTo(-sweep, 0)
    .rect(tip_c, tip_t)
    .loft(combine=True)
)

try:
    wing = wing.edges("|Z").fillet(min(4.0, tip_t * 0.4))
except Exception:
    pass

# Stand the wing up (span along Y)
result = wing.rotate((0, 0, 0), (1, 0, 0), 90).translate((0, 0, root_t / 2.0))
'''
