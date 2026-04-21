from ..core.metadata import ExampleMetadata

metadata = ExampleMetadata(
    id="wine_bottle",
    name="Wine Bottle",
    category="container",
    keywords=["wine", "bottle", "wine bottle", "bordeaux", "glass", "alcohol"],
    description="Classic Bordeaux-style wine bottle: tall shoulder body with elongated neck and lip.",
    techniques=["revolve"],
    nominal_dimensions_mm={"diameter": 76.0, "height": 300.0},
    difficulty="easy",
)

code = '''import cadquery as cq

# Bordeaux outer profile
outer_pts = [
    (0, 0),
    (38, 0),
    (38, 5),       # small heel
    (38, 200),     # straight shoulder body
    (36, 215),     # shoulder curve start
    (14, 240),     # shoulder-to-neck
    (14, 290),     # neck straight
    (17, 296),     # lip flare
    (17, 300),
    (0, 300),
]
outer = cq.Workplane("XZ").polyline(outer_pts).close().revolve(360, (0, 0, 0), (0, 1, 0))

# Inner (punt + hollow)
inner_pts = [
    (0, 20),       # punt dome at bottom
    (32, 8),
    (35, 15),
    (35, 200),
    (33, 215),
    (11, 240),
    (11, 298),
    (0, 298),
]
inner = cq.Workplane("XZ").polyline(inner_pts).close().revolve(360, (0, 0, 0), (0, 1, 0))
body = outer.cut(inner)

# Foil band near top
foil = (cq.Workplane("XY").workplane(offset=260)
        .circle(18).circle(17).extrude(35))
body = body.union(foil)

result = body
'''
