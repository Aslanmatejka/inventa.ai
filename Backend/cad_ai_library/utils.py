"""Helpers used by the rest of the backend to consume this library."""

from typing import Dict, List, Optional, Any

from .index import REGISTRY, search
from .core.metadata import ExampleMetadata


def load_example(example_id: str) -> Dict[str, Any]:
    """Return ``{metadata, code}`` for a given example id. Raises KeyError."""
    entry = REGISTRY[example_id]
    return {"metadata": entry["metadata"], "code": entry["code"]}


def find_relevant(prompt: str, *, limit: int = 3) -> List[Dict[str, Any]]:
    """Top-N relevant examples for a natural-language prompt.

    Shape matches what the Claude few-shot injector expects:
        [{"id": str, "score": float, "metadata": ExampleMetadata, "code": str}]
    """
    return search(prompt, limit=limit)


# Same allowlist and forbidden-module list used by parametric_cad_service.
# Duplicated here so this package has no runtime dependency on services/.
_ALLOWED_IMPORTS = {
    "cadquery",
    "cq",
    "math",
    "copy",
    "cq_warehouse",
    "numpy",
    "np",
}
_FORBIDDEN_CALLS = ("eval(", "exec(", "open(", "__import__(", "file(")
_FORBIDDEN_MODULES = {"os", "sys", "subprocess", "socket", "shutil", "pathlib", "builtins"}


def validate_code(code: str) -> Dict[str, Any]:
    """Lightweight safety check mirroring ParametricCADService rules.

    Returns ``{"ok": bool, "errors": [..], "warnings": [..]}``.
    """
    import re

    errors: List[str] = []
    warnings: List[str] = []

    if not isinstance(code, str) or not code.strip():
        return {"ok": False, "errors": ["empty code"], "warnings": []}

    for bad in _FORBIDDEN_CALLS:
        if bad in code:
            errors.append(f"forbidden call: {bad}")

    import_pat = re.compile(r"^\s*(?:import\s+([\w\.]+)|from\s+([\w\.]+)\s+import)", re.M)
    for match in import_pat.finditer(code):
        mod = (match.group(1) or match.group(2)).split(".")[0]
        if mod in _FORBIDDEN_MODULES:
            errors.append(f"forbidden module: {mod}")
        elif mod not in _ALLOWED_IMPORTS:
            warnings.append(f"unrecognised import: {mod}")

    if "result" not in code:
        errors.append("missing `result = ...` assignment")

    return {"ok": not errors, "errors": errors, "warnings": warnings}
