"""
Usage metering for inventa.ai.

In-memory counter for builds-per-user-per-day. When a database is configured,
callers can persist by reading `snapshot()` and flushing elsewhere. The default
implementation is intentionally lightweight and dependency-free so the core
build path never blocks on metering.

Used by:
  - free-tier guardrails in /api/build/stream
  - analytics scaffolding (later)
"""
from __future__ import annotations

from collections import defaultdict
from datetime import date
from threading import Lock
from typing import Dict


class UsageMeter:
    """Thread-safe per-user daily build counter."""

    FREE_TIER_DAILY_BUILDS = 20

    def __init__(self) -> None:
        self._lock = Lock()
        # {(user_id, YYYY-MM-DD): count}
        self._counts: Dict[tuple[str, str], int] = defaultdict(int)

    @staticmethod
    def _today() -> str:
        return date.today().isoformat()

    def increment(self, user_id: str | None, kind: str = "build") -> int:
        uid = (user_id or "anonymous") + ":" + kind
        key = (uid, self._today())
        with self._lock:
            self._counts[key] += 1
            return self._counts[key]

    def get(self, user_id: str | None, kind: str = "build") -> int:
        uid = (user_id or "anonymous") + ":" + kind
        key = (uid, self._today())
        with self._lock:
            return self._counts.get(key, 0)

    def check_free_tier(self, user_id: str | None) -> tuple[bool, int, int]:
        """Returns (allowed, used_today, limit)."""
        used = self.get(user_id)
        limit = self.FREE_TIER_DAILY_BUILDS
        return (used < limit, used, limit)

    def snapshot(self) -> Dict[str, int]:
        """Returns a flat copy suitable for logging / persistence."""
        with self._lock:
            return {f"{k[0]}|{k[1]}": v for k, v in self._counts.items()}

    def reset(self) -> None:
        """Clears all counters. Used in tests."""
        with self._lock:
            self._counts.clear()


usage_meter = UsageMeter()
