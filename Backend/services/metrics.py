"""
Lightweight in-process metrics collector.

Exposes Prometheus-style counters + histograms without requiring the
`prometheus_client` dependency. The `/metrics` endpoint in main.py
formats the snapshot in the standard Prometheus exposition format.
"""
from __future__ import annotations

from collections import defaultdict
from threading import Lock
from time import time
from typing import Dict, List


class Metrics:
    def __init__(self) -> None:
        self._lock = Lock()
        self._counters: Dict[str, Dict[tuple, float]] = defaultdict(lambda: defaultdict(float))
        self._histograms: Dict[str, Dict[tuple, List[float]]] = defaultdict(
            lambda: defaultdict(list)
        )
        self._started_at = time()

    def incr(self, name: str, labels: Dict[str, str] | None = None, value: float = 1.0) -> None:
        key = tuple(sorted((labels or {}).items()))
        with self._lock:
            self._counters[name][key] += value

    def observe(self, name: str, value: float, labels: Dict[str, str] | None = None) -> None:
        key = tuple(sorted((labels or {}).items()))
        with self._lock:
            bucket = self._histograms[name][key]
            bucket.append(value)
            # Keep bounded so memory never blows up
            if len(bucket) > 1000:
                del bucket[: len(bucket) - 1000]

    @staticmethod
    def _fmt_labels(key: tuple) -> str:
        if not key:
            return ""
        parts = [f'{k}="{str(v).replace(chr(34), "")}"' for k, v in key]
        return "{" + ",".join(parts) + "}"

    def snapshot_prometheus(self) -> str:
        lines: list[str] = []
        with self._lock:
            uptime = time() - self._started_at
            lines.append("# TYPE inventa_uptime_seconds counter")
            lines.append(f"inventa_uptime_seconds {uptime:.1f}")

            for name, by_labels in self._counters.items():
                lines.append(f"# TYPE {name} counter")
                for key, val in by_labels.items():
                    lines.append(f"{name}{self._fmt_labels(key)} {val}")

            for name, by_labels in self._histograms.items():
                lines.append(f"# TYPE {name} summary")
                for key, vals in by_labels.items():
                    if not vals:
                        continue
                    count = len(vals)
                    total = sum(vals)
                    vals_sorted = sorted(vals)
                    p50 = vals_sorted[count // 2]
                    p95 = vals_sorted[int(count * 0.95)] if count > 1 else vals_sorted[0]
                    p99 = vals_sorted[int(count * 0.99)] if count > 1 else vals_sorted[0]
                    label_str = self._fmt_labels(key)
                    base = f"{name}{label_str}"
                    lines.append(f'{base}{{quantile="0.5"}} {p50:.3f}')
                    lines.append(f'{base}{{quantile="0.95"}} {p95:.3f}')
                    lines.append(f'{base}{{quantile="0.99"}} {p99:.3f}')
                    lines.append(f"{name}_sum{label_str} {total:.3f}")
                    lines.append(f"{name}_count{label_str} {count}")

        return "\n".join(lines) + "\n"


metrics = Metrics()
