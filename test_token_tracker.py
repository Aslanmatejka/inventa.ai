"""Test: token_tracker — ContextVar scope, aggregation, flush, cost estimation."""
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

from services import token_tracker as tt  # noqa: E402


class _FakeAnthropicUsage:
    def __init__(self, inp, out, cache_read=0, cache_write=0):
        self.input_tokens = inp
        self.output_tokens = out
        self.cache_read_input_tokens = cache_read
        self.cache_creation_input_tokens = cache_write


class _FakeOpenAIUsage:
    def __init__(self, prompt, completion):
        self.prompt_tokens = prompt
        self.completion_tokens = completion


def main():
    failures = []

    # ── No active build → record is a no-op (does not raise) ──
    tt.record_usage("claude-opus-4-7", _FakeAnthropicUsage(100, 50))
    if tt.peek("none"):
        failures.append("record outside an active build must be a no-op")

    # ── Scope 1: Anthropic-style usage ──
    token = tt.start("build_a")
    try:
        tt.record_usage("claude-opus-4-7", _FakeAnthropicUsage(1000, 200, cache_read=50))
        tt.record_usage("claude-opus-4-7", _FakeAnthropicUsage(500, 100))
        snap = tt.peek("build_a")
        if snap["input_tokens"] != 1500:
            failures.append(f"input aggregation wrong: {snap['input_tokens']}")
        if snap["output_tokens"] != 300:
            failures.append(f"output aggregation wrong: {snap['output_tokens']}")
        if snap["cache_read_input_tokens"] != 50:
            failures.append("cache_read aggregation wrong")
        if snap["calls"] != 2:
            failures.append(f"calls wrong: {snap['calls']}")
        if snap["cost_usd"] <= 0:
            failures.append("cost_usd should be > 0 for Opus")
    finally:
        tt.restore(token)

    # ── Flush returns totals and clears ──
    flushed = tt.flush("build_a")
    if flushed["input_tokens"] != 1500:
        failures.append("flush lost totals")
    if tt.peek("build_a"):
        failures.append("flush did not clear ledger row")

    # ── Scope 2: OpenAI-style usage object maps correctly ──
    # The app no longer uses OpenAI, but record_usage still has a fallback
    # for any usage object exposing prompt_tokens/completion_tokens, so we
    # keep this regression test for the field-name mapping.
    token = tt.start("build_b")
    try:
        tt.record_usage("future-openai-style", _FakeOpenAIUsage(2000, 400))
        snap = tt.peek("build_b")
        if snap["input_tokens"] != 2000 or snap["output_tokens"] != 400:
            failures.append(f"openai-style mapping wrong: {snap}")
    finally:
        tt.restore(token)
    tt.flush("build_b")

    # ── Unknown model → cost is None, aggregation still works ──
    token = tt.start("build_c")
    try:
        tt.record_usage("future-model-x", _FakeAnthropicUsage(10, 20))
        snap = tt.peek("build_c")
        if snap["input_tokens"] != 10:
            failures.append("unknown-model aggregation failed")
        if snap["cost_usd"] != 0.0:
            failures.append("unknown-model cost should be 0")
    finally:
        tt.restore(token)
    tt.flush("build_c")

    # ── estimate_cost is deterministic and model-aware ──
    opus = tt.estimate_cost("claude-opus-4-7", 1000, 1000)
    if opus is None:
        failures.append("estimate_cost returned None for the only supported model")
    elif opus <= 0:
        failures.append(f"Opus cost should be > 0, got {opus}")
    if tt.estimate_cost("no-such-model", 100, 100) is not None:
        failures.append("estimate_cost should return None for unknown model")

    if failures:
        print("❌ test_token_tracker failures:")
        for f in failures:
            print(f"   - {f}")
        sys.exit(1)

    print("✅ test_token_tracker: scope, aggregation, flush, cost estimation verified")
    sys.exit(0)


if __name__ == "__main__":
    main()
