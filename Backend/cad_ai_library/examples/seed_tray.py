from ..core.metadata import ExampleMetadata

metadata = ExampleMetadata(
    id="seed_tray",
    name="Seed Starter Tray",
    category="outdoor",
    keywords=["seed", "tray", "planter", "garden", "nursery", "cell", "propagator"],
    description="4x6 cell seed starter tray with drainage holes in each cell.",
    techniques=["loft_frustum"],
    nominal_dimensions_mm={"length": 240.0, "width": 160.0, "height": 45.0, "cells": "4x6"},
    difficulty="medium",
)

code = '''import cadquery as cq

length = 240.0
width = 160.0
height = 45.0
wall = 2.0
rows = 4
cols = 6
drain_d = 4.0

body = cq.Workplane("XY").box(length, width, height, centered=(True, True, False))
try:
    body = body.edges("|Z").fillet(3.0)
except Exception:
    pass

cell_x = (length - 2 * wall) / cols
cell_y = (width - 2 * wall) / rows
top_x = cell_x - 2
top_y = cell_y - 2
bot_x = top_x * 0.65
bot_y = top_y * 0.65

for i in range(cols):
    for j in range(rows):
        cx = -length / 2.0 + wall + cell_x * (i + 0.5)
        cy = -width / 2.0 + wall + cell_y * (j + 0.5)
        cavity = (
            cq.Workplane("XY", origin=(cx, cy, wall))
            .rect(bot_x, bot_y)
            .workplane(offset=height - wall + 0.1)
            .rect(top_x, top_y)
            .loft(combine=True)
        )
        body = body.cut(cavity)
        # Drain hole
        drain = (
            cq.Workplane("XY", origin=(cx, cy, -0.1))
            .circle(drain_d / 2.0)
            .extrude(wall + 0.3)
        )
        body = body.cut(drain)

result = body
'''
