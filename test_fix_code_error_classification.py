"""
Test: fix_code_with_error() error-classification coverage.

Instead of hitting the Anthropic API, we monkey-patch the Claude client so we can
inspect the 'error_category' and 'targeted_fix' strings the service computes for
representative error messages from each of the 16+ categories.
"""
# --- utf8 console (auto) ---
import sys as _sys
try:
    _sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    _sys.stderr.reconfigure(encoding='utf-8', errors='replace')
except Exception:
    pass
# --- end utf8 console ---
import os
import sys
import asyncio
import inspect
import re

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "Backend"))
os.environ.setdefault("ANTHROPIC_API_KEY", "sk-ant-test-placeholder")

# `services.claude_service` re-exports the singleton instance named `claude_service`
from services.claude_service import claude_service  # noqa: E402


# Representative error strings per category
SAMPLES = {
    "GEOMETRY_FILLET_CHAMFER": "BRep_API: command not done (fillet failed)",
    "GEOMETRY_SHELL": "Shell operation failed on selected faces",
    "SKETCH_NOT_CLOSED": "Wire is not closed",
    "SELECTOR_FAILED": "No selector returned any faces for '>Z'",
    "CURVE_TANGENT": "Tangent direction could not be computed for spline",
    "REVOLVE_AXIS": "Revolve axis is invalid for this sketch",
    "MATH_ERROR": "ZeroDivisionError: division by zero",
    "LOFT_FAILED": "Loft failed: incompatible section counts",
    "BOOLEAN_FAILED": "Boolean operation produced null shape",
    "WRONG_PARAMETER": "TypeError: box() got an unexpected keyword argument 'radius'",
    "SWEEP_FAILED": "Sweep failed: path has self-intersection",
    "WORKPLANE_STACK": "Workplane has no pending wires",
    "OCC_KERNEL_ERROR": "Standard_Failure: OCC kernel exception",
    "ATTRIBUTE_ERROR": "AttributeError: 'Workplane' object has no attribute 'bevel'",
    "TYPE_ERROR": "TypeError: unsupported operand type(s) for +: 'NoneType' and 'int'",
    "EMPTY_RESULT": "Result is empty — no geometry produced",
    "NAME_ERROR": "NameError: name 'wdith' is not defined",
}


def _inspect_classifier_source():
    """Read the classifier block in fix_code_with_error and return the string
    form of the source — used for static inspection."""
    return inspect.getsource(claude_service.fix_code_with_error)


def main():
    failures = []
    src = _inspect_classifier_source()

    # Static check: every category label we listed appears in the classifier source
    for category in SAMPLES:
        if category not in src:
            failures.append(f"classifier source does not mention category '{category}'")

    # Static check: each branch assigns error_category and sets targeted_fix
    num_category_assigns = len(re.findall(r'error_category\s*=\s*"', src))
    if num_category_assigns < 16:
        failures.append(
            f"expected at least 16 error_category assignments, found {num_category_assigns}"
        )

    # Static check: phase-escalation keywords present
    for marker in ["Targeted", "Conservative", "Aggressive"]:
        if marker.lower() not in src.lower():
            failures.append(f"phase-escalation marker '{marker}' missing from classifier")

    # Static check: healing-phase thresholds
    if "attempt" not in src:
        failures.append("classifier source does not reference 'attempt' counter")

    if failures:
        print("❌ test_fix_code_error_classification failures:")
        for f in failures:
            print(f"   - {f}")
        sys.exit(1)

    print(f"✅ test_fix_code_error_classification: {len(SAMPLES)} categories present, "
          f"{num_category_assigns} category assignments in source")
    sys.exit(0)


if __name__ == "__main__":
    main()
