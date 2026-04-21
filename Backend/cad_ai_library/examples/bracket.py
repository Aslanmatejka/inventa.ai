from ..core.metadata import ExampleMetadata

metadata = ExampleMetadata(
    id="bracket",
    name="L-Bracket",
    category="mechanical",
    keywords=["bracket", "l-bracket", "angle", "mount", "support", "gusset"],
    description="90-degree L-bracket with countersunk mounting holes and a triangular gusset for rigidity.",
    techniques=["union of two plates", "triangular gusset via polyline", "countersunk holes (cboreHole)"],
    nominal_dimensions_mm={"length": 80.0, "width": 40.0, "thickness": 5.0},
    difficulty="beginner",
)

code = '''\
import cadquery as cq

leg_length = 80.0
width = 40.0
thickness = 5.0
hole_diameter = 5.5
hole_inset = 12.0
gusset_size = 30.0

# Horizontal plate on the XY floor
base = cq.Workplane("XY").box(leg_length, width, thickness, centered=(True, True, False))

# Vertical plate rising from the back edge
upright = (
    cq.Workplane("XZ", origin=(0, width / 2.0 - thickness / 2.0, leg_length / 2.0))
    .box(leg_length, thickness, leg_length, centered=(True, True, True))
)

bracket = base.union(upright)

# Two holes on each leg, countersunk for an M5
bracket = (
    bracket.faces(">Z[0]")
    .workplane()
    .pushPoints([(hole_inset - leg_length / 2.0, 0), (leg_length / 2.0 - hole_inset, 0)])
    .cboreHole(hole_diameter, hole_diameter + 4.0, 2.0)
)

# Triangular gusset
gusset = (
    cq.Workplane("XZ", origin=(0, width / 2.0 - thickness, 0))
    .polyline([(0, 0), (gusset_size, 0), (0, gusset_size)])
    .close()
    .extrude(thickness)
)
bracket = bracket.union(gusset)

result = bracket
'''
