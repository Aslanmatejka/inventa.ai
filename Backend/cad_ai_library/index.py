"""Registry of all examples keyed by id, plus search helpers.

Each entry stores ``metadata`` and ``code`` lazily-loaded from the
``examples/`` subpackage. Importing this module does NOT import
CadQuery — it only touches dataclass metadata.
"""

from importlib import import_module
from typing import Dict, List, Tuple, Any

from .core.metadata import ExampleMetadata, CATEGORIES


_EXAMPLE_MODULES: Tuple[str, ...] = (
    "mug",
    "bottle",
    "vase",
    "electronics_enclosure",
    "desk_organizer",
    "bracket",
    "gear",
    "storage_box",
    "lamp",
    "drone_quadcopter",
    "phone_stand",
    # Batch 2
    "bowl",
    "tray",
    "pen_holder",
    "candle_holder",
    "flower_pot",
    "knob",
    "hinge",
    "keychain",
    "wall_hook",
    "coaster",
    "dice",
    "funnel",
    # Batch 3
    "spoon",
    "soap_dish",
    "cable_clip",
    "whistle",
    "speaker_grille",
    "ring",
    "car_toy",
    "name_plate",
    "book_end",
    "usb_cover",
    "washer",
    "pulley",
    # Batch 4
    "screwdriver_handle",
    "wrench",
    "stool",
    "picture_frame",
    "clip_board",
    "bird_house",
    "medicine_bottle",
    "syringe_body",
    "drawer_pull",
    "garden_stake",
    "shelf_bracket",
    "headphone_stand",
    # Batch 5
    "dumbbell",
    "frisbee",
    "dog_bowl",
    "guitar_pick",
    "capo",
    "bolt",
    "nut",
    "spring",
    "propeller",
    "lego_brick",
    "yoyo",
    "heart_box",
    # Batch 6
    "cutting_board",
    "rolling_pin",
    "measuring_cup",
    "watch_band_link",
    "glasses_case",
    "robot_arm_segment",
    "robot_gripper_finger",
    "rocket_fin",
    "rocket_nose_cone",
    "airplane_wing",
    "chess_pawn",
    "flashlight",
    # Batch 7
    "pipe_elbow",
    "faucet_handle",
    "funnel_strainer",
    "lens_mount",
    "boat_cleat",
    "column_greek",
    "arch_keystone",
    "tile_hex",
    "door_knob",
    "gopro_mount",
    "ball_bearing",
    "ice_cube_tray",
    # Batch 8
    "pill_organizer",
    "stethoscope_head",
    "inhaler_body",
    "hammer_head",
    "pliers_jaw",
    "allen_key",
    "watering_can",
    "seed_tray",
    "pencil_sharpener",
    "stapler",
    "tape_dispenser",
    "toothbrush_holder",
    # Batch 9
    "earbud_case",
    "speaker_cabinet",
    "microphone_body",
    "signet_ring",
    "pendant_heart",
    "earring_hoop",
    "crate_stackable",
    "pallet",
    "bottle_crate",
    "skateboard_deck",
    "bike_pedal",
    "planter_geometric",
    # Batch 10
    "pet_feeder",
    "cat_scratcher",
    "vent_grille",
    "duct_reducer",
    "smoke_detector",
    "fire_extinguisher",
    "hard_hat",
    "soap_pump_bottle",
    "toilet_paper_holder",
    "shower_head",
    "paint_can",
    "trash_can",
    # Batch 11
    "beaker",
    "test_tube_rack",
    "petri_dish",
    "camp_stove",
    "tent_stake",
    "carabiner",
    "wall_clock",
    "hourglass",
    "cookie_cutter",
    "wine_glass",
    "garden_gnome",
    "mailbox",
    # Batch 12
    "drumstick",
    "dice_d6",
    "meeple",
    "game_card_tray",
    "paint_brush",
    "paint_palette",
    "tractor_wheel",
    "milk_can",
    "wind_turbine_blade",
    "solar_panel",
    "anatomical_heart",
    "abacus",
    # Batch 13
    "aquarium_tank",
    "fishing_reel",
    "binoculars",
    "magnifying_glass",
    "keyboard_keycap",
    "computer_mouse",
    "snow_shovel_head",
    "ski_binding",
    "trophy_cup",
    "medal",
    "espresso_cup",
    "whiskey_tumbler",
    # Batch 14
    "harmonica",
    "maraca",
    "syringe",
    "iv_drip_bag",
    "road_cone",
    "life_ring",
    "anchor",
    "soccer_goal",
    "yoga_block",
    "kettlebell",
    "piggy_bank",
    "rubber_duck",
    # Batch 15
    "pliers",
    "screwdriver",
    "tape_measure",
    "spirit_level",
    "laptop_stand",
    "monitor_stand",
    "smart_plug",
    "doorbell",
    "thermostat_ring",
    "bird_feeder",
    "sundial",
    "weather_vane",
    # Batch 16 (car parts, guns, prosthetics, sculptures, phone covers, bottles)
    "piston",
    "brake_rotor",
    "steering_wheel",
    "revolver",
    "rifle_stock",
    "prosthetic_hand",
    "prosthetic_leg",
    "abstract_sculpture",
    "pedestal_bust",
    "phone_case_basic",
    "water_bottle",
    "wine_bottle",
    # Batch 17 (additional legal firearms)
    "taurus_gx4_toro",
    "diamondback_db9",
    "ruger_lcp_max",
    "ruger_lcp_ii",
    # Batch 18 (Glock family)
    "glock_17",
    "glock_19",
    "glock_19x",
    "glock_26",
    "glock_34",
    "glock_42",
    "glock_43",
    "glock_43x",
    "glock_44",
    "glock_45",
    # Batch 19 (additional prosthetics)
    "prosthetic_foot",
    "prosthetic_finger",
    "prosthetic_knee_joint",
    "prosthetic_eye",
    "prosthetic_ear",
    "split_hook_prosthetic",
    "myoelectric_forearm",
    "dental_crown",
    # Batch 20 (modern prosthetics)
    "running_blade_prosthetic",
    "bebionic_hand",
    "osseointegrated_implant",
    "cochlear_implant",
    "hip_implant",
    "spinal_cage_implant",
    "cranial_plate",
    "pacemaker",
    "transradial_socket",
    "exoskeleton_joint",
)


def _load_all() -> Dict[str, Dict[str, Any]]:
    registry: Dict[str, Dict[str, Any]] = {}
    for name in _EXAMPLE_MODULES:
        mod = import_module(f".examples.{name}", package=__package__)
        md: ExampleMetadata = getattr(mod, "metadata")
        code: str = getattr(mod, "code")
        registry[md.id] = {"metadata": md, "code": code, "module": f"{__package__}.examples.{name}"}
    return registry


REGISTRY: Dict[str, Dict[str, Any]] = _load_all()


def all_categories() -> List[str]:
    """Categories actually present in the registry (ordered)."""
    seen: Dict[str, None] = {}
    for entry in REGISTRY.values():
        seen[entry["metadata"].category] = None
    # Preserve canonical order where possible
    return [c for c in CATEGORIES if c in seen] + [c for c in seen if c not in CATEGORIES]


def search(query: str, *, limit: int = 3) -> List[Dict[str, Any]]:
    """Rank examples by keyword overlap against `query`.

    Returns a list of ``{id, score, metadata, code}`` sorted by score desc.
    Scoring is intentionally simple — the library is small enough that
    naive substring + keyword matching beats anything heavier.
    """
    q = (query or "").lower().strip()
    if not q:
        return []

    scored: List[Tuple[float, str]] = []
    # Techniques that produce smooth/modern geometry — tiebreaker bonus
    _MODERN_TECHNIQUES = {
        "revolve", "loft", "sweep", "spline", "fillet",
        "guarded_fillet", "ellipse", "threePointArc",
    }
    for ex_id, entry in REGISTRY.items():
        md: ExampleMetadata = entry["metadata"]
        score = 0.0
        # id / name hits
        if ex_id in q or ex_id.replace("_", " ") in q:
            score += 5.0
        if md.name.lower() in q:
            score += 4.0
        # keyword hits (each match worth 2, full-token worth 3)
        for kw in md.keywords:
            if kw.lower() in q:
                score += 3.0 if f" {kw.lower()} " in f" {q} " else 2.0
        # category hint
        if md.category in q:
            score += 1.0
        # Modernity tiebreaker: small bonus per curve-producing technique
        if score > 0:
            for tech in md.techniques or []:
                t_norm = tech.lower()
                for modern in _MODERN_TECHNIQUES:
                    if modern in t_norm:
                        score += 0.25
                        break
        if score > 0:
            scored.append((score, ex_id))

    scored.sort(key=lambda x: x[0], reverse=True)
    results: List[Dict[str, Any]] = []
    for score, ex_id in scored[:limit]:
        entry = REGISTRY[ex_id]
        results.append({
            "id": ex_id,
            "score": score,
            "metadata": entry["metadata"],
            "code": entry["code"],
        })
    return results
