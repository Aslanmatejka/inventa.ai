"""
Test the AI code safety allowlist/denylist in ParametricCADService._validate_code_safety.
This is the primary security boundary around exec() of Claude-generated code.
"""
import sys
import os
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


def expect_safe(code: str, label: str):
    global passed, failed
    try:
        svc._validate_code_safety(code)
        print(f"  PASS: {label}")
        passed += 1
    except Exception as e:
        print(f"  FAIL: {label} -> unexpectedly blocked: {e}")
        failed += 1
        failures.append(label)


def expect_blocked(code: str, label: str, must_contain: str = None):
    global passed, failed
    try:
        svc._validate_code_safety(code)
        print(f"  FAIL: {label} -> should have been blocked")
        failed += 1
        failures.append(label)
    except ValueError as e:
        msg = str(e)
        if must_contain and must_contain.lower() not in msg.lower():
            print(f"  FAIL: {label} -> blocked but wrong reason: {msg}")
            failed += 1
            failures.append(label)
        else:
            print(f"  PASS: {label} ({msg[:60]})")
            passed += 1
    except Exception as e:
        print(f"  FAIL: {label} -> wrong exception type: {type(e).__name__}: {e}")
        failed += 1
        failures.append(label)


print("=" * 60)
print("SAFE CODE (should pass)")
print("=" * 60)

expect_safe(
    "import cadquery as cq\nresult = cq.Workplane('XY').box(10, 10, 10)",
    "basic cadquery import"
)
expect_safe(
    "import cadquery as cq\nimport math\nimport copy\nresult = cq.Workplane('XY').circle(math.pi).extrude(5)",
    "math + copy imports"
)
expect_safe(
    "import cadquery as cq\nimport numpy as np\nresult = cq.Workplane('XY').box(10,10,10)",
    "numpy as np"
)
# Note: the validator requires a literal "import cadquery" or "import cq" substring,
# so bare `from cadquery import X` is (intentionally) rejected — Claude is instructed
# to use `import cadquery as cq`. We lock that contract in:
expect_blocked(
    "from cadquery import Workplane\nresult = Workplane('XY').box(5,5,5)",
    "bare 'from cadquery import' rejected (must use 'import cadquery as cq')",
    must_contain="cadquery",
)
expect_safe(
    "import cadquery as cq\n# socket_depth = 5 is a legitimate CAD feature name\nsocket_depth = 5\nresult = cq.Workplane('XY').box(10, 10, socket_depth)",
    "word 'socket' in variable name (not import)"
)
expect_safe(
    "import cadquery as cq\n# http_port_cutout = 8 is a CAD feature\nhttp_port = 8\nresult = cq.Workplane('XY').box(http_port, 10, 10)",
    "word 'http' in variable name (not import)"
)

print()
print("=" * 60)
print("UNSAFE CODE (should be blocked)")
print("=" * 60)

expect_blocked(
    "import os\nresult = os.listdir('.')",
    "import os",
    must_contain="os",
)
expect_blocked(
    "import subprocess\nsubprocess.run(['ls'])",
    "import subprocess",
    must_contain="subprocess",
)
expect_blocked(
    "import cadquery as cq\nimport socket\ns = socket.socket()\nresult = cq.Workplane('XY').box(1,1,1)",
    "import socket",
    must_contain="socket",
)
expect_blocked(
    "from os import path\nresult = None",
    "from os import path",
    must_contain="os",
)
expect_blocked(
    "import cadquery as cq\nimport requests\nresult = cq.Workplane('XY').box(1,1,1)",
    "import requests",
    must_contain="requests",
)
expect_blocked(
    "import cadquery as cq\neval('1+1')\nresult = cq.Workplane('XY').box(1,1,1)",
    "eval() call",
    must_contain="eval(",
)
expect_blocked(
    "import cadquery as cq\nexec('x=1')\nresult = cq.Workplane('XY').box(1,1,1)",
    "exec() call",
    must_contain="exec(",
)
expect_blocked(
    "import cadquery as cq\nopen('/etc/passwd').read()\nresult = cq.Workplane('XY').box(1,1,1)",
    "open() call",
    must_contain="open(",
)
# The __subclasses__ escape contains multiple dangerous dunders; any one of them
# being blocked is sufficient (whichever the validator hits first).
expect_blocked(
    "import cadquery as cq\nx = (1).__class__.__bases__[0].__subclasses__()\nresult = cq.Workplane('XY').box(1,1,1)",
    "__subclasses__ / __class__ escape blocked",
)
expect_blocked(
    "import cadquery as cq\n__builtins__['print']('hi')\nresult = cq.Workplane('XY').box(1,1,1)",
    "__builtins__ access",
    must_contain="__builtins__",
)
expect_blocked(
    "import random\nresult = random.random()",
    "non-allowlisted import 'random'",
    must_contain="random",
)
expect_blocked(
    "result = 1",
    "missing cadquery import",
    must_contain="cadquery",
)

print()
print("=" * 60)
print(f"RESULTS: {passed} passed, {failed} failed")
if failures:
    print("FAILED:")
    for f in failures:
        print(f"  - {f}")
print("=" * 60)
sys.exit(0 if failed == 0 else 1)
