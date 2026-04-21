from ..core.metadata import ExampleMetadata

metadata = ExampleMetadata(
    id="storage_box",
    name="Stackable Storage Box",
    category="organizer",
    keywords=["box", "storage", "bin", "stackable", "lid", "tote"],
    description="Thin-wall storage box with rounded corners and a recessed rim so identical boxes stack.",
    techniques=["box+shell", "corner fillet before shell", "recessed rim for stacking"],
    nominal_dimensions_mm={"length": 200.0, "width": 140.0, "height": 90.0},
    difficulty="beginner",
)

code = '''\
import cadquery as cq

length, width, height = 200.0, 140.0, 90.0
wall = 3.0
corner_fillet = 8.0
rim_recess_depth = 3.0
rim_recess_inset = 2.0

outer = cq.Workplane("XY").box(length, width, height, centered=(True, True, False))

# Round vertical corners BEFORE shelling — much more robust than shelling first
try:
    outer = outer.edges("|Z").fillet(corner_fillet)
except Exception:
    pass

box_ = outer.faces(">Z").shell(-wall)

# Recess on top rim so the base of another box nests into it
rim_cutter = (
    cq.Workplane("XY", origin=(0, 0, height - rim_recess_depth))
    .box(
        length - 2 * rim_recess_inset,
        width - 2 * rim_recess_inset,
        rim_recess_depth + 0.5,
        centered=(True, True, False),
    )
)
box_ = box_.cut(rim_cutter)

result = box_
'''
