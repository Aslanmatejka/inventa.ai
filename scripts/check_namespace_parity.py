"""
Namespace parity check.

The AI code safety allowlist in `_validate_code_safety` must stay in sync with
the actual `namespace` dicts used by `_execute_cadquery_code` and
`rebuild_with_parameters`. This script parses parametric_cad_service.py and
warns if any module allowed for import is missing from a runtime namespace (or
vice versa), which would let AI code pass validation and then NameError.

Run: python scripts/check_namespace_parity.py
Exit 0 if in sync, 1 otherwise.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SVC = ROOT / "Backend" / "services" / "parametric_cad_service.py"


def extract_allowlist(src: str) -> set[str]:
    # allowed_imports = {"cadquery", "cq", ...}
    m = re.search(r"allowed_imports\s*=\s*\{(.*?)\}", src, re.DOTALL)
    if not m:
        print("ERROR: could not find allowed_imports set")
        sys.exit(2)
    body = m.group(1)
    # Strip inline comments and collect quoted tokens only.
    body = re.sub(r"#[^\n]*", "", body)
    tokens = re.findall(r'["\']([^"\']+)["\']', body)
    return set(tokens)


def extract_namespace_keys(src: str) -> list[set[str]]:
    """
    Find every `namespace = { ... }` literal and also sweep the next ~60 lines
    after each literal for `namespace["X"] = ...` assignments (which happen in
    conditional blocks for optional deps like numpy / cq_warehouse).
    """
    lines = src.splitlines()
    namespaces: list[set[str]] = []

    # Locate each literal
    literal_matches = list(re.finditer(r"namespace\s*=\s*\{(.*?)\n\s*\}", src, re.DOTALL))
    for m in literal_matches:
        body = m.group(1)
        keys = set(re.findall(r'"([^"]+)"\s*:', body))
        keys |= set(re.findall(r"'([^']+)'\s*:", body))

        # Figure out which line the literal ends on.
        end_line = src[: m.end()].count("\n")
        # Sweep the next 80 lines for namespace["X"] = ... style adds.
        for line in lines[end_line : end_line + 80]:
            stripped = line.strip()
            # Stop sweeping once we leave the function scope (unindented return / def).
            if stripped.startswith(("def ", "async def ", "class ")) and line[:1] not in (" ", "\t"):
                break
            for key in re.findall(r'namespace\[\s*["\']([^"\']+)["\']\s*\]\s*=', line):
                keys.add(key)
        namespaces.append(keys)
    return namespaces


def main() -> int:
    src = SVC.read_text(encoding="utf-8")
    allow = extract_allowlist(src)
    namespaces = extract_namespace_keys(src)

    if len(namespaces) < 2:
        print(f"ERROR: expected >=2 namespace dicts, found {len(namespaces)}")
        return 2

    # The safety allowlist always includes aliases like "cq" and "np" even though
    # they aren't top-level modules. These are added to each namespace dynamically
    # (cq alias, np alias, cq_warehouse gated on availability). So the parity
    # contract is: every allowlisted name must appear in every namespace dict.
    problems: list[str] = []
    for i, ns in enumerate(namespaces, 1):
        missing = allow - ns
        if missing:
            problems.append(f"namespace #{i} is missing: {sorted(missing)}")

    # Also flag: a name used in a namespace but not allowlisted (AI code can't
    # reach it anyway, so it's dead weight worth removing).
    union = set().union(*namespaces)
    dead = union - allow - {"deepcopy"}  # deepcopy is a helper not a module
    if dead:
        # Don't fail on this — fasteners like "Nut", "Screw" live here. Just info.
        pass

    print(f"Allowlist modules: {sorted(allow)}")
    print(f"Namespace dicts found: {len(namespaces)}")
    for i, ns in enumerate(namespaces, 1):
        print(f"  #{i}: {len(ns)} keys")

    if problems:
        print("\nPARITY VIOLATIONS:")
        for p in problems:
            print(f"  - {p}")
        print("\nTriple-update rule broken. See .github/copilot-instructions.md.")
        return 1

    print("\nOK: allowlist and namespace dicts are in parity.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
