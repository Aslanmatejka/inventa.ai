"""
Test: rebuild_with_parameters() marker parsing and error paths.

Validates:
  1. Missing script file → FileNotFoundError
  2. Script without GEOMETRY GENERATION marker → ValueError
  3. Script without EXPORT marker → ValueError
  4. Script without blank line after marker → ValueError
  5. Marker strings match the exact literals in _generate_editable_script()
"""
import os
import sys
import asyncio
import tempfile
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "Backend"))

os.environ.setdefault("ANTHROPIC_API_KEY", "sk-ant-test-placeholder")

from services.parametric_cad_service import parametric_cad_service  # noqa: E402

GEO_MARKER = "# ═══════════════════════════════════════════════════════════════\n# GEOMETRY GENERATION"
EXPORT_MARKER = "# ═══════════════════════════════════════════════════════════════\n# EXPORT"


def _run(coro):
    return asyncio.get_event_loop().run_until_complete(coro) if sys.version_info < (3, 10) \
        else asyncio.run(coro)


def _write_script(tmp_dir: Path, build_id: str, body: str) -> Path:
    path = tmp_dir / f"{build_id}_parametric.py"
    path.write_text(body, encoding="utf-8")
    return path


def main():
    failures = []
    original_output_dir = parametric_cad_service.output_dir
    tmp = Path(tempfile.mkdtemp(prefix="inventa_rebuild_test_"))
    parametric_cad_service.output_dir = tmp

    try:
        # --- 1. Missing file ---
        try:
            _run(parametric_cad_service.rebuild_with_parameters("nonexistent_build", {}))
            failures.append("missing file: expected FileNotFoundError, got none")
        except FileNotFoundError:
            pass
        except Exception as e:
            failures.append(f"missing file: expected FileNotFoundError, got {type(e).__name__}: {e}")

        # --- 2. Missing GEOMETRY GENERATION marker ---
        _write_script(tmp, "no_geo", "w = 10\n\n" + EXPORT_MARKER + "\n")
        try:
            _run(parametric_cad_service.rebuild_with_parameters("no_geo", {"w": 20}))
            failures.append("no geo marker: expected ValueError, got none")
        except ValueError as e:
            if "GEOMETRY GENERATION" not in str(e):
                failures.append(f"no geo marker: wrong error message: {e}")
        except Exception as e:
            failures.append(f"no geo marker: expected ValueError, got {type(e).__name__}: {e}")

        # --- 3. Missing EXPORT marker ---
        _write_script(
            tmp, "no_export",
            "w = 10\n" + GEO_MARKER + "\n\nresult = None\n",
        )
        try:
            _run(parametric_cad_service.rebuild_with_parameters("no_export", {"w": 20}))
            failures.append("no export marker: expected ValueError, got none")
        except ValueError as e:
            if "EXPORT" not in str(e):
                failures.append(f"no export marker: wrong message: {e}")
        except Exception as e:
            failures.append(f"no export marker: expected ValueError, got {type(e).__name__}: {e}")

        # --- 4. Missing blank line after marker ---
        bad = "w = 10\n" + GEO_MARKER + "\nresult = None\n" + EXPORT_MARKER + "\n"
        _write_script(tmp, "no_blank", bad)
        try:
            _run(parametric_cad_service.rebuild_with_parameters("no_blank", {"w": 20}))
            failures.append("no blank line: expected ValueError, got none")
        except ValueError as e:
            if "corrupted" not in str(e).lower() and "blank line" not in str(e).lower():
                failures.append(f"no blank line: wrong message: {e}")
        except Exception as e:
            # Could fail differently depending on CQ availability; only ValueError is a pass
            failures.append(f"no blank line: expected ValueError, got {type(e).__name__}: {e}")

        # --- 5. Marker literals match the script generator ---
        sample = parametric_cad_service._generate_editable_script(
            code="result = cq.Workplane('XY').box(10, 10, 10)",
            parameters=[{"name": "w", "default": 10, "min": 1, "max": 100, "unit": "mm", "description": "w"}],
            explanation={},
        )
        if GEO_MARKER not in sample:
            failures.append("generated script is missing GEOMETRY GENERATION marker literal")
        if EXPORT_MARKER not in sample:
            failures.append("generated script is missing EXPORT marker literal")
    finally:
        parametric_cad_service.output_dir = original_output_dir

    if failures:
        print("❌ test_rebuild failures:")
        for f in failures:
            print(f"   - {f}")
        sys.exit(1)

    print("✅ test_rebuild: marker parsing + error paths validated")
    # Force-exit to avoid OCC kernel segfaults at interpreter shutdown on Windows
    os._exit(0)


if __name__ == "__main__":
    main()
