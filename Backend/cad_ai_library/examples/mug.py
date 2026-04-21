from ..core.metadata import ExampleMetadata

metadata = ExampleMetadata(
    id="mug",
    name="Coffee Mug",
    category="container",
    keywords=["mug", "cup", "tumbler", "coffee", "tea", "handle"],
    description="Hollow cylindrical mug with a fillet rim, flat base, and extruded side handle.",
    techniques=["box+shell", "union handle", "rim fillet", "centered grounding"],
    nominal_dimensions_mm={"diameter": 80.0, "height": 95.0, "wall": 3.0},
    difficulty="beginner",
)

code = '''\
import cadquery as cq

# Parameters (mm)
diameter = 80.0
height = 95.0
wall = 3.0
base_thickness = 4.0
handle_width = 12.0
handle_thickness = 8.0
handle_height = 50.0
handle_offset = 18.0  # gap between handle inner face and mug wall
rim_fillet = 2.0

# Body — a closed cylinder, then shell out the top face for a cup cavity.
body = (
    cq.Workplane("XY")
    .circle(diameter / 2.0)
    .extrude(height)
)
body = body.faces(">Z").shell(-wall)  # inward shell keeps outer diameter exact

# Rim softening (guarded — fillet can fail if radius exceeds wall)
try:
    body = body.edges(">Z").fillet(min(rim_fillet, wall * 0.45))
except Exception:
    pass

# Handle — a rounded rectangle bar unioned to the side, with a cutout for the grip.
handle_outer = (
    cq.Workplane("XZ", origin=(diameter / 2.0 + handle_offset / 2.0, 0, height / 2.0))
    .rect(handle_thickness + handle_offset, handle_height)
    .extrude(handle_width, both=True)
    .edges("|Y")
    .fillet(4.0)
)
handle_inner = (
    cq.Workplane("XZ", origin=(diameter / 2.0 + handle_offset / 2.0 + 3.0, 0, height / 2.0))
    .rect(handle_offset + 0.5, handle_height - 16.0)
    .extrude(handle_width + 2.0, both=True)
)
handle = handle_outer.cut(handle_inner)

result = body.union(handle)
'''
