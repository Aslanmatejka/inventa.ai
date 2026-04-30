"""
Path-traversal defense tests for /exports/cad/{filename}.

Expands the basic smoke test with encoded, double-encoded, and OS-specific
variants to ensure the handler rejects every attack pattern.
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
os.environ.setdefault("PYTHONIOENCODING", "utf-8")

try:
    from fastapi.testclient import TestClient
except Exception as e:
    print(f"⚠️ TestClient unavailable: {e}")
    sys.exit(0)


def main():
    try:
        from main import app  # noqa: E402
    except Exception as e:
        print(f"❌ Could not import Backend.main: {e}")
        sys.exit(1)

    client = TestClient(app)
    failures = []

    # Attack payloads and the status codes we accept (4xx only).
    attacks = [
        "../etc/passwd",
        "..%2Fetc%2Fpasswd",
        "..%252Fetc%252Fpasswd",          # double-encoded
        "%2e%2e/etc/passwd",
        "..\\windows\\system32\\config",
        "..%5Cwindows%5Csystem32",
        ".env",
        ".ssh/id_rsa",
        "",                                # empty
        "CON",                             # Windows reserved
        "file%00.stl",                      # NUL byte
        "legitname.exe",                    # disallowed extension
        "script.sh",
        "a" * 500 + ".stl",                 # very long name
    ]

    for attack in attacks:
        r = client.get(f"/exports/cad/{attack}")
        if r.status_code not in (400, 403, 404):
            failures.append(f"{attack!r}: expected 4xx, got {r.status_code}")

    # Legitimate-looking path with disallowed extension
    r = client.get("/exports/cad/build_123.pdf")
    if r.status_code not in (400, 403, 404):
        failures.append(f"pdf extension: expected 4xx, got {r.status_code}")

    # Non-existent but syntactically valid file
    r = client.get("/exports/cad/does_not_exist_12345.stl")
    if r.status_code != 404:
        failures.append(f"non-existent valid: expected 404, got {r.status_code}")

    if failures:
        print("❌ test_path_traversal failures:")
        for f in failures:
            print(f"   - {f}")
        sys.exit(1)

    print(f"✅ test_path_traversal: {len(attacks) + 2} attack variants rejected")
    sys.exit(0)


if __name__ == "__main__":
    main()
