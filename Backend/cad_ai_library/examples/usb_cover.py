from ..core.metadata import ExampleMetadata

metadata = ExampleMetadata(
    id="usb_cover",
    name="USB Port Cover",
    category="accessory",
    keywords=["usb", "cover", "cap", "port", "plug", "dust"],
    description="Friction-fit dust cover for a USB-A port with pull tab.",
    techniques=["guarded_fillet"],
    nominal_dimensions_mm={"length": 18.0, "width": 14.0, "plug_depth": 8.0, "wall": 1.2},
    difficulty="easy",
)

code = '''import cadquery as cq

plug_l = 12.4
plug_w = 4.8
plug_depth = 8.0
wall = 1.2
outer_l = plug_l + 2 * wall
outer_w = plug_w + 2 * wall
flange_l = outer_l + 4.0
flange_w = outer_w + 2.0
flange_t = 2.0
tab_l = 10.0
tab_w = 5.0
tab_t = 1.5

flange = cq.Workplane("XY").box(flange_l, flange_w, flange_t, centered=(True, True, False))
try:
    flange = flange.edges("|Z").fillet(1.5)
except Exception:
    pass

plug = (
    cq.Workplane("XY", origin=(0, 0, flange_t))
    .box(outer_l, outer_w, plug_depth, centered=(True, True, False))
)
try:
    plug = plug.edges("|Z").fillet(0.8)
except Exception:
    pass

plug_cav = (
    cq.Workplane("XY", origin=(0, 0, flange_t + wall))
    .box(outer_l - 2 * wall, outer_w - 2 * wall, plug_depth, centered=(True, True, False))
)
plug = plug.cut(plug_cav)

body = flange.union(plug)

tab = (
    cq.Workplane("XY", origin=(-(flange_l / 2.0 + tab_l / 2.0), 0, 0))
    .box(tab_l, tab_w, tab_t, centered=(True, True, False))
)
try:
    tab = tab.edges("|Z").fillet(1.0)
except Exception:
    pass
tab = (
    tab.faces(">Z").workplane()
    .center(0, 0)
    .hole(2.0)
)
body = body.union(tab)

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
