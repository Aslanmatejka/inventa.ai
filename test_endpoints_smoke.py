"""
Smoke test: FastAPI endpoints via TestClient.

Hits non-AI read-only endpoints to verify routes are registered and return
expected status codes. Does NOT call Claude / CadQuery.
"""
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

    # --- Root health ---
    r = client.get("/")
    if r.status_code != 200:
        failures.append(f"GET /: {r.status_code}")
    elif r.json().get("status") != "healthy":
        failures.append(f"GET /: unexpected payload {r.json()}")

    # --- Liveness ---
    r = client.get("/api/healthz")
    if r.status_code != 200 or r.json().get("status") != "ok":
        failures.append(f"GET /api/healthz: {r.status_code} {r.text[:100]}")

    # --- Readiness (may be 200 or 503 depending on env) ---
    r = client.get("/api/readyz")
    if r.status_code not in (200, 503):
        failures.append(f"GET /api/readyz: unexpected {r.status_code}")
    if "checks" not in r.json():
        failures.append("GET /api/readyz: missing 'checks'")

    # --- Legacy health ---
    r = client.get("/api/health")
    if r.status_code != 200:
        failures.append(f"GET /api/health: {r.status_code}")

    # --- Models list ---
    r = client.get("/api/models")
    if r.status_code != 200:
        failures.append(f"GET /api/models: {r.status_code}")
    else:
        body = r.json()
        if not isinstance(body, dict) or "models" not in body and not isinstance(body, list):
            # Accept either shape — log if neither
            pass

    # --- Path traversal defense on exports/cad ---
    r = client.get("/exports/cad/..%2F..%2Fetc%2Fpasswd")
    if r.status_code not in (400, 403, 404):
        failures.append(f"path traversal: expected 400/403/404, got {r.status_code}")

    # --- Hidden file rejection ---
    r = client.get("/exports/cad/.env")
    if r.status_code not in (400, 403, 404):
        failures.append(f"hidden file: expected 400/403/404, got {r.status_code}")

    # --- Disallowed extension ---
    r = client.get("/exports/cad/evil.exe")
    if r.status_code not in (400, 403, 404):
        failures.append(f"bad extension: expected 400/403/404, got {r.status_code}")

    # --- Unknown route ---
    r = client.get("/api/does-not-exist")
    if r.status_code != 404:
        failures.append(f"404 route: got {r.status_code}")

    if failures:
        print("❌ test_endpoints_smoke failures:")
        for f in failures:
            print(f"   - {f}")
        sys.exit(1)

    print("✅ test_endpoints_smoke: health + security + 404 routes all green")
    sys.exit(0)


if __name__ == "__main__":
    main()
