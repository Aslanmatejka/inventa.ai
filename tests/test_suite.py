"""
Pytest wrapper for the 12 standalone backend test scripts at the repo root.

Each script is executed as a subprocess so its `sys.exit(code)` doesn't abort
the pytest session. Scripts exit 0 for pass, non-zero for fail.
"""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]

TEST_SCRIPTS = [
    "test_completeness.py",
    "test_cq_warehouse.py",
    "test_drone_analyzer.py",
    "test_drone_types.py",
    "test_ground_fix.py",
    "test_phase1.py",
    "test_phase32.py",
    "test_phone_case_analyzer.py",
    "test_shape_quality.py",
    "test_code_safety.py",
    "test_preprocessing.py",
    "test_product_library.py",
    "test_rebuild.py",
    "test_claude_extract_json.py",
    "test_fix_code_error_classification.py",
    "test_endpoints_smoke.py",
    "test_visual_knowledge.py",
    "test_config_loader.py",
    "test_path_traversal.py",
    "test_prompt_injection.py",
    "test_usage_meter.py",
    "test_metrics.py",
    "test_token_tracker.py",
]


@pytest.mark.parametrize("script", TEST_SCRIPTS)
def test_standalone_script(script: str) -> None:
    """Runs one legacy test_*.py script and asserts it exits 0."""
    script_path = ROOT / script
    assert script_path.exists(), f"missing test script: {script}"

    env = os.environ.copy()
    env.setdefault("PYTHONIOENCODING", "utf-8")
    env.setdefault("ANTHROPIC_API_KEY", "sk-ant-ci-placeholder")

    proc = subprocess.run(
        [sys.executable, str(script_path)],
        cwd=str(ROOT),
        env=env,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=600,
    )
    if proc.returncode != 0:
        print(proc.stdout)
        print(proc.stderr, file=sys.stderr)
    assert proc.returncode == 0, f"{script} exited {proc.returncode}"
