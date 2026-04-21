from ..core.metadata import ExampleMetadata

metadata = ExampleMetadata(
    id="spinal_cage_implant",
    name="Spinal Fusion Cage",
    category="prosthetic",
    keywords=["spinal", "spine", "fusion cage", "interbody", "plif", "tlif", "lumbar", "orthopedic implant", "titanium cage", "prosthetic"],
    description="Interbody fusion cage: kidney-bean shaped hollow titanium cage with porous walls and graft window.",
    techniques=["boolean_cut", "guarded_fillet"],
    nominal_dimensions_mm={"length": 28.0, "width": 12.0, "height": 11.0},
    difficulty="medium",
)

code = '''import cadquery as cq

L = 28.0
W = 12.0
H = 11.0

# Kidney-bean outer shape: combine two circles + a box
left = cq.Workplane("XY").center(-L/2 + W/2, 0).circle(W/2).extrude(H)
right = cq.Workplane("XY").center(L/2 - W/2, 0).circle(W/2).extrude(H)
middle = cq.Workplane("XY").box(L - W, W, H, centered=(True, True, False))
cage = left.union(right).union(middle)

# Concave back edge (bite out to make kidney shape)
bite = (cq.Workplane("XY").center(0, W/2 + 3).circle(6).extrude(H + 2))
cage = cage.cut(bite)

# Central graft window (large rectangular hole)
graft = cq.Workplane("XY").center(0, 0).rect(L - W - 2, W - 4).extrude(H + 2)
cage = cage.cut(graft)

# Porous side windows (lateral ports)
for x_sign in (-1, 1):
    port = (cq.Workplane("XZ").workplane(offset=-x_sign * (W/2 + 0.1))
            .center(x_sign * L * 0.25, H/2).rect(8, 5).extrude(W + 2))
    cage = cage.cut(port)

# Anti-migration teeth on top and bottom
for z in (H - 1, 1):
    for xi in [-8, 0, 8]:
        tooth = (cq.Workplane("XY").workplane(offset=z)
                 .center(xi, 0).rect(2, 6).extrude(1))
        cage = cage.union(tooth)

# Insertion tool threaded hole (anterior)
bore = (cq.Workplane("XZ").workplane(offset=-W/2 - 1)
        .center(0, H/2).circle(2).extrude(W + 2))
cage = cage.cut(bore)

try:
    cage = cage.edges("|Z").fillet(0.6)
except Exception:
    pass

result = cage
'''
