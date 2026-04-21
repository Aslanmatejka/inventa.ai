"""Typed metadata describing each CadQuery example.

Kept dependency-free (dataclass only) so the library can be imported
from anywhere in the backend without pulling CadQuery into memory
unless an example is actually loaded.
"""

from dataclasses import dataclass, field, asdict
from typing import List, Dict, Any


@dataclass
class ExampleMetadata:
    """Machine-readable description of a single CadQuery example."""

    id: str                       # stable slug, e.g. "mug"
    name: str                     # human-readable title
    category: str                 # top-level bucket (see CATEGORIES below)
    keywords: List[str] = field(default_factory=list)
    description: str = ""         # 1-2 sentence summary
    techniques: List[str] = field(default_factory=list)
    # Nominal dimensions in mm so the search layer can filter by scale
    nominal_dimensions_mm: Dict[str, float] = field(default_factory=dict)
    difficulty: str = "intermediate"  # "beginner" | "intermediate" | "advanced"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


# Canonical category list — keep in sync with product_visual_knowledge.py
CATEGORIES = (
    "container",
    "enclosure",
    "organizer",
    "mechanical",
    "decorative",
    "electronics",
    "lighting",
    "vehicle",
    "accessory",
    "furniture",
    "outdoor",
    "sports",
    "musical",
    "fastener",
    "toy",
    "wearable",
    "robotics",
    "aerospace",
    "plumbing",
    "optics",
    "marine",
    "architecture",
    "medical",
    "tool",
    "stationery",
    "packaging",
    "pet",
    "hvac",
    "safety",
    "sanitary",
    "lab",
    "camping",
    "music_accessory",
    "gaming",
    "art_supplies",
    "agriculture",
    "energy",
    "educational",
    "aquarium",
    "fishing",
    "photography",
    "computing",
    "winter",
    "award",
    "drinkware",
    "fitness",
    "automotive",
    "firearm",
    "prosthetic",
    "sculpture",
    "phone_case",
)
