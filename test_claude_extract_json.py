"""
Test: claude_service._extract_json_from_response()

Exercises:
  1. Clean JSON (no fences)
  2. JSON wrapped in ```json ... ``` fences
  3. JSON wrapped in plain ``` ... ``` fences
  4. JSON with leading/trailing prose
  5. Malformed JSON → ValueError
  6. Truncated JSON (max_tokens cutoff) — best-effort repair or ValueError
"""
import os
import sys
import json

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "Backend"))
os.environ.setdefault("ANTHROPIC_API_KEY", "sk-ant-test-placeholder")

from services.claude_service import claude_service  # noqa: E402


def main():
    failures = []
    extract = claude_service._extract_json_from_response

    # --- 1. Clean JSON ---
    clean = '{"parameters": [], "code": "result = None", "explanation": {"design_intent": "x"}}'
    try:
        out = extract(clean)
        assert out["code"] == "result = None"
    except Exception as e:
        failures.append(f"clean JSON: {type(e).__name__}: {e}")

    # --- 2. ```json fenced ---
    fenced_json = "Here is the design:\n```json\n" + clean + "\n```\nDone."
    try:
        out = extract(fenced_json)
        assert out["code"] == "result = None", f"expected code, got {out}"
    except Exception as e:
        failures.append(f"```json fenced: {type(e).__name__}: {e}")

    # --- 3. Plain ``` fenced ---
    fenced_plain = "```\n" + clean + "\n```"
    try:
        out = extract(fenced_plain)
        assert out["code"] == "result = None"
    except Exception as e:
        failures.append(f"```plain fenced: {type(e).__name__}: {e}")

    # --- 4. Leading/trailing prose ---
    prosy = "Sure! Here's your design.\n\n" + clean + "\n\nLet me know if you want changes."
    try:
        out = extract(prosy)
        assert out["code"] == "result = None"
    except Exception as e:
        failures.append(f"prose wrapping: {type(e).__name__}: {e}")

    # --- 5. Malformed JSON ---
    bad = "Sorry, I could not generate a design."
    try:
        extract(bad)
        failures.append("malformed: expected ValueError, got none")
    except ValueError:
        pass
    except Exception as e:
        failures.append(f"malformed: expected ValueError, got {type(e).__name__}: {e}")

    # --- 6. Truncated JSON — acceptable outcomes: repaired dict OR ValueError ---
    truncated = '{"parameters": [], "code": "result = cq.Workplane(\\"XY\\").box(10, 10, 10).fillet'
    try:
        out = extract(truncated)
        # If repair succeeded, result must be a dict with 'code' key
        if not isinstance(out, dict) or "code" not in out:
            failures.append(f"truncated: repaired but missing 'code' key: {out}")
    except ValueError:
        pass  # acceptable — unrepairable
    except Exception as e:
        failures.append(f"truncated: unexpected {type(e).__name__}: {e}")

    if failures:
        print("❌ test_claude_extract_json failures:")
        for f in failures:
            print(f"   - {f}")
        sys.exit(1)

    print("✅ test_claude_extract_json: 6 extraction scenarios validated")
    sys.exit(0)


if __name__ == "__main__":
    main()
