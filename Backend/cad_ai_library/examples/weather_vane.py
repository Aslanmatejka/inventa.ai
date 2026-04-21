from ..core.metadata import ExampleMetadata

metadata = ExampleMetadata(
    id="weather_vane",
    name="Weather Vane",
    category="outdoor",
    keywords=["weather", "vane", "wind", "arrow", "rooster", "direction"],
    description="Weather vane with directional arrow, center pivot, and N/S/E/W cross.",
    techniques=["boolean_union"],
    nominal_dimensions_mm={"height": 500.0, "arrow_length": 260.0},
    difficulty="medium",
)

code = '''import cadquery as cq

post_r = 8.0
post_h = 400.0
post = cq.Workplane("XY").circle(post_r).extrude(post_h)

# Pivot ball
pivot = (cq.Workplane("XY").workplane(offset=post_h)
         .sphere(14))
body = post.union(pivot)

# Directional cross (N S E W) just below pivot
for ang in [0, 90, 180, 270]:
    arm = (cq.Workplane("XY").workplane(offset=post_h - 30)
           .rect(60, 4).extrude(4))
    arm = arm.rotate((0, 0, post_h - 30), (0, 0, 1), ang)
    body = body.union(arm)

# Arrow at top
# Shaft
shaft = (cq.Workplane("XY").workplane(offset=post_h + 20)
         .rect(260, 4).extrude(4))
body = body.union(shaft)

# Arrow head (triangle)
head_pts = [(130, 0), (90, 20), (90, -20)]
head = (cq.Workplane("XY").workplane(offset=post_h + 20)
        .polyline(head_pts).close().extrude(4))
body = body.union(head)

# Arrow tail (notched)
tail_pts = [(-130, 0), (-90, 25), (-105, 0), (-90, -25)]
tail = (cq.Workplane("XY").workplane(offset=post_h + 20)
        .polyline(tail_pts).close().extrude(4))
body = body.union(tail)

result = body
'''
