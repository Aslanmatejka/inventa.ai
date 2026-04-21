"""
Test the 7-step preprocessing pipeline in ParametricCADService.
Each transform must stay idempotent and surgical — this locks the contract in place.
"""
import sys
try:
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')
except Exception:
    pass
sys.path.insert(0, 'Backend')

from services.parametric_cad_service import ParametricCADService

svc = ParametricCADService()
passed = 0
failed = 0
failures = []


def check(cond: bool, label: str, detail: str = ""):
    global passed, failed
    if cond:
        print(f"  PASS: {label}")
        passed += 1
    else:
        print(f"  FAIL: {label}  {detail}")
        failed += 1
        failures.append(label)


# ── _strip_centered_from_non_box ──────────────────────────────────────────
print("=" * 60)
print("TEST 1: _strip_centered_from_non_box")
print("=" * 60)
src = (
    "import cadquery as cq\n"
    "result = cq.Workplane('XY').rect(10, 20, centered=True)"
    ".extrude(5, centered=(True,True,False))\n"
)
out = svc._strip_centered_from_non_box(src)
check("centered=True" not in out.split(".rect(")[1].split(")")[0],
      "removes centered= from .rect()")
check("centered=" not in out.split(".extrude(")[1].split(")")[0],
      "removes centered= from .extrude()")
# .box() must keep its centered param
src2 = "import cadquery as cq\nresult = cq.Workplane('XY').box(10,10,10, centered=(True,True,False))\n"
out2 = svc._strip_centered_from_non_box(src2)
check("centered=" in out2, "preserves centered= on .box()")

# ── _fix_zero_dimensions ──────────────────────────────────────────────────
print()
print("=" * 60)
print("TEST 2: _fix_zero_dimensions")
print("=" * 60)
src = "import cadquery as cq\nresult = cq.Workplane('XY').circle(5).extrude(0)\n"
out = svc._fix_zero_dimensions(src)
check(".extrude(0.1)" in out, "replaces .extrude(0) with .extrude(0.1)")
src = "import cadquery as cq\nresult = cq.Workplane('XY').circle(5).extrude(0.0)\n"
out = svc._fix_zero_dimensions(src)
check(".extrude(0.1)" in out, "replaces .extrude(0.0) with .extrude(0.1)")
# Non-zero extrude must stay intact
src = "import cadquery as cq\nresult = cq.Workplane('XY').circle(5).extrude(7.5)\n"
out = svc._fix_zero_dimensions(src)
check(".extrude(7.5)" in out, "preserves non-zero extrude")

# ── _ensure_result_assignment ─────────────────────────────────────────────
print()
print("=" * 60)
print("TEST 3: _ensure_result_assignment")
print("=" * 60)
src = "import cadquery as cq\nbody = cq.Workplane('XY').box(10,10,10)\n"
out = svc._ensure_result_assignment(src)
check("result = body" in out, "auto-assigns result = body when missing")
# Already-assigned code must not get double assignment
src2 = "import cadquery as cq\nresult = cq.Workplane('XY').box(10,10,10)\n"
out2 = svc._ensure_result_assignment(src2)
check(out2.count("result =") == 1, "no double assignment when result already exists")

# ── _clamp_fillet_radii ───────────────────────────────────────────────────
print()
print("=" * 60)
print("TEST 4: _clamp_fillet_radii")
print("=" * 60)
src = (
    "import cadquery as cq\n"
    "body = cq.Workplane('XY').box(20, 10, 5)\n"
    "body = body.edges('|Z').fillet(3)\n"
    "result = body\n"
)
out = svc._clamp_fillet_radii(src)
check("_auto_fillet_max" in out, "emits _auto_fillet_max guard")
# The guard should be a number strictly less than the smallest dimension (5mm)
import re
m = re.search(r'_auto_fillet_max\s*=\s*([\d.]+)', out)
if m:
    val = float(m.group(1))
    check(0 < val < 5, f"clamp value {val} is within (0, 5)")
else:
    check(False, "clamp value present", "no numeric match")

# ── _wrap_fillets_in_try_except ───────────────────────────────────────────
print()
print("=" * 60)
print("TEST 5: _wrap_fillets_in_try_except")
print("=" * 60)
src = (
    "import cadquery as cq\n"
    "body = cq.Workplane('XY').box(20, 10, 5)\n"
    "body = body.edges('|Z').fillet(_auto_fillet_max)\n"
    "result = body\n"
)
out = svc._wrap_fillets_in_try_except(src)
check("try:" in out and "except" in out, "wraps fillet in try/except")
check("body = body.edges" in out, "preserves original assignment")


# ── Full-pipeline idempotency ────────────────────────────────────────────
print()
print("=" * 60)
print("TEST 6: preprocessing idempotency")
print("=" * 60)
src = (
    "import cadquery as cq\n"
    "body = cq.Workplane('XY').box(20, 20, 10, centered=(True,True,False))\n"
    "body = body.edges('|Z').fillet(3)\n"
    "result = body\n"
)
once = svc._strip_centered_from_non_box(src)
once = svc._fix_zero_dimensions(once)
once = svc._ensure_result_assignment(once)
once = svc._clamp_fillet_radii(once)
once = svc._wrap_fillets_in_try_except(once)

twice = svc._strip_centered_from_non_box(once)
twice = svc._fix_zero_dimensions(twice)
twice = svc._ensure_result_assignment(twice)
twice = svc._clamp_fillet_radii(twice)
twice = svc._wrap_fillets_in_try_except(twice)
check(once == twice, "running pipeline twice is idempotent",
      "" if once == twice else f"diff size: {abs(len(once)-len(twice))} chars")


print()
print("=" * 60)
print(f"RESULTS: {passed} passed, {failed} failed")
if failures:
    print("FAILED:")
    for f in failures:
        print(f"  - {f}")
print("=" * 60)
sys.exit(0 if failed == 0 else 1)
