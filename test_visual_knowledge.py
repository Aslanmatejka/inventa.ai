"""
Test: product_visual_knowledge schema validation.

Ensures every category in CATEGORY_VISUAL_KNOWLEDGE has the required keys
and that the values are non-trivial strings.
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "Backend"))
os.environ.setdefault("ANTHROPIC_API_KEY", "sk-ant-test-placeholder")

from services.product_visual_knowledge import CATEGORY_VISUAL_KNOWLEDGE  # noqa: E402

REQUIRED_KEYS = {"visual_profile", "build_strategy", "recognition_features"}
MIN_LEN = 80  # characters — catches accidental empties / placeholders


def main():
    failures = []

    if not isinstance(CATEGORY_VISUAL_KNOWLEDGE, dict):
        print("❌ CATEGORY_VISUAL_KNOWLEDGE is not a dict")
        sys.exit(1)

    if len(CATEGORY_VISUAL_KNOWLEDGE) < 5:
        failures.append(f"only {len(CATEGORY_VISUAL_KNOWLEDGE)} categories defined; expected >= 5")

    for category, knowledge in CATEGORY_VISUAL_KNOWLEDGE.items():
        if not isinstance(knowledge, dict):
            failures.append(f"{category}: entry is not a dict")
            continue

        missing = REQUIRED_KEYS - set(knowledge.keys())
        if missing:
            failures.append(f"{category}: missing keys {sorted(missing)}")
            continue

        for key in REQUIRED_KEYS:
            value = knowledge[key]
            if not isinstance(value, str):
                failures.append(f"{category}.{key}: not a string ({type(value).__name__})")
            elif len(value) < MIN_LEN:
                failures.append(
                    f"{category}.{key}: suspiciously short ({len(value)} chars, min {MIN_LEN})"
                )

        # Optional: position_map must be a dict if present
        if "position_map" in knowledge and not isinstance(knowledge["position_map"], (dict, str)):
            failures.append(f"{category}.position_map: must be dict or str")

    if failures:
        print("❌ test_visual_knowledge failures:")
        for f in failures:
            print(f"   - {f}")
        sys.exit(1)

    print(
        f"✅ test_visual_knowledge: {len(CATEGORY_VISUAL_KNOWLEDGE)} categories, "
        f"all have required keys"
    )
    sys.exit(0)


if __name__ == "__main__":
    main()
