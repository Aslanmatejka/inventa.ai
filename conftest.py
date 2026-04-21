"""
Root conftest.py — makes the existing standalone test_*.py scripts at the repo
root discoverable by pytest without rewriting them.

The existing scripts each `sys.path.insert(0, 'Backend')` and call sys.exit(0/1).
Pytest imports them as modules, which runs their top-level code inside a
`test_<name>` wrapper (see tests/test_suite.py).
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
BACKEND = ROOT / "Backend"

# Ensure Backend is importable regardless of CWD.
for p in (str(ROOT), str(BACKEND)):
    if p not in sys.path:
        sys.path.insert(0, p)

# Make the Anthropic client happy in CI when no real key is present.
os.environ.setdefault("PYTHONIOENCODING", "utf-8")
os.environ.setdefault("ANTHROPIC_API_KEY", os.environ.get("ANTHROPIC_API_KEY", "sk-ant-ci-placeholder"))
