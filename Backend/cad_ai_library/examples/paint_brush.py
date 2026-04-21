from ..core.metadata import ExampleMetadata

metadata = ExampleMetadata(
    id="paint_brush",
    name="Artist Paint Brush",
    category="art_supplies",
    keywords=["paint", "brush", "artist", "art", "painting", "craft"],
    description="Flat-ferrule artist paint brush: wooden handle, metal ferrule, bristle block.",
    techniques=["safe_revolve"],
    nominal_dimensions_mm={"total_length": 200.0, "handle_diameter": 10.0, "ferrule_length": 25.0, "bristle_length": 20.0},
    difficulty="medium",
)

code = '''import cadquery as cq

total_l = 200.0
handle_d = 10.0
handle_tip_d = 6.0
ferrule_l = 25.0
ferrule_d = 10.5
bristle_l = 20.0
bristle_w = 12.0
bristle_t = 3.0

# Handle: tapered, revolved (profile lies along +X axis in XZ plane; we revolve about Z... actually we want axis along X)
# Use XZ plane with Z as the long axis so revolve about Z axis works naturally
# Build horizontally then rotate afterwards.
handle_profile = (
    cq.Workplane("XZ")
    .moveTo(0, 0)
    .lineTo(handle_tip_d / 2.0, 0)
    .spline([(handle_d / 2.0 * 0.9, total_l * 0.2),
             (handle_d / 2.0, total_l * 0.45)])
    .lineTo(handle_d / 2.0 * 0.85, total_l - ferrule_l - 2)
    .lineTo(0, total_l - ferrule_l - 2)
    .close()
)
handle = handle_profile.revolve(360)

# Ferrule (cylinder)
ferrule = (
    cq.Workplane("XY", origin=(0, 0, total_l - ferrule_l - 2))
    .circle(ferrule_d / 2.0)
    .extrude(ferrule_l)
)

# Bristles (flat rectangular block flattened at the tip)
bristles = (
    cq.Workplane("XY", origin=(0, 0, total_l - 2))
    .rect(bristle_w, bristle_t)
    .extrude(bristle_l)
)
try:
    bristles = bristles.edges(">Z").fillet(1.0)
except Exception:
    pass

body = handle.union(ferrule).union(bristles)

result = body
'''
