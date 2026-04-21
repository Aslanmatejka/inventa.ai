from ..core.metadata import ExampleMetadata

metadata = ExampleMetadata(
    id="hourglass",
    name="Hourglass",
    category="decorative",
    keywords=["hourglass", "sand", "timer", "sandglass", "decor"],
    description="Classic hourglass with two glass bulbs joined at a narrow waist between wooden end caps.",
    techniques=["safe_revolve"],
    nominal_dimensions_mm={"height": 180.0, "bulb_diameter": 70.0, "waist_diameter": 8.0},
    difficulty="medium",
)

code = '''import cadquery as cq

total_h = 180.0
bulb_d = 70.0
waist_d = 8.0
cap_d = bulb_d + 20
cap_h = 12.0

r_bulb = bulb_d / 2.0
r_waist = waist_d / 2.0

# Glass shape (two bulbs)
glass_profile = (
    cq.Workplane("XZ")
    .moveTo(0, cap_h)
    .lineTo(r_bulb, cap_h)
    .spline([(r_bulb * 0.85, total_h * 0.3),
             (r_waist + 1, total_h * 0.45),
             (r_waist, total_h / 2.0),
             (r_waist + 1, total_h * 0.55),
             (r_bulb * 0.85, total_h * 0.7),
             (r_bulb, total_h - cap_h)])
    .lineTo(0, total_h - cap_h)
    .close()
)
glass = glass_profile.revolve(360)

# Top and bottom caps (wooden disks)
bot_cap = cq.Workplane("XY").circle(cap_d / 2.0).extrude(cap_h)
top_cap = (
    cq.Workplane("XY", origin=(0, 0, total_h - cap_h))
    .circle(cap_d / 2.0)
    .extrude(cap_h)
)

# Three support posts between the caps
import math
for i in range(3):
    theta = 120 * i + 30
    x = (cap_d / 2.0 - 4) * math.cos(math.radians(theta))
    y = (cap_d / 2.0 - 4) * math.sin(math.radians(theta))
    post = (
        cq.Workplane("XY", origin=(x, y, cap_h))
        .circle(2.5)
        .extrude(total_h - 2 * cap_h)
    )
    glass = glass.union(post)

body = glass.union(bot_cap).union(top_cap)

result = body
'''
