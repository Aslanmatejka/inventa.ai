from ..core.metadata import ExampleMetadata

metadata = ExampleMetadata(
    id="desk_organizer",
    name="Desk Organizer",
    category="organizer",
    keywords=["organizer", "desk", "tray", "compartment", "caddy", "pencil holder"],
    description="Rectangular tray with three internal compartments, subtractive cavities cut from a solid block.",
    techniques=["subtractive cavities", "grid of cuts", "chamfered top edge"],
    nominal_dimensions_mm={"length": 180.0, "width": 100.0, "height": 60.0},
    difficulty="beginner",
)

code = '''\
import cadquery as cq

length, width, height = 180.0, 100.0, 60.0
wall = 4.0
compartments = 3
divider = 3.5

body = cq.Workplane("XY").box(length, width, height, centered=(True, True, False))

# Usable inner length after walls + dividers
inner_length = length - 2 * wall - (compartments - 1) * divider
slot_length = inner_length / compartments
slot_width = width - 2 * wall
slot_depth = height - wall  # leave solid floor

x0 = -length / 2.0 + wall + slot_length / 2.0
for i in range(compartments):
    x = x0 + i * (slot_length + divider)
    cavity = (
        cq.Workplane("XY", origin=(x, 0, wall))
        .box(slot_length, slot_width, slot_depth + 1.0, centered=(True, True, False))
    )
    body = body.cut(cavity)

try:
    body = body.edges(">Z").chamfer(1.2)
except Exception:
    pass

result = body
'''
