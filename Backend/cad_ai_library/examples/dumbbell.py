from ..core.metadata import ExampleMetadata

metadata = ExampleMetadata(
    id="dumbbell",
    name="Dumbbell",
    category="sports",
    keywords=["dumbbell", "weight", "gym", "fitness", "exercise"],
    description="Classic dumbbell: central grip bar with two weight discs.",
    techniques=["safe_revolve", "guarded_fillet"],
    nominal_dimensions_mm={"total_length": 300.0, "grip_diameter": 28.0, "weight_diameter": 110.0},
    difficulty="easy",
)

code = '''import cadquery as cq

total_l = 300.0
grip_d = 28.0
weight_d = 110.0
weight_thick = 40.0
grip_l = total_l - 2 * weight_thick

# Grip along Y axis
grip = (
    cq.Workplane("XZ", origin=(0, -grip_l / 2.0, 0))
    .circle(grip_d / 2.0)
    .extrude(grip_l)
)
body = grip

# Two weight discs at the ends
for y in (-total_l / 2.0, total_l / 2.0 - weight_thick):
    disc = (
        cq.Workplane("XZ", origin=(0, y, 0))
        .circle(weight_d / 2.0)
        .extrude(weight_thick)
    )
    body = body.union(disc)

try:
    body = body.edges().fillet(2.0)
except Exception:
    pass

# Translate so lowest point is Z=0
body = body.translate((0, 0, weight_d / 2.0))

result = body
'''
