from ..core.metadata import ExampleMetadata

metadata = ExampleMetadata(
    id="doorbell",
    name="Smart Doorbell",
    category="electronics",
    keywords=["doorbell", "ring", "camera", "smart doorbell", "video", "bell"],
    description="Wall doorbell with camera lens, speaker grille, and illuminated ring button.",
    techniques=["boolean_cut", "guarded_fillet"],
    nominal_dimensions_mm={"width": 55.0, "height": 130.0, "depth": 25.0},
    difficulty="easy",
)

code = '''import cadquery as cq

w = 55.0
h = 130.0
d = 25.0

body = cq.Workplane("XY").box(w, d, h, centered=(True, True, False))
try:
    body = body.edges().fillet(8.0)
except Exception:
    pass

# Camera lens (top)
lens_housing = (cq.Workplane("XZ").workplane(offset=-d/2)
                .center(0, h - 25).circle(14).extrude(5))
lens = (cq.Workplane("XZ").workplane(offset=-d/2 - 4)
        .center(0, h - 25).circle(7).extrude(3))
body = body.union(lens_housing).union(lens)

# Ring button (bottom)
ring_outer = (cq.Workplane("XZ").workplane(offset=-d/2)
              .center(0, 25).circle(14).extrude(2))
ring_cut = (cq.Workplane("XZ").workplane(offset=-d/2 - 3)
            .center(0, 25).circle(10).extrude(5))
body = body.union(ring_outer).cut(ring_cut)

btn = (cq.Workplane("XZ").workplane(offset=-d/2)
       .center(0, 25).circle(8).extrude(3))
body = body.union(btn)

# Speaker grille slots
for i in range(3):
    sl = (cq.Workplane("XZ").workplane(offset=-d/2 - 1)
          .center(0, h/2 - 5 + i * 6).rect(20, 1.5).extrude(3))
    body = body.cut(sl)

result = body
'''
