"""Verify the model configuration is locked to a single Anthropic Claude model.

This app intentionally uses exactly one model (Claude Opus 4.7). This script
verifies the fallback chain in claude_service has length 1 and references
settings.AI_MODEL_NAME (not a hardcoded ID).
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
src = (ROOT / "Backend" / "services" / "claude_service.py").read_text(encoding="utf-8")

m = re.search(r"self\.model_fallback_chain\s*=\s*\[(.*?)\]", src, re.DOTALL)
if not m:
    print("BAD  could not find model_fallback_chain initializer")
    sys.exit(1)

body = m.group(1).strip()
entries = [e.strip() for e in body.split(",") if e.strip()]

if len(entries) != 1:
    print(f"BAD  expected exactly 1 model in fallback chain, got {len(entries)}: {entries}")
    sys.exit(1)

if "settings.AI_MODEL_NAME" not in entries[0]:
    print(f"BAD  fallback chain should reference settings.AI_MODEL_NAME, got {entries[0]}")
    sys.exit(1)

print("OK   model_fallback_chain is single-entry and references settings.AI_MODEL_NAME")
sys.exit(0)
