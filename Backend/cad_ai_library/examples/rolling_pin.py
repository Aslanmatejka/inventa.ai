from ..core.metadata import ExampleMetadata

metadata = ExampleMetadata(
    id="rolling_pin",
    name="Rolling Pin",
    category="accessory",
    keywords=["rolling", "pin", "kitchen", "dough", "bake", "pastry"],
    description="Traditional rolling pin with central barrel and two grip handles.",
    techniques=["safe_revolve", "guarded_fillet"],
    nominal_dimensions_mm={"total_length": 400.0, "barrel_diameter": 60.0, "handle_diameter": 28.0},
    difficulty="easy",
)

code = '''import cadquery as cq

total_l = 400.0
barrel_l = 260.0
barrel_d = 60.0
handle_d = 28.0
handle_l = (total_l - barrel_l) / 2.0

# Revolve profile in XZ (all X >= 0)
profile = (
    cq.Workplane("XZ")
    .moveTo(0, 0)
    .lineTo(handle_d / 2.0, 0)
    .lineTo(handle_d / 2.0, handle_l - 4)
    .lineTo(barrel_d / 2.0, handle_l + 4)
    .lineTo(barrel_d / 2.0, handle_l + barrel_l - 4)
    .lineTo(handle_d / 2.0, handle_l + barrel_l + 4)
    .lineTo(handle_d / 2.0, total_l)
    .lineTo(0, total_l)
    .close()
)
body = profile.revolve(360)

try:
    body = body.edges().fillet(1.5)
except Exception:
    pass

# Lay it flat (rotate so long axis is along Y)
body = body.rotate((0, 0, 0), (1, 0, 0), 90).translate((0, 0, barrel_d / 2.0))

result = body
'''
