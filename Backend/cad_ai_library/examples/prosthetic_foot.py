from ..core.metadata import ExampleMetadata

metadata = ExampleMetadata(
    id="prosthetic_foot",
    name="Prosthetic Foot (SACH)",
    category="prosthetic",
    keywords=["prosthetic", "foot", "sach", "amputee", "artificial foot", "prosthesis", "keel"],
    description="SACH-style prosthetic foot: foam-shaped outer foot shell with internal wooden keel and heel wedge.",
    techniques=["boolean_union", "guarded_fillet"],
    nominal_dimensions_mm={"length": 250.0, "width": 90.0, "height": 75.0},
    difficulty="medium",
)

code = '''import cadquery as cq

L = 250.0
W = 90.0
H = 75.0

# Foot-shaped base block
foot = cq.Workplane("XY").box(L, W, H, centered=(True, True, False))
try:
    foot = foot.edges("|Z").fillet(25.0)
except Exception:
    pass
try:
    foot = foot.edges(">Z").fillet(15.0)
except Exception:
    pass

# Toe taper (cut front-top angle)
toe_cut_pts = [(L/2, H), (L/2 - 60, H), (L/2, H * 0.35)]
toe_cut = (cq.Workplane("XZ").polyline(toe_cut_pts).close()
           .extrude(W + 2, both=True))
foot = foot.cut(toe_cut)

# Heel taper
heel_cut_pts = [(-L/2, H), (-L/2 + 40, H), (-L/2, H * 0.5)]
heel_cut = (cq.Workplane("XZ").polyline(heel_cut_pts).close()
            .extrude(W + 2, both=True))
foot = foot.cut(heel_cut)

# Ankle coupler on top (for pylon attachment)
ankle = (cq.Workplane("XY").workplane(offset=H)
         .center(-L * 0.1, 0).circle(22).extrude(18))
body = foot.union(ankle)

# Bolt hole for pylon
bolt = (cq.Workplane("XY").workplane(offset=H - 1)
        .center(-L * 0.1, 0).circle(6).extrude(20))
body = body.cut(bolt)

# Toe split slot (bottom)
slot = (cq.Workplane("XY").center(L * 0.25, 0).rect(L * 0.35, 3).extrude(10))
body = body.cut(slot)

result = body
'''
