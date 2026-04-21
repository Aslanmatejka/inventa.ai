from ..core.metadata import ExampleMetadata

metadata = ExampleMetadata(
    id="gear",
    name="Spur Gear",
    category="mechanical",
    keywords=["gear", "spur gear", "cog", "teeth", "hub"],
    description="Simple spur gear: a disk with trapezoidal teeth polar-arrayed around the rim, plus a central bore.",
    techniques=["polar array via polarArray", "trapezoidal tooth profile", "central bore"],
    nominal_dimensions_mm={"pitch_diameter": 60.0, "teeth": 20, "thickness": 8.0},
    difficulty="intermediate",
)

code = '''\
import cadquery as cq
import math

module_m = 3.0
teeth = 20
pitch_diameter = module_m * teeth
outer_diameter = pitch_diameter + 2 * module_m
root_diameter = pitch_diameter - 2.5 * module_m
thickness = 8.0
bore_diameter = 10.0

# Base disk to outer diameter
gear = (
    cq.Workplane("XY")
    .circle(outer_diameter / 2.0)
    .extrude(thickness)
)

# Tooth profile — thin trapezoid, placed on +X and polar-arrayed
tooth_tip = module_m * 1.2
tooth_base = module_m * 1.6
tooth_radial = (outer_diameter - root_diameter) / 2.0 + 0.5

tooth = (
    cq.Workplane("XY", origin=(root_diameter / 2.0, 0, 0))
    .polyline([
        (0, -tooth_base / 2.0),
        (tooth_radial, -tooth_tip / 2.0),
        (tooth_radial, tooth_tip / 2.0),
        (0, tooth_base / 2.0),
    ])
    .close()
    .extrude(thickness)
)

# Polar-array the tooth; cut the disk DOWN to the root diameter first,
# then union the teeth back on top.
root_disk = cq.Workplane("XY").circle(root_diameter / 2.0).extrude(thickness)
tooth_ring = cq.Workplane("XY")
for i in range(teeth):
    angle = 360.0 / teeth * i
    tooth_ring = tooth_ring.union(
        tooth.rotate((0, 0, 0), (0, 0, 1), angle)
    )

gear = root_disk.union(tooth_ring)

# Central bore
gear = gear.faces(">Z").workplane().hole(bore_diameter)

result = gear
'''
