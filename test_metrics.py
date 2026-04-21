"""Test: metrics collector — counters, histograms, Prometheus formatting."""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "Backend"))
os.environ.setdefault("ANTHROPIC_API_KEY", "sk-ant-test-placeholder")

from services.metrics import Metrics  # noqa: E402


def main():
    failures = []
    m = Metrics()

    # Counters
    m.incr("reqs_total", {"path": "/api/build", "status": "200"})
    m.incr("reqs_total", {"path": "/api/build", "status": "200"})
    m.incr("reqs_total", {"path": "/api/build", "status": "500"})
    out = m.snapshot_prometheus()

    if 'reqs_total{path="/api/build",status="200"} 2' not in out:
        failures.append("counter 200 missing or wrong value")
    if 'reqs_total{path="/api/build",status="500"} 1' not in out:
        failures.append("counter 500 missing")
    if "# TYPE reqs_total counter" not in out:
        failures.append("counter type header missing")

    # Histograms
    for v in [0.1, 0.2, 0.3, 0.4, 0.5]:
        m.observe("latency_seconds", v)
    out = m.snapshot_prometheus()
    if "# TYPE latency_seconds summary" not in out:
        failures.append("summary type header missing")
    if "latency_seconds_count" not in out:
        failures.append("_count line missing")
    if "latency_seconds_sum" not in out:
        failures.append("_sum line missing")
    if 'quantile="0.5"' not in out:
        failures.append("p50 quantile missing")

    # Uptime always present
    if "inventa_uptime_seconds" not in out:
        failures.append("uptime line missing")

    # Histogram memory cap — push 2000 values, internal bucket must cap at 1000
    for i in range(2000):
        m.observe("burst", float(i))
    # Access internals for verification
    key = tuple()
    stored = m._histograms["burst"][key]
    if len(stored) != 1000:
        failures.append(f"histogram cap broken: {len(stored)}")

    if failures:
        print("❌ test_metrics failures:")
        for f in failures:
            print(f"   - {f}")
        sys.exit(1)

    print("✅ test_metrics: counters, histograms, Prometheus formatting verified")
    sys.exit(0)


if __name__ == "__main__":
    main()
