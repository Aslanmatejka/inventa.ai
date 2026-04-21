from ..core.metadata import ExampleMetadata

metadata = ExampleMetadata(
    id="pet_feeder",
    name="Pet Food Bowl Stand",
    category="pet",
    keywords=["pet", "feeder", "dog", "cat", "bowl", "stand", "animal"],
    description="Elevated twin-bowl pet feeder with two round bowl recesses.",
    techniques=["guarded_fillet"],
    nominal_dimensions_mm={"length": 380.0, "width": 200.0, "height": 80.0, "bowl_diameter": 150.0},
    difficulty="easy",
)

code = '''import cadquery as cq

length = 380.0
width = 200.0
height = 80.0
bowl_d = 150.0
bowl_depth = 55.0

body = cq.Workplane("XY").box(length, width, height, centered=(True, True, False))
try:
    body = body.edges("|Z").fillet(18.0)
except Exception:
    pass
try:
    body = body.edges(">Z or <Z").fillet(4.0)
except Exception:
    pass

# Two bowl recesses
for dx in (-length * 0.25, length * 0.25):
    recess = (
        cq.Workplane("XY", origin=(dx, 0, height - bowl_depth))
        .circle(bowl_d / 2.0)
        .extrude(bowl_depth + 1)
    )
    body = body.cut(recess)

# Rubber-foot cutouts on the bottom (4 small discs)
for sx in (-1, 1):
    for sy in (-1, 1):
        foot = (
            cq.Workplane("XY", origin=(sx * (length / 2.0 - 20),
                                        sy * (width / 2.0 - 20),
                                        -0.1))
            .circle(9.0)
            .extrude(2.0)
        )
        body = body.cut(foot)

result = body
'''
