"""One-off validator: exec every example's `code` string in a CadQuery
sandbox and report which ones fail. Mirrors the sandbox used by
parametric_cad_service._execute_cadquery_code.

Run from project root:
    python Backend/validate_cad_ai_library.py
"""
import sys
import traceback
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import cadquery as cq  # noqa
import math, copy  # noqa
try:
    import numpy as np  # noqa
except Exception:
    np = None
try:
    import cq_warehouse  # noqa
except Exception:
    cq_warehouse = None

from cad_ai_library import REGISTRY


def build_namespace():
    ns = {
        "cq": cq,
        "cadquery": cq,
        "math": math,
        "copy": copy,
        "__builtins__": __builtins__,
    }
    if np is not None:
        ns["np"] = np
        ns["numpy"] = np
    if cq_warehouse is not None:
        ns["cq_warehouse"] = cq_warehouse
    return ns


def run_one(example_id: str, code: str):
    ns = build_namespace()
    ns["_auto_fillet_max"] = 100.0  # match preprocessing injection
    try:
        exec(code, ns)
    except Exception as e:
        return False, f"{type(e).__name__}: {e}", traceback.format_exc()
    result = ns.get("result")
    if result is None:
        return False, "no `result` defined", ""
    # Verify it's something solid-ish
    try:
        val = result.val() if hasattr(result, "val") else result
        # Try a shallow op to ensure geometry is valid
        if hasattr(val, "Volume"):
            vol = abs(val.Volume())
            if vol < 1e-6:
                return False, f"empty result (volume={vol})", ""
    except Exception as e:
        return False, f"volume check failed: {e}", traceback.format_exc()
    return True, "ok", ""


def main():
    total = len(REGISTRY)
    failures = []
    print(f"Validating {total} examples...\n")
    for i, (ex_id, entry) in enumerate(sorted(REGISTRY.items()), 1):
        ok, msg, tb = run_one(ex_id, entry["code"])
        status = "OK " if ok else "FAIL"
        print(f"[{i:3d}/{total}] {status} {ex_id}: {msg}")
        if not ok:
            failures.append((ex_id, msg, tb))
    print(f"\n{'='*60}")
    print(f"Total: {total}  OK: {total - len(failures)}  FAIL: {len(failures)}")
    if failures:
        print("\nFailures:")
        for ex_id, msg, tb in failures:
            print(f"\n--- {ex_id} ---")
            print(msg)
    return 0 if not failures else 1


if __name__ == "__main__":
    sys.exit(main())
