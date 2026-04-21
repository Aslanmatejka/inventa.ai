"""CadQuery AI example library.

A curated collection of battle-tested CadQuery scripts that the AI can
retrieve, study, and adapt when generating new designs. Each example
exposes a `metadata` dict and a `code` string so the registry can
search by keyword/category and hand raw source to the LLM as a
few-shot demonstration.

Public API:
    from cad_ai_library import find_relevant, load_example, REGISTRY
"""

from .index import REGISTRY, search, all_categories
from .utils import load_example, find_relevant, validate_code

__all__ = [
    "REGISTRY",
    "search",
    "all_categories",
    "load_example",
    "find_relevant",
    "validate_code",
]
