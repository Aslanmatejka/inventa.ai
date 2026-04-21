"""
End-to-end token tracking.

Scopes token usage to the currently-active build via a ContextVar so the
Anthropic and OpenAI streaming wrappers can record usage without having to
thread a build_id through every call. At the end of a build, the caller
calls `flush()` to get aggregated totals and cost, which are then:

  1. emitted to the /metrics Prometheus endpoint, and
  2. included in the SSE `complete` event payload, and
  3. persisted to `build_analytics` via database_service.save_analytics().

Per-token USD pricing is a best-effort table of public API list prices and
can be updated as new models ship. If a model is missing from the table the
cost is reported as None instead of raising.
"""
from __future__ import annotations

import contextvars
import threading
from typing import Any, Dict, Optional

# ── Public API list prices (USD per 1K tokens) ─────────────────────────
# Keep prices approximate; used for user-facing cost estimates only. Missing
# models return None from estimate_cost() rather than failing.
_PRICING_USD_PER_1K: Dict[str, Dict[str, float]] = {
    # Anthropic Claude — Opus tier
    "claude-opus-4-7":          {"in": 0.015,  "out": 0.075},
    "claude-opus-4-6":          {"in": 0.015,  "out": 0.075},
    "claude-opus-4-20250514":   {"in": 0.015,  "out": 0.075},
    # Anthropic Claude — Sonnet tier
    "claude-sonnet-4-6":        {"in": 0.003,  "out": 0.015},
    "claude-sonnet-4-20250514": {"in": 0.003,  "out": 0.015},
    # OpenAI GPT-4.1
    "gpt-4.1-2025-04-14":       {"in": 0.002,  "out": 0.008},
    "gpt-4.1-mini-2025-04-14":  {"in": 0.0004, "out": 0.0016},
    "gpt-4.1-nano-2025-04-14":  {"in": 0.0001, "out": 0.0004},
}


def estimate_cost(model: str, input_tokens: int, output_tokens: int) -> Optional[float]:
    """Return USD cost estimate, or None if the model isn't in the pricing table."""
    p = _PRICING_USD_PER_1K.get(model)
    if not p:
        return None
    return round((input_tokens / 1000.0) * p["in"] + (output_tokens / 1000.0) * p["out"], 6)


# ── Active-build context + aggregate ledger ────────────────────────────
_active_build: contextvars.ContextVar[Optional[str]] = contextvars.ContextVar(
    "active_build", default=None
)


class _Ledger:
    """Aggregate token usage keyed by build id. Thread-safe."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._data: Dict[str, Dict[str, Any]] = {}

    def record(self, build_id: str, model: str, input_tokens: int,
               output_tokens: int, cache_read: int = 0, cache_write: int = 0) -> None:
        if not build_id:
            return
        with self._lock:
            row = self._data.setdefault(build_id, {
                "input_tokens": 0,
                "output_tokens": 0,
                "cache_read_input_tokens": 0,
                "cache_creation_input_tokens": 0,
                "calls": 0,
                "model": model,
                "cost_usd": 0.0,
            })
            row["input_tokens"] += int(input_tokens or 0)
            row["output_tokens"] += int(output_tokens or 0)
            row["cache_read_input_tokens"] += int(cache_read or 0)
            row["cache_creation_input_tokens"] += int(cache_write or 0)
            row["calls"] += 1
            row["model"] = model  # last-seen model, for cost estimation
            est = estimate_cost(model, input_tokens or 0, output_tokens or 0)
            if est is not None:
                row["cost_usd"] = round(row["cost_usd"] + est, 6)

    def flush(self, build_id: str) -> Dict[str, Any]:
        if not build_id:
            return {"input_tokens": 0, "output_tokens": 0, "calls": 0, "cost_usd": 0.0}
        with self._lock:
            return self._data.pop(build_id, {
                "input_tokens": 0,
                "output_tokens": 0,
                "cache_read_input_tokens": 0,
                "cache_creation_input_tokens": 0,
                "calls": 0,
                "cost_usd": 0.0,
            })

    def peek(self, build_id: str) -> Dict[str, Any]:
        with self._lock:
            return dict(self._data.get(build_id, {}))


_ledger = _Ledger()


# ── Context helpers ────────────────────────────────────────────────────
def start(build_id: str) -> contextvars.Token:
    """Mark a build id as the active scope. Returns a token for restore()."""
    return _active_build.set(build_id)


def restore(token: contextvars.Token) -> None:
    _active_build.reset(token)


def current_build_id() -> Optional[str]:
    return _active_build.get()


def record_usage(model: str, usage_obj: Any) -> None:
    """Record token usage from an SDK usage object (Anthropic or OpenAI).

    Accepts either an Anthropic `Usage` (input_tokens / output_tokens /
    cache_read_input_tokens / cache_creation_input_tokens) or an OpenAI
    CompletionUsage (prompt_tokens / completion_tokens). Unknown shapes are
    silently ignored.
    """
    build_id = current_build_id()
    if not build_id or usage_obj is None:
        return

    def _get(name: str) -> int:
        v = getattr(usage_obj, name, None)
        if v is None and isinstance(usage_obj, dict):
            v = usage_obj.get(name)
        try:
            return int(v or 0)
        except (TypeError, ValueError):
            return 0

    # Anthropic-style first, then OpenAI-style fallback
    input_tokens = _get("input_tokens") or _get("prompt_tokens")
    output_tokens = _get("output_tokens") or _get("completion_tokens")
    cache_read = _get("cache_read_input_tokens")
    cache_write = _get("cache_creation_input_tokens")

    _ledger.record(build_id, model, input_tokens, output_tokens, cache_read, cache_write)

    # Prometheus counters (best-effort)
    try:
        from services.metrics import metrics as _metrics
        labels = {"model": model}
        _metrics.incr("inventa_tokens_input_total", labels, input_tokens)
        _metrics.incr("inventa_tokens_output_total", labels, output_tokens)
        if cache_read:
            _metrics.incr("inventa_tokens_cache_read_total", labels, cache_read)
    except Exception:
        pass


def flush(build_id: str) -> Dict[str, Any]:
    """Return aggregated totals for a build and remove the ledger row."""
    return _ledger.flush(build_id)


def peek(build_id: str) -> Dict[str, Any]:
    return _ledger.peek(build_id)
