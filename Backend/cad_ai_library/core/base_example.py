"""Optional base class for examples that want runtime validation.

Most example modules in `examples/` ship as plain `metadata` + `code`
pairs (simpler for the LLM to read). When an example benefits from
programmatic checks — e.g. bounding-box assertions or volume sanity
tests — it can subclass BaseExample and expose a `build()` method.
"""

from typing import Any, Dict

from .metadata import ExampleMetadata


class BaseExample:
    """Minimal convention for executable examples.

    Subclasses set a class-level `metadata` attribute and implement
    `build(**params) -> cq.Workplane`. The `validate()` helper runs a
    few cheap post-conditions (positive volume, sane bounding box).
    """

    metadata: ExampleMetadata

    def build(self, **params: Any):
        raise NotImplementedError

    def validate(self, result: Any) -> Dict[str, Any]:
        """Return a small report; raise on hard failures."""
        try:
            solid = result.val() if hasattr(result, "val") else result
            volume = float(solid.Volume())
            bb = solid.BoundingBox()
        except Exception as exc:  # pragma: no cover - defensive
            raise RuntimeError(f"validate() could not inspect result: {exc}") from exc

        if volume <= 0:
            raise RuntimeError(f"non-positive volume: {volume:.2f} mm^3")

        return {
            "volume_mm3": volume,
            "bbox_mm": (bb.xlen, bb.ylen, bb.zlen),
            "ok": True,
        }
