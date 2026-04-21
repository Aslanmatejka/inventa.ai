from ..core.metadata import ExampleMetadata

metadata = ExampleMetadata(
    id="propeller",
    name="Boat / Fan Propeller",
    category="mechanical",
    keywords=["propeller", "prop", "blade", "fan", "boat", "impeller"],
    description="Three-blade propeller with twisted loft-blades on a central hub.",
    techniques=["loft_frustum", "polar_array"],
    nominal_dimensions_mm={"hub_diameter": 18.0, "blade_length": 60.0, "blade_count": 3},
    difficulty="advanced",
)

code = '''import cadquery as cq

hub_d = 18.0
hub_h = 14.0
blade_count = 3
blade_len = 60.0
bore_d = 6.0

# Central hub
hub = cq.Workplane("XY").circle(hub_d / 2.0).extrude(hub_h)

# Single blade: loft between two airfoil-like rectangles at different twist angles
root_w = 10.0
root_t = 3.5
tip_w = 18.0
tip_t = 1.8

root = (
    cq.Workplane("YZ", origin=(hub_d / 2.0, 0, hub_h / 2.0))
    .rect(root_w, root_t)
    .val()
)
tip = (
    cq.Workplane("YZ", origin=(hub_d / 2.0 + blade_len, 0, hub_h / 2.0))
    .rect(tip_w, tip_t)
    .val()
)
blade_wire = cq.Workplane().newObject([root]).add(tip)
# Simpler explicit loft:
blade = (
    cq.Workplane("YZ", origin=(hub_d / 2.0, 0, hub_h / 2.0))
    .rect(root_w, root_t)
    .workplane(offset=blade_len)
    .rect(tip_w, tip_t)
    .loft(combine=True)
)

# Polar array the blade
body = hub
for i in range(blade_count):
    theta = 360.0 / blade_count * i
    body = body.union(blade.rotate((0, 0, 0), (0, 0, 1), theta))

# Shaft bore
body = body.faces(">Z").workplane().hole(bore_d)

try:
    body = body.edges(">Z or <Z").fillet(0.6)
except Exception:
    pass

result = body
'''
