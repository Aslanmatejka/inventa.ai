"""
Test: config.Settings — env loading, typing, and defaults.

Validates the pydantic Settings class accepts expected fields, returns correct
types, and produces the right derived values.
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "Backend"))
os.environ.setdefault("ANTHROPIC_API_KEY", "sk-ant-test-placeholder")

from config import Settings, settings  # noqa: E402


def main():
    failures = []

    # --- Required field types ---
    if not isinstance(settings.CORS_ORIGINS, str):
        failures.append(f"CORS_ORIGINS not str: {type(settings.CORS_ORIGINS).__name__}")

    if not isinstance(settings.PORT, int):
        failures.append(f"PORT not int: {type(settings.PORT).__name__}")

    if not isinstance(settings.AI_MAX_TOKENS, int):
        failures.append(f"AI_MAX_TOKENS not int: {type(settings.AI_MAX_TOKENS).__name__}")

    if not isinstance(settings.AI_TEMPERATURE, float):
        failures.append(f"AI_TEMPERATURE not float: {type(settings.AI_TEMPERATURE).__name__}")

    # --- Rate-limit strings follow slowapi format ---
    for field in ("RATE_LIMIT_BUILD", "RATE_LIMIT_DEFAULT"):
        val = getattr(settings, field, "")
        if "/" not in val:
            failures.append(f"{field}: expected 'N/unit' format, got {val!r}")

    # --- CORS_ORIGINS parses into a non-empty list ---
    origins = [o.strip() for o in settings.CORS_ORIGINS.split(",") if o.strip()]
    if not origins:
        failures.append("CORS_ORIGINS parses to empty list")
    for o in origins:
        if not (o.startswith("http://") or o.startswith("https://")):
            failures.append(f"CORS origin missing scheme: {o!r}")

    # --- Paths exist/can be created ---
    if not settings.EXPORTS_DIR.exists():
        failures.append(f"EXPORTS_DIR missing: {settings.EXPORTS_DIR}")
    if not settings.CAD_DIR.exists():
        failures.append(f"CAD_DIR missing: {settings.CAD_DIR}")

    # --- Environment override: build a fresh Settings with injected env ---
    os.environ["RATE_LIMIT_BUILD"] = "99/hour"
    os.environ["AI_MAX_TOKENS"] = "1234"
    try:
        fresh = Settings()
        if fresh.RATE_LIMIT_BUILD != "99/hour":
            failures.append(f"env override RATE_LIMIT_BUILD: {fresh.RATE_LIMIT_BUILD}")
        if fresh.AI_MAX_TOKENS != 1234:
            failures.append(f"env override AI_MAX_TOKENS: {fresh.AI_MAX_TOKENS}")
    finally:
        os.environ.pop("RATE_LIMIT_BUILD", None)
        os.environ.pop("AI_MAX_TOKENS", None)

    # --- Defaults are sensible ---
    if settings.PORT != 3001:
        print(f"  (info) PORT overridden to {settings.PORT}")
    if settings.AI_MODEL_NAME == "":
        failures.append("AI_MODEL_NAME is empty")

    # --- REQUIRE_AUTH is a bool ---
    if not isinstance(settings.REQUIRE_AUTH, bool):
        failures.append(f"REQUIRE_AUTH not bool: {type(settings.REQUIRE_AUTH).__name__}")

    if failures:
        print("❌ test_config_loader failures:")
        for f in failures:
            print(f"   - {f}")
        sys.exit(1)

    print("✅ test_config_loader: Settings class loads, types coerce, overrides work")
    sys.exit(0)


if __name__ == "__main__":
    main()
