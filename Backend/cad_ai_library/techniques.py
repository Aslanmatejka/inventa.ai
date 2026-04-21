"""Reusable CadQuery technique snippets.

A reference sheet of patterns the AI should use verbatim when it
recognises the corresponding problem. Keep each snippet minimal,
self-contained, and comment-annotated so it doubles as documentation.

Exposed as ``TECHNIQUES`` (dict) and ``get_technique(name)``.
"""

from typing import Dict


TECHNIQUES: Dict[str, Dict[str, str]] = {
    "grounding": {
        "when": "Every model should sit on Z=0 so the slicer/printer sees the bed plane.",
        "snippet": (
            "body = cq.Workplane(\"XY\").box(L, W, H, centered=(True, True, False))  # Z=0 is ground\n"
        ),
    },
    "shell_cavity": {
        "when": "Hollow out a closed body to create a cup/enclosure. Shell the TOP face, not the whole body.",
        "snippet": (
            "body = body.faces(\">Z\").shell(-wall_thickness)  # negative = inward\n"
        ),
    },
    "guarded_fillet": {
        "when": "Fillets fail if radius exceeds adjacent geometry. Always wrap in try/except and clamp.",
        "snippet": (
            "try:\n"
            "    body = body.edges(\">Z\").fillet(min(r, wall * 0.45))\n"
            "except Exception:\n"
            "    pass  # skip fillet if it's invalid\n"
        ),
    },
    "safe_revolve": {
        "when": "Revolve profiles MUST stay on one side of the axis (all X >= 0). Crossing causes negative volume.",
        "snippet": (
            "profile = (cq.Workplane(\"XZ\")\n"
            "    .moveTo(0, 0)\n"
            "    .lineTo(r_base, 0)\n"
            "    .spline([(r_belly, h*0.4), (r_neck, h*0.8), (r_lip, h)])\n"
            "    .lineTo(0, h)\n"
            "    .close()\n"
            ")\n"
            "result = profile.revolve(360)\n"
        ),
    },
    "stacked_rings_threads": {
        "when": "Fake external threads without a helical sweep (which frequently self-intersects in OCC).",
        "snippet": (
            "for i in range(turns):\n"
            "    z = neck_base_z + i * pitch\n"
            "    ring = cq.Workplane(\"XY\", origin=(0,0,z)).circle(r_outer+depth).circle(r_outer).extrude(thick)\n"
            "    neck = neck.union(ring)\n"
        ),
    },
    "loft_frustum": {
        "when": "Cone-like transitions (shoulder of bottle, lamp shade, funnel).",
        "snippet": (
            "frustum = (cq.Workplane(\"XY\", origin=(0,0,z0))\n"
            "    .circle(r_bottom)\n"
            "    .workplane(offset=h)\n"
            "    .circle(r_top)\n"
            "    .loft(combine=True)\n"
            ")\n"
        ),
    },
    "polar_array": {
        "when": "Gear teeth, bolt circles, dividers — anywhere N copies need to sit around a central axis.",
        "snippet": (
            "for i in range(n):\n"
            "    theta = 360.0 / n * i\n"
            "    assembly = assembly.union(feature.rotate((0,0,0), (0,0,1), theta))\n"
        ),
    },
    "cbore_hole": {
        "when": "Countersunk / counterbored mounting holes on a flat face.",
        "snippet": (
            "body = body.faces(\">Z\").workplane().pushPoints(pts).cboreHole(d_shaft, d_head, depth)\n"
        ),
    },
    "centered_grounding_only_on_box": {
        "when": "Only `.box()` accepts `centered=`. Remove it from `.extrude()`, `.rect()`, `.circle()`.",
        "snippet": (
            "# WRONG: .rect(a, b, centered=True).extrude(h, centered=True)\n"
            "# RIGHT: .rect(a, b).extrude(h)\n"
        ),
    },
    "verify_bbox": {
        "when": "After build, verify bbox matches declared parameters to within ~15%.",
        "snippet": (
            "bb = result.val().BoundingBox()\n"
            "assert bb.zlen > declared_height * 0.5, f\"collapsed Z: {bb.zlen}\"\n"
        ),
    },
}


def get_technique(name: str) -> Dict[str, str]:
    """Return the named technique or raise KeyError."""
    return TECHNIQUES[name]


def list_techniques() -> Dict[str, str]:
    """Return {name: when} for browsing."""
    return {k: v["when"] for k, v in TECHNIQUES.items()}
