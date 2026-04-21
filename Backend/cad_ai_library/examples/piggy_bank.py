from ..core.metadata import ExampleMetadata

metadata = ExampleMetadata(
    id="piggy_bank",
    name="Piggy Bank",
    category="toy",
    keywords=["piggy", "bank", "savings", "pig", "coin", "money", "toy"],
    description="Stylized piggy bank: round body, four short legs, snout with two nostrils, coin slot on top.",
    techniques=["safe_revolve"],
    nominal_dimensions_mm={"body_length": 140.0, "body_diameter": 90.0, "total_height": 110.0},
    difficulty="medium",
)

code = '''import cadquery as cq

body_l = 140.0
body_d = 90.0
leg_h = 20.0
leg_d = 16.0

# Body is an oval (ellipsoid approximated by revolving an ellipse profile)
r = body_d / 2.0
profile = (
    cq.Workplane("XZ")
    .ellipse(body_l / 2.0, r)
    .translate((0, 0, leg_h + r))
)
# Revolve around X axis by revolving profile (which is in XZ around Z) — we want a pig pointing along X.
# Use sphere scaled: create sphere then stretch via scale trick: sweep an ellipse ring.
body = (
    cq.Workplane("XY", origin=(0, 0, leg_h + r))
    .ellipseArc(body_l / 2.0, r, 0, 180)
    .close()
    .revolve(360, (0, 0, 0), (1, 0, 0))
)
# The above revolve sweeps around X axis — which gives ellipsoid. Move it back to correct Z.
# Use simpler: sphere, then scale along X via extrude/loft? Fall back to just a sphere with snout.
body = cq.Workplane("XY", origin=(0, 0, leg_h + r)).sphere(r)
# Stretch by union with an extra cylinder along X
stretch = (
    cq.Workplane("YZ", origin=(-body_l / 2.0 + r, 0, leg_h + r))
    .circle(r * 0.95)
    .extrude(body_l - 2 * r)
)
body = body.union(stretch)
# Tail cap sphere
tail_sphere = cq.Workplane("XY", origin=(-body_l / 2.0 + r, 0, leg_h + r)).sphere(r * 0.95)
body = body.union(tail_sphere)

# Four legs
leg_offsets = [(-body_l * 0.25, -r * 0.6),
               (body_l * 0.25, -r * 0.6),
               (-body_l * 0.25, r * 0.6),
               (body_l * 0.25, r * 0.6)]
for (lx, ly) in leg_offsets:
    leg = cq.Workplane("XY", origin=(lx, ly, 0)).circle(leg_d / 2.0).extrude(leg_h + 5)
    body = body.union(leg)

# Snout (small cylinder on +X end)
snout = (
    cq.Workplane("YZ", origin=(body_l / 2.0 - r * 0.3, 0, leg_h + r))
    .circle(r * 0.35)
    .extrude(r * 0.4)
)
body = body.union(snout)
# Nostrils (two small holes in the snout)
for sy in (-r * 0.12, r * 0.12):
    nostril = (
        cq.Workplane("YZ", origin=(body_l / 2.0 + r * 0.1, sy, leg_h + r))
        .circle(1.8)
        .extrude(-6)
    )
    body = body.cut(nostril)

# Coin slot on top
slot = (
    cq.Workplane("XY", origin=(0, 0, leg_h + 2 * r - 4))
    .rect(30, 3)
    .extrude(10)
)
body = body.cut(slot)

# Curly tail (small torus offset)
tail = (
    cq.Workplane("XZ", origin=(-body_l / 2.0 - 4, 0, leg_h + r * 1.5))
    .circle(6)
    .extrude(4)
    .translate((0, -2, 0))
)
tail_hole = (
    cq.Workplane("XZ", origin=(-body_l / 2.0 - 4, 0, leg_h + r * 1.5))
    .circle(3)
    .extrude(5)
    .translate((0, -2.5, 0))
)
body = body.union(tail).cut(tail_hole)

result = body
'''
