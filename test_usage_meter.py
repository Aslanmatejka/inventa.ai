"""
Test: usage_meter — per-user daily counter + free-tier guard.
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

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "Backend"))
os.environ.setdefault("ANTHROPIC_API_KEY", "sk-ant-test-placeholder")

from services.usage_meter import UsageMeter, usage_meter  # noqa: E402


def main():
    failures = []
    m = UsageMeter()

    # Fresh counter starts at 0
    if m.get("alice") != 0:
        failures.append("fresh counter should be 0")

    # Increment returns the running total
    if m.increment("alice") != 1:
        failures.append("first increment should return 1")
    if m.increment("alice") != 2:
        failures.append("second increment should return 2")
    if m.get("alice") != 2:
        failures.append("get() mismatch after 2 increments")

    # Different users are independent
    if m.increment("bob") != 1:
        failures.append("bob's first increment should return 1")
    if m.get("alice") != 2:
        failures.append("bob's increment leaked into alice")

    # Anonymous bucket
    if m.increment(None) != 1:
        failures.append("anonymous first increment should return 1")

    # Free-tier guard: allow under limit
    limit = m.FREE_TIER_DAILY_BUILDS
    m.reset()
    for i in range(limit):
        m.increment("charlie")
    allowed, used, cap = m.check_free_tier("charlie")
    if allowed:
        failures.append(f"at exactly the limit ({used}/{cap}) should be disallowed")
    if used != limit or cap != limit:
        failures.append(f"check_free_tier counts wrong: used={used}, cap={cap}")

    # Under the limit is allowed
    allowed, used, cap = m.check_free_tier("danny")
    if not allowed:
        failures.append("new user should be allowed")

    # Snapshot returns a dict
    snap = m.snapshot()
    if not isinstance(snap, dict):
        failures.append("snapshot not a dict")
    if not any("charlie" in k for k in snap):
        failures.append("snapshot missing charlie")

    # Reset clears everything
    m.reset()
    if m.snapshot():
        failures.append("reset did not clear snapshot")

    # Module singleton is instantiable
    if not isinstance(usage_meter, UsageMeter):
        failures.append("module singleton wrong type")

    if failures:
        print("❌ test_usage_meter failures:")
        for f in failures:
            print(f"   - {f}")
        sys.exit(1)

    print("✅ test_usage_meter: counter, free-tier guard, isolation, reset verified")
    sys.exit(0)


if __name__ == "__main__":
    main()
