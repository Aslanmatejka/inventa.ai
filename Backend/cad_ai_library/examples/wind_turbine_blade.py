from ..core.metadata import ExampleMetadata

metadata = ExampleMetadata(
    id="wind_turbine_blade",
    name="Wind Turbine Blade",
    category="energy",
    keywords=["wind", "turbine", "blade", "renewable", "energy", "airfoil"],
    description="Tapered, twisted wind turbine blade lofted from airfoil sections.",
    techniques=["loft_airfoils"],
    nominal_dimensions_mm={"length": 400.0, "root_chord": 60.0, "tip_chord": 20.0, "twist_deg": 12.0},
    difficulty="hard",
)

code = '''import cadquery as cq

length = 400.0
root_chord = 60.0
tip_chord = 20.0
twist = 12.0  # deg, root to tip
root_thick = 18.0
tip_thick = 5.0

def airfoil(chord, thick, twist_deg, z):
    t = thick / 2.0
    c = chord
    # Teardrop-ish airfoil: rect with rounded leading/trailing via spline
    pts = [
        (-c * 0.5, 0),
        (-c * 0.4, t),
        (c * 0.2, t * 0.9),
        (c * 0.5, 0),
        (c * 0.2, -t * 0.9),
        (-c * 0.4, -t),
    ]
    wp = cq.Workplane("XY", origin=(0, 0, z)).polyline(pts).close()
    return wp

sections = 5
sketches = []
for i in range(sections):
    f = i / (sections - 1)
    chord = root_chord + (tip_chord - root_chord) * f
    thick = root_thick + (tip_thick - root_thick) * f
    z = length * f
    # We'll build the loft by stacking workplanes manually
    sketches.append((chord, thick, twist * f, z))

# Build loft incrementally using Workplane chain
wp = cq.Workplane("XY")
first = True
for (chord, thick, tw, z) in sketches:
    t = thick / 2.0
    pts = [
        (-chord * 0.5, 0),
        (-chord * 0.4, t),
        (chord * 0.2, t * 0.9),
        (chord * 0.5, 0),
        (chord * 0.2, -t * 0.9),
        (-chord * 0.4, -t),
    ]
    # Apply twist rotation to points
    import math as _m
    ca = _m.cos(_m.radians(tw))
    sa = _m.sin(_m.radians(tw))
    pts = [(x * ca - y * sa, x * sa + y * ca) for (x, y) in pts]
    if first:
        wp = cq.Workplane("XY").polyline(pts).close()
        first = False
    else:
        wp = wp.workplane(offset=z - sketches[sketches.index((chord, thick, tw, z)) - 1][3]).polyline(pts).close()

body = wp.loft(combine=True)

# Rotate to stand vertically (blade along +Z already)
result = body
'''
