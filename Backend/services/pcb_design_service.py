"""
PCB Design Service — AI-Powered PCB Layout Generation

Generates PCB designs from natural language descriptions:
1. AI creates a component placement + routing plan
2. Service generates KiCad .kicad_pcb files (S-expression format)
3. Service creates 3D CadQuery models of the populated board
4. Bridges PCB dimensions → enclosure design (mounting holes, connector cutouts)

No KiCad installation required — files are generated as text.
"""

import cadquery as cq
import math
import json
import uuid
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))
from config import settings
from services.pcb_component_library import (
    COMPONENTS, PCB_SPECS, BOARD_PRESETS,
    search_components, get_component, format_component_reference,
    get_edge_mount_components,
)


class PCBDesignService:
    """Generate PCB layouts and 3D models from AI-designed specifications."""

    def __init__(self):
        self.output_dir = settings.CAD_DIR
        self.pcb_dir = Path(settings.EXPORTS_DIR) / "pcb"
        self.pcb_dir.mkdir(parents=True, exist_ok=True)

    # ═══════════════════════════════════════════════════════════════════════
    # PUBLIC API
    # ═══════════════════════════════════════════════════════════════════════

    async def generate_pcb_from_spec(
        self,
        pcb_spec: Dict[str, Any],
        build_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Generate PCB files from an AI-produced specification.

        Args:
            pcb_spec: {
                "board": {
                    "width": float,
                    "height": float,
                    "thickness": 1.6,
                    "corner_radius": 2.0,
                    "mounting_holes": [{"x": ..., "y": ..., "diameter": 3.2}, ...],
                    "color": "green",
                    "layers": 2,
                },
                "components": [
                    {
                        "id": "esp32_wroom",    # from component library
                        "ref": "U1",            # reference designator
                        "x": 30.0, "y": 20.0,  # center position on board
                        "rotation": 0,          # degrees
                        "side": "front",        # "front" or "back"
                        "value": "",            # optional value (e.g., "10K")
                    },
                    ...
                ],
                "traces": [
                    {
                        "net": "VCC",
                        "width": 0.5,
                        "points": [[x1,y1], [x2,y2], ...],
                        "layer": "F.Cu",
                    },
                    ...
                ],
                "zones": [
                    {
                        "net": "GND",
                        "layer": "B.Cu",
                        "type": "fill",   # ground pour
                    },
                    ...
                ],
            }
            build_id: Optional build ID.

        Returns:
            {
                "buildId": str,
                "kicadFile": str,       # path to .kicad_pcb
                "stlFile": str,         # path to 3D STL of populated board
                "stepFile": str,        # path to 3D STEP of populated board
                "boardDimensions": {...},
                "componentList": [...],
                "enclosureSpec": {...},  # dimensions + cutouts for enclosure generation
                "success": True,
            }
        """
        if not build_id:
            build_id = str(uuid.uuid4())

        board = pcb_spec.get("board", {})
        components = pcb_spec.get("components", [])
        traces = pcb_spec.get("traces", [])
        zones = pcb_spec.get("zones", [])

        board_w = board.get("width", 50.0)
        board_h = board.get("height", 50.0)
        board_t = board.get("thickness", 1.6)
        corner_r = board.get("corner_radius", 1.5)
        mounting_holes = board.get("mounting_holes", [])
        board_color = board.get("color", "green")
        layer_count = board.get("layers", 2)

        # ── 1. Generate KiCad PCB file ──
        kicad_path = self.pcb_dir / f"{build_id}.kicad_pcb"
        kicad_content = self._generate_kicad_pcb(
            board_w, board_h, board_t, corner_r, layer_count,
            mounting_holes, components, traces, zones
        )
        kicad_path.write_text(kicad_content, encoding="utf-8")
        print(f"📋 KiCad PCB generated: {kicad_path}")

        # ── 2. Generate 3D CadQuery model ──
        cad_result = self._generate_3d_model(
            build_id, board_w, board_h, board_t, corner_r,
            mounting_holes, components, board_color
        )

        # ── 3. Generate enclosure specification ──
        enclosure_spec = self._generate_enclosure_spec(
            board_w, board_h, board_t, mounting_holes, components
        )

        # ── 4. Generate CadQuery code for the PCB (so it can be edited) ──
        pcb_code = self._generate_pcb_cadquery_code(
            board_w, board_h, board_t, corner_r,
            mounting_holes, components, board_color
        )

        return {
            "buildId": build_id,
            "kicadFile": f"/exports/pcb/{build_id}.kicad_pcb",
            "stlFile": cad_result["stlFile"],
            "stepFile": cad_result["stepFile"],
            "boardDimensions": {
                "width": board_w,
                "height": board_h,
                "thickness": board_t,
                "cornerRadius": corner_r,
            },
            "componentList": [
                {
                    "ref": c.get("ref", "?"),
                    "id": c.get("id", "unknown"),
                    "name": COMPONENTS.get(c.get("id", ""), {}).get("name", c.get("id", "")),
                    "x": c.get("x", 0),
                    "y": c.get("y", 0),
                    "side": c.get("side", "front"),
                }
                for c in components
            ],
            "enclosureSpec": enclosure_spec,
            "pcbCode": pcb_code,
            "success": True,
        }

    def generate_enclosure_for_pcb(
        self,
        pcb_result: Dict[str, Any],
        enclosure_style: str = "box",
        wall_thickness: float = 2.0,
        clearance: float = 1.0,
    ) -> Dict[str, str]:
        """
        Generate CadQuery code for an enclosure that fits this PCB.

        Args:
            pcb_result: Output from generate_pcb_from_spec()
            enclosure_style: "box", "rounded", "snap_fit", "screw_mount"
            wall_thickness: Wall thickness in mm
            clearance: Extra clearance around PCB in mm

        Returns:
            CadQuery code string for the enclosure + lid.
        """
        spec = pcb_result.get("enclosureSpec", {})
        board = pcb_result.get("boardDimensions", {})

        bw = board.get("width", 50) + 2 * (wall_thickness + clearance)
        bh = board.get("height", 50) + 2 * (wall_thickness + clearance)
        bt = board.get("thickness", 1.6)
        max_comp_h = spec.get("maxComponentHeight", 10.0)
        total_h = bt + max_comp_h + clearance + wall_thickness * 2 + 2  # base + PCB + comps + lid

        cutouts = spec.get("connectorCutouts", [])
        mounting = spec.get("mountingPosts", [])

        code = self._generate_enclosure_code(
            bw, bh, total_h, wall_thickness, clearance,
            bt, mounting, cutouts, enclosure_style
        )
        return {"code": code, "style": enclosure_style}

    # ═══════════════════════════════════════════════════════════════════════
    # KICAD FILE GENERATION
    # ═══════════════════════════════════════════════════════════════════════

    def _generate_kicad_pcb(
        self,
        board_w: float, board_h: float, board_t: float,
        corner_r: float, layer_count: int,
        mounting_holes: List[Dict], components: List[Dict],
        traces: List[Dict], zones: List[Dict],
    ) -> str:
        """Generate a KiCad .kicad_pcb S-expression file."""

        # Layer definitions
        if layer_count <= 2:
            layers = [
                '(0 "F.Cu" signal)', '(31 "B.Cu" signal)',
                '(36 "B.SilkS" user)', '(37 "F.SilkS" user)',
                '(38 "B.Mask" user)', '(39 "F.Mask" user)',
                '(44 "Edge.Cuts" user)',
            ]
        else:
            layers = [
                '(0 "F.Cu" signal)', '(1 "In1.Cu" signal)',
                '(2 "In2.Cu" signal)', '(31 "B.Cu" signal)',
                '(36 "B.SilkS" user)', '(37 "F.SilkS" user)',
                '(38 "B.Mask" user)', '(39 "F.Mask" user)',
                '(44 "Edge.Cuts" user)',
            ]

        layers_str = "\n    ".join(layers)

        # Board outline (Edge.Cuts)
        if corner_r > 0:
            outline = self._kicad_rounded_rect_outline(board_w, board_h, corner_r)
        else:
            outline = self._kicad_rect_outline(board_w, board_h)

        # Mounting holes as footprints
        holes_str = ""
        for i, hole in enumerate(mounting_holes):
            holes_str += self._kicad_mounting_hole(
                hole["x"], hole["y"],
                hole.get("diameter", 3.2),
                f"MH{i+1}"
            )

        # Component footprints (simplified — reference + placement)
        comps_str = ""
        for comp in components:
            comp_info = COMPONENTS.get(comp.get("id", ""), {})
            if comp_info:
                comps_str += self._kicad_component_footprint(
                    comp.get("ref", "U?"),
                    comp_info,
                    comp.get("x", 0),
                    comp.get("y", 0),
                    comp.get("rotation", 0),
                    comp.get("side", "front"),
                )

        # Traces
        traces_str = ""
        for trace in traces:
            points = trace.get("points", [])
            width = trace.get("width", 0.25)
            layer = trace.get("layer", "F.Cu")
            net = trace.get("net", "")
            for i in range(len(points) - 1):
                p1, p2 = points[i], points[i + 1]
                traces_str += f'  (segment (start {p1[0]} {p1[1]}) (end {p2[0]} {p2[1]}) (width {width}) (layer "{layer}") (net 0))\n'

        # Ground zones
        zones_str = ""
        for zone in zones:
            layer = zone.get("layer", "B.Cu")
            zones_str += f"""  (zone (net 0) (net_name "{zone.get('net', 'GND')}") (layer "{layer}") (hatch edge 0.508)
    (fill yes (thermal_gap 0.508) (thermal_bridge_width 0.508))
    (polygon (pts
      (xy 0 0) (xy {board_w} 0) (xy {board_w} {board_h}) (xy 0 {board_h})
    ))
  )\n"""

        return f"""(kicad_pcb (version 20221018) (generator "cad-ai-builder")

  (general
    (thickness {board_t})
  )

  (layers
    {layers_str}
  )

  (setup
    (pad_to_mask_clearance 0.05)
    (aux_axis_origin 0 0)
    (grid_origin 0 0)
  )

  (net 0 "")
  (net 1 "GND")
  (net 2 "VCC")

{outline}
{holes_str}
{comps_str}
{traces_str}
{zones_str}
)
"""

    def _kicad_rect_outline(self, w: float, h: float) -> str:
        """Generate rectangular board outline."""
        return f"""  (gr_line (start 0 0) (end {w} 0) (layer "Edge.Cuts") (width 0.05))
  (gr_line (start {w} 0) (end {w} {h}) (layer "Edge.Cuts") (width 0.05))
  (gr_line (start {w} {h}) (end 0 {h}) (layer "Edge.Cuts") (width 0.05))
  (gr_line (start 0 {h}) (end 0 0) (layer "Edge.Cuts") (width 0.05))"""

    def _kicad_rounded_rect_outline(self, w: float, h: float, r: float) -> str:
        """Generate rounded-rectangle board outline."""
        lines = []
        # Top edge
        lines.append(f'  (gr_line (start {r} 0) (end {w-r} 0) (layer "Edge.Cuts") (width 0.05))')
        # Top-right corner arc
        lines.append(f'  (gr_arc (start {w-r} {r}) (mid {w-r+r*0.707} {r-r*0.707}) (end {w} {r}) (layer "Edge.Cuts") (width 0.05))')
        # Right edge
        lines.append(f'  (gr_line (start {w} {r}) (end {w} {h-r}) (layer "Edge.Cuts") (width 0.05))')
        # Bottom-right corner arc
        lines.append(f'  (gr_arc (start {w-r} {h-r}) (mid {w-r+r*0.707} {h-r+r*0.707}) (end {w-r} {h}) (layer "Edge.Cuts") (width 0.05))')
        # Bottom edge (right to left)
        lines.append(f'  (gr_line (start {w-r} {h}) (end {r} {h}) (layer "Edge.Cuts") (width 0.05))')
        # Bottom-left corner arc
        lines.append(f'  (gr_arc (start {r} {h-r}) (mid {r-r*0.707} {h-r+r*0.707}) (end 0 {h-r}) (layer "Edge.Cuts") (width 0.05))')
        # Left edge
        lines.append(f'  (gr_line (start 0 {h-r}) (end 0 {r}) (layer "Edge.Cuts") (width 0.05))')
        # Top-left corner arc
        lines.append(f'  (gr_arc (start {r} {r}) (mid {r-r*0.707} {r-r*0.707}) (end {r} 0) (layer "Edge.Cuts") (width 0.05))')
        return "\n".join(lines)

    def _kicad_mounting_hole(self, x: float, y: float, diameter: float, ref: str) -> str:
        """Generate a mounting hole footprint."""
        pad_d = diameter + 1.0  # annular ring
        return f"""
  (footprint "MountingHole:MountingHole_{diameter:.1f}mm" (layer "F.Cu")
    (at {x} {y})
    (property "Reference" "{ref}" (at 0 -{diameter} 0) (layer "F.SilkS") (effects (font (size 1 1) (thickness 0.15))))
    (pad "" thru_hole circle (at 0 0) (size {pad_d} {pad_d}) (drill {diameter}) (layers "*.Cu" "*.Mask"))
  )
"""

    def _kicad_component_footprint(
        self, ref: str, comp: Dict, x: float, y: float,
        rotation: float, side: str
    ) -> str:
        """Generate a simplified component footprint placement."""
        layer = "F.Cu" if side == "front" else "B.Cu"
        silk = "F.SilkS" if side == "front" else "B.SilkS"
        body = comp.get("body", {"x": 5, "y": 5, "z": 2})
        bx, by = body["x"] / 2, body["y"] / 2
        fp_name = comp.get("footprint", f"Package:Generic_{body['x']}x{body['y']}mm")

        pads = ""
        pin_count = comp.get("pins", 2)
        pitch = comp.get("pitch", 2.54)
        mounting = comp.get("mounting", "smd")

        if mounting == "smd":
            # Simple dual-row SMD pads
            pad_w = min(pitch * 0.6, 1.0)
            pad_h = min(pitch * 0.5, 0.8)
            cols = min(pin_count // 2, 20)
            for i in range(cols):
                px = -((cols - 1) * pitch / 2) + i * pitch
                pads += f'    (pad {i+1} smd rect (at {px:.2f} {-by-0.5:.2f}) (size {pad_w:.2f} {pad_h:.2f}) (layers "{layer}" "F.Paste" "F.Mask"))\n'
                pads += f'    (pad {i+1+cols} smd rect (at {px:.2f} {by+0.5:.2f}) (size {pad_w:.2f} {pad_h:.2f}) (layers "{layer}" "F.Paste" "F.Mask"))\n'
        else:
            # Through-hole pads
            drill = min(pitch * 0.4, 1.0)
            pad_d = drill + 0.6
            cols = min(pin_count, 20)
            for i in range(cols):
                px = -((cols - 1) * pitch / 2) + i * pitch
                pads += f'    (pad {i+1} thru_hole circle (at {px:.2f} 0) (size {pad_d:.2f} {pad_d:.2f}) (drill {drill:.2f}) (layers "*.Cu" "*.Mask"))\n'

        rot_str = f" {rotation}" if rotation else ""

        return f"""
  (footprint "{fp_name}" (layer "{layer}")
    (at {x} {y}{rot_str})
    (property "Reference" "{ref}" (at 0 {-by-2} 0) (layer "{silk}") (effects (font (size 1 1) (thickness 0.15))))
    (fp_rect (start {-bx} {-by}) (end {bx} {by}) (layer "F.Fab") (width 0.1))
    (fp_text user "{ref}" (at 0 0) (layer "{silk}") (effects (font (size 0.8 0.8) (thickness 0.12))))
{pads}  )
"""

    # ═══════════════════════════════════════════════════════════════════════
    # 3D MODEL GENERATION (CadQuery)
    # ═══════════════════════════════════════════════════════════════════════

    def _generate_3d_model(
        self,
        build_id: str,
        board_w: float, board_h: float, board_t: float,
        corner_r: float, mounting_holes: List[Dict],
        components: List[Dict], board_color: str,
    ) -> Dict[str, str]:
        """Create a 3D CadQuery model of the populated PCB."""

        # ── Board substrate ──
        if corner_r > 0:
            board = (
                cq.Workplane("XY")
                .rect(board_w, board_h)
                .extrude(board_t)
            )
            try:
                fillet_r = min(corner_r, board_w * 0.25, board_h * 0.25)
                board = board.edges("|Z").fillet(fillet_r)
            except Exception:
                pass
        else:
            board = cq.Workplane("XY").box(board_w, board_h, board_t, centered=(True, True, False))

        # ── Mounting holes ──
        for hole in mounting_holes:
            hx = hole["x"] - board_w / 2
            hy = hole["y"] - board_h / 2
            hd = hole.get("diameter", 3.2)
            try:
                board = (
                    board.faces(">Z").workplane()
                    .center(hx, hy)
                    .hole(hd)
                )
            except Exception:
                pass

        # ── Components as 3D bodies ──
        result = board
        for comp in components:
            comp_info = COMPONENTS.get(comp.get("id", ""))
            if not comp_info:
                continue

            body = comp_info.get("body", {"x": 5, "y": 5, "z": 2})
            cx = comp.get("x", 0) - board_w / 2
            cy = comp.get("y", 0) - board_h / 2
            side = comp.get("side", "front")
            rotation = comp.get("rotation", 0)

            # Create component body
            comp_body = cq.Workplane("XY").box(
                body["x"], body["y"], body["z"],
                centered=(True, True, False)
            )

            # Position on board
            if side == "front":
                comp_body = comp_body.translate((cx, cy, board_t))
            else:
                comp_body = comp_body.translate((cx, cy, -body["z"]))

            # Rotation (around Z axis at component center)
            if rotation:
                comp_body = comp_body.rotate((cx, cy, 0), (cx, cy, 1), rotation)

            try:
                result = result.union(comp_body)
            except Exception as e:
                print(f"⚠️ Failed to union component {comp.get('ref', '?')}: {e}")

        # ── Export ──
        step_path = self.output_dir / f"{build_id}.step"
        stl_path = self.output_dir / f"{build_id}.stl"

        try:
            cq.exporters.export(result, str(step_path))
        except Exception as e:
            print(f"⚠️ STEP export failed: {e}")

        try:
            cq.exporters.export(result, str(stl_path),
                                exportType="STL", tolerance=0.1, angularTolerance=0.1)
        except Exception:
            try:
                cq.exporters.export(result, str(stl_path))
            except Exception as e:
                print(f"⚠️ STL export failed: {e}")

        return {
            "stlFile": f"/exports/cad/{build_id}.stl",
            "stepFile": f"/exports/cad/{build_id}.step",
        }

    # ═══════════════════════════════════════════════════════════════════════
    # ENCLOSURE SPECIFICATION
    # ═══════════════════════════════════════════════════════════════════════

    def _generate_enclosure_spec(
        self,
        board_w: float, board_h: float, board_t: float,
        mounting_holes: List[Dict], components: List[Dict],
    ) -> Dict[str, Any]:
        """
        Analyze PCB and generate specifications for a matching enclosure.
        Returns dimensions, mounting post locations, and connector cutout positions.
        """
        # Find max component height (above and below board)
        max_top_h = 0.0
        max_bot_h = 0.0
        connector_cutouts = []

        for comp in components:
            comp_info = COMPONENTS.get(comp.get("id", ""))
            if not comp_info:
                continue

            body = comp_info.get("body", {"x": 5, "y": 5, "z": 2})
            side = comp.get("side", "front")

            if side == "front":
                max_top_h = max(max_top_h, body["z"])
            else:
                max_bot_h = max(max_bot_h, body["z"])

            # Edge-mounted connectors need enclosure cutouts
            if comp_info.get("edge_mount") or comp_info.get("mating_face"):
                mf = comp_info.get("mating_face", body)
                cutout = {
                    "ref": comp.get("ref", "?"),
                    "name": comp_info.get("name", ""),
                    "x": comp.get("x", 0),
                    "y": comp.get("y", 0),
                    "side": side,
                }
                if "diameter" in mf:
                    cutout["shape"] = "circle"
                    cutout["diameter"] = mf["diameter"]
                else:
                    cutout["shape"] = "rect"
                    cutout["width"] = mf.get("x", body["x"])
                    cutout["height"] = mf.get("y", mf.get("z", body["z"]))

                # Determine which enclosure wall this connector faces
                cx, cy = comp.get("x", 0), comp.get("y", 0)
                edge = self._nearest_edge(cx, cy, board_w, board_h)
                cutout["wall"] = edge

                connector_cutouts.append(cutout)

            # Displays need windows
            if comp_info.get("display_area"):
                da = comp_info["display_area"]
                connector_cutouts.append({
                    "ref": comp.get("ref", "?"),
                    "name": comp_info.get("name", ""),
                    "x": comp.get("x", 0),
                    "y": comp.get("y", 0),
                    "shape": "rect",
                    "width": da["x"] + 1.0,   # +1mm margin
                    "height": da["y"] + 1.0,
                    "wall": "top",  # display windows go in the lid
                    "side": "front",
                })

        # Mounting posts match PCB mounting holes
        mounting_posts = [
            {
                "x": h["x"],
                "y": h["y"],
                "screwDiameter": h.get("diameter", 3.2),
                "postDiameter": h.get("diameter", 3.2) + 3.0,
                "postHeight": max_bot_h + 2.0,  # raise PCB above bottom components
            }
            for h in mounting_holes
        ]

        return {
            "boardWidth": board_w,
            "boardHeight": board_h,
            "boardThickness": board_t,
            "maxComponentHeight": max_top_h,
            "maxBottomHeight": max_bot_h,
            "connectorCutouts": connector_cutouts,
            "mountingPosts": mounting_posts,
            "recommendedWallThickness": 2.0,
            "recommendedClearance": 1.0,
        }

    def _nearest_edge(self, x: float, y: float, w: float, h: float) -> str:
        """Determine which board edge a point is nearest to."""
        distances = {
            "front": y,         # bottom edge (y=0)
            "back": h - y,      # top edge (y=h)
            "left": x,          # left edge (x=0)
            "right": w - x,     # right edge (x=w)
        }
        return min(distances, key=distances.get)

    # ═══════════════════════════════════════════════════════════════════════
    # CADQUERY CODE GENERATION
    # ═══════════════════════════════════════════════════════════════════════

    def _generate_pcb_cadquery_code(
        self,
        board_w: float, board_h: float, board_t: float,
        corner_r: float, mounting_holes: List[Dict],
        components: List[Dict], board_color: str,
    ) -> str:
        """Generate editable CadQuery Python code for the PCB model."""

        # Build component placement code
        comp_lines = []
        for comp in components:
            comp_info = COMPONENTS.get(comp.get("id", ""))
            if not comp_info:
                continue
            body = comp_info["body"]
            ref = comp.get("ref", "U?")
            cx = comp.get("x", 0)
            cy = comp.get("y", 0)
            side = comp.get("side", "front")
            name = comp_info["name"]

            comp_lines.append(f"""
# {ref}: {name} ({body['x']}x{body['y']}x{body['z']}mm)
{ref.lower()}_body = cq.Workplane("XY").box({body['x']}, {body['y']}, {body['z']}, centered=(True, True, False))""")

            if side == "front":
                comp_lines.append(f"{ref.lower()}_body = {ref.lower()}_body.translate(({cx} - board_width/2, {cy} - board_height/2, pcb_thickness))")
            else:
                comp_lines.append(f"{ref.lower()}_body = {ref.lower()}_body.translate(({cx} - board_width/2, {cy} - board_height/2, -{body['z']}))")

            comp_lines.append(f"result = result.union({ref.lower()}_body)")

        components_code = "\n".join(comp_lines)

        # Build mounting hole code
        hole_lines = []
        for i, hole in enumerate(mounting_holes):
            hx = hole["x"]
            hy = hole["y"]
            hd = hole.get("diameter", 3.2)
            hole_lines.append(f"result = result.faces('>Z').workplane().center({hx} - board_width/2, {hy} - board_height/2).hole({hd})")

        holes_code = "\n".join(hole_lines) if hole_lines else "# No mounting holes"

        return f"""import cadquery as cq
import math

# ═══════════════════════════════════════════════════════════════
# PCB PARAMETERS
# ═══════════════════════════════════════════════════════════════
board_width = {board_w}     # mm
board_height = {board_h}    # mm
pcb_thickness = {board_t}   # mm (standard 1.6mm)
corner_radius = {corner_r}  # mm

# ═══════════════════════════════════════════════════════════════
# GEOMETRY GENERATION
# ═══════════════════════════════════════════════════════════════

# ── PCB Substrate ──
result = cq.Workplane("XY").rect(board_width, board_height).extrude(pcb_thickness)
try:
    fillet_r = min(corner_radius, board_width * 0.25, board_height * 0.25)
    if fillet_r > 0.1:
        result = result.edges("|Z").fillet(fillet_r)
except Exception:
    pass

# ── Mounting Holes ──
{holes_code}

# ── Components ──
{components_code}

# ═══════════════════════════════════════════════════════════════
# EXPORT
# ═══════════════════════════════════════════════════════════════
"""

    def _generate_enclosure_code(
        self,
        enc_w: float, enc_h: float, enc_total_h: float,
        wall_t: float, clearance: float, board_t: float,
        mounting: List[Dict], cutouts: List[Dict],
        style: str,
    ) -> str:
        """Generate CadQuery code for a PCB enclosure."""

        # Mounting post code
        post_lines = []
        for m in mounting:
            px = m["x"]
            py = m["y"]
            pd = m.get("postDiameter", 6.0)
            ph = m.get("postHeight", 4.0)
            sd = m.get("screwDiameter", 3.2)
            post_lines.append(f"""
# Mounting post at ({px}, {py})
post = cq.Workplane("XY").cylinder({ph}, {pd/2})
post = post.translate(({px} - enc_width/2 + wall_t + clearance, {py} - enc_height/2 + wall_t + clearance, wall_t))
try:
    base_body = base_body.union(post)
except Exception:
    pass
# Screw hole in post
try:
    base_body = base_body.faces(">Z").workplane().center({px} - enc_width/2 + wall_t + clearance, {py} - enc_height/2 + wall_t + clearance).hole({sd * 0.8})
except Exception:
    pass""")

        posts_code = "\n".join(post_lines) if post_lines else "# No mounting posts"

        # Connector cutout code
        cutout_lines = []
        for c in cutouts:
            if c.get("wall") == "top":
                # Window in lid
                cutout_lines.append(f"""
# {c.get('ref', '?')}: {c.get('name', 'connector')} window in lid
try:
    cx = {c.get('x', 0)} - enc_width/2 + wall_t + clearance
    cy = {c.get('y', 0)} - enc_height/2 + wall_t + clearance
    lid = lid.faces(">Z").workplane().center(cx, cy).rect({c.get('width', 10)}, {c.get('height', 5)}).cutBlind(-wall_t * 1.5)
except Exception:
    pass""")
            else:
                wall = c.get("wall", "front")
                if c.get("shape") == "circle":
                    cutout_lines.append(f"""
# {c.get('ref', '?')}: {c.get('name', 'connector')} ({wall} wall, circular)
try:
    base_body = base_body.faces("{self._wall_selector(wall)}").workplane().circle({c.get('diameter', 6) / 2}).cutBlind(-wall_t * 3)
except Exception:
    pass""")
                else:
                    cutout_lines.append(f"""
# {c.get('ref', '?')}: {c.get('name', 'connector')} ({wall} wall, rectangular)
try:
    base_body = base_body.faces("{self._wall_selector(wall)}").workplane().rect({c.get('width', 10)}, {c.get('height', 5)}).cutBlind(-wall_t * 3)
except Exception:
    pass""")

        cutouts_code = "\n".join(cutout_lines) if cutout_lines else "# No connector cutouts"

        corner_fillet = min(wall_t, 2.0) if style in ("rounded", "snap_fit") else 0

        return f"""import cadquery as cq
import math

# ═══════════════════════════════════════════════════════════════
# ENCLOSURE PARAMETERS (auto-generated from PCB spec)
# ═══════════════════════════════════════════════════════════════
enc_width = {enc_w:.1f}      # mm (board + walls + clearance)
enc_height = {enc_h:.1f}     # mm
enc_total_h = {enc_total_h:.1f}  # mm (total internal height)
wall_t = {wall_t:.1f}        # mm wall thickness
clearance = {clearance:.1f}  # mm clearance around PCB
lid_height = {wall_t + 5:.1f}  # mm lid overlap

base_height = enc_total_h - lid_height

# ═══════════════════════════════════════════════════════════════
# GEOMETRY GENERATION
# ═══════════════════════════════════════════════════════════════

# ── Base (bottom half) ──
base_body = cq.Workplane("XY").box(enc_width, enc_height, base_height, centered=(True, True, False))
base_body = base_body.shell(-wall_t)  # hollow it out from top
{"try:\\n    base_body = base_body.edges('|Z').fillet(" + str(corner_fillet) + ")\\nexcept Exception:\\n    pass" if corner_fillet > 0 else "# Square corners"}

# ── Mounting Posts ──
{posts_code}

# ── Connector Cutouts (base walls) ──
{cutouts_code}

# ── Lid ──
lid = cq.Workplane("XY").box(enc_width, enc_height, lid_height, centered=(True, True, False))
# Inner lip for snap/press fit
lip = cq.Workplane("XY").box(enc_width - wall_t*2 - 0.3, enc_height - wall_t*2 - 0.3, wall_t, centered=(True, True, False))
lid = lid.union(lip.translate((0, 0, -wall_t)))
{"try:\\n    lid = lid.edges('|Z').fillet(" + str(corner_fillet) + ")\\nexcept Exception:\\n    pass" if corner_fillet > 0 else "# Square corners"}

# Position lid above base (for preview — in reality it sits on top)
lid = lid.translate((0, 0, base_height + 5))  # offset for visibility

result = base_body.union(lid)

# ═══════════════════════════════════════════════════════════════
# EXPORT
# ═══════════════════════════════════════════════════════════════
"""

    def _wall_selector(self, wall: str) -> str:
        """Convert wall name to CadQuery face selector."""
        selectors = {
            "front": "<Y",
            "back": ">Y",
            "left": "<X",
            "right": ">X",
            "top": ">Z",
            "bottom": "<Z",
        }
        return selectors.get(wall, "<Y")

    # ═══════════════════════════════════════════════════════════════════════
    # PCB SYSTEM PROMPT (for Claude AI)
    # ═══════════════════════════════════════════════════════════════════════

    def get_pcb_system_prompt(self) -> str:
        """Return the system prompt section for PCB-aware designs."""
        # Build compact component reference
        comp_ref = []
        for key, comp in COMPONENTS.items():
            body = comp["body"]
            comp_ref.append(
                f"  {key}: {comp['name']} | {body['x']}x{body['y']}x{body['z']}mm | "
                f"{comp['pins']}pin {comp['mounting']} | pitch={comp.get('pitch','?')}mm"
            )
        comp_list = "\n".join(comp_ref)

        board_ref = []
        for key, preset in BOARD_PRESETS.items():
            if key == "custom":
                continue
            board_ref.append(f"  {key}: {preset['name']} ({preset['width']}x{preset['height']}mm)")
        board_list = "\n".join(board_ref)

        return f"""
═══ PCB DESIGN CAPABILITY ═══
You can design PCBs alongside mechanical enclosures. When the user asks for an
electronic product (IoT device, sensor box, controller, etc.), generate BOTH:
1. A pcb_spec JSON describing the board layout
2. CadQuery code for the matching enclosure with connector cutouts

PCB SPEC FORMAT (return as "pcb_spec" key in your response JSON):
{{
  "board": {{
    "width": 60.0, "height": 40.0, "thickness": 1.6,
    "corner_radius": 2.0, "color": "green", "layers": 2,
    "mounting_holes": [{{"x": 3.5, "y": 3.5, "diameter": 3.2}}, ...]
  }},
  "components": [
    {{"id": "esp32_wroom", "ref": "U1", "x": 30, "y": 20, "rotation": 0, "side": "front"}},
    ...
  ],
  "traces": [
    {{"net": "VCC", "width": 0.5, "points": [[x1,y1],[x2,y2]], "layer": "F.Cu"}},
    ...
  ],
  "zones": [
    {{"net": "GND", "layer": "B.Cu", "type": "fill"}}
  ]
}}

AVAILABLE COMPONENTS:
{comp_list}

BOARD PRESETS:
{board_list}

PCB PLACEMENT RULES:
1. Place components by center position (x, y) in mm from board origin (0,0 = bottom-left)
2. Edge-mount connectors (USB, barrel jack, audio) go flush with board edge
3. Keep antenna areas (ESP32, nRF24) free from ground plane and near board edge
4. Place decoupling caps (100nF) within 5mm of MCU power pins
5. Mounting holes at corners, inset by ~3.5mm
6. Ground zone on back copper layer (B.Cu)
7. Power traces >= 0.5mm, signal traces >= 0.25mm
8. Keep minimum 0.5mm clearance between components
"""

    def get_pcb_detection_keywords(self) -> List[str]:
        """Keywords that suggest the user wants PCB design."""
        return [
            "pcb", "circuit board", "printed circuit", "electronics",
            "iot device", "iot sensor", "sensor board", "microcontroller",
            "esp32", "arduino", "raspberry pi", "stm32", "rp2040",
            "schematic", "circuit", "electronic", "pcba",
            "development board", "breakout board", "shield",
            "with electronics", "with pcb", "with circuit",
            "smart device", "connected device", "wifi device",
            "bluetooth device", "sensor hub", "control board",
        ]


# ── Singleton ─────────────────────────────────────────────────────────────
pcb_design_service = PCBDesignService()
