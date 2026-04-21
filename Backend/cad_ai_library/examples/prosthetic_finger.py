from ..core.metadata import ExampleMetadata

metadata = ExampleMetadata(
    id="prosthetic_finger",
    name="Prosthetic Finger",
    category="prosthetic",
    keywords=["prosthetic", "finger", "digit", "3d printed finger", "prosthesis", "partial hand"],
    description="Three-segment articulated prosthetic finger with pin joints and rounded tip.",
    techniques=["boolean_union", "boolean_cut"],
    nominal_dimensions_mm={"length": 85.0, "width": 16.0, "thickness": 14.0},
    difficulty="medium",
)

code = '''import cadquery as cq

W = 16.0
T = 14.0

def segment(length, x0):
    seg = cq.Workplane("XY").center(x0 + length / 2, 0).box(length, W, T, centered=(True, True, False))
    try:
        seg = seg.edges("|Z").fillet(3.0)
    except Exception:
        pass
    # Pivot hole at far end
    pivot = (cq.Workplane("YZ").workplane(offset=x0 + length - 4)
             .center(0, T / 2).circle(1.5).extrude(W + 2))
    return seg.cut(pivot)

# Proximal, middle, distal phalanges
prox = segment(35, 0)
mid = segment(28, 37)
dist = segment(20, 67)

# Distal rounded tip
tip = (cq.Workplane("XY").workplane(offset=0)
       .center(85, 0).circle(W / 2).extrude(T))
try:
    tip = tip.edges(">X").fillet(4.0)
except Exception:
    pass

# Pin axles at each joint
pin1 = (cq.Workplane("YZ").workplane(offset=33)
        .center(0, T / 2).circle(1.2).extrude(W + 4, both=True))
pin2 = (cq.Workplane("YZ").workplane(offset=63)
        .center(0, T / 2).circle(1.2).extrude(W + 4, both=True))

body = prox.union(mid).union(dist).union(tip).union(pin1).union(pin2)

# Tendon channel (underside bore through all segments)
tendon = cq.Workplane("XY").workplane(offset=T * 0.25).center(42, 0).rect(85, 2).extrude(2)
body = body.cut(tendon)

result = body

# --- Modern finishing pass (guarded) ---
try:
    result = result.edges("|Z").fillet(1.2)
except Exception:
    pass
try:
    result = result.faces(">Z").edges().chamfer(0.5)
except Exception:
    pass
try:
    result = result.faces("<Z").edges().fillet(0.8)
except Exception:
    pass
'''
