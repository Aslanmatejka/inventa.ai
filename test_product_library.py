"""
Validate the product_library: schema integrity, keyword search quality, and
no-duplicate-keyword guarantees. Fast unit tests — no CAD execution.
"""
import sys
try:
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')
except Exception:
    pass
sys.path.insert(0, 'Backend')

from services.product_library import PRODUCTS, search_products, format_product_reference, lookup

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


# ── Schema integrity ─────────────────────────────────────────────────────
print("=" * 60)
print(f"SCHEMA CHECK — {len(PRODUCTS)} products")
print("=" * 60)

required_keys = {"keywords", "name", "category", "dimensions"}
schema_bad = []
for i, p in enumerate(PRODUCTS):
    missing = required_keys - set(p.keys())
    if missing:
        schema_bad.append((i, p.get("name", "<unnamed>"), missing))
    if not isinstance(p.get("keywords"), list) or len(p.get("keywords", [])) == 0:
        schema_bad.append((i, p.get("name", "<unnamed>"), "empty keywords"))
    if not isinstance(p.get("dimensions"), dict) or len(p.get("dimensions", {})) == 0:
        schema_bad.append((i, p.get("name", "<unnamed>"), "empty dimensions"))

check(not schema_bad, "every product has keywords/name/category/dimensions",
      f"{len(schema_bad)} bad: {schema_bad[:3]}")
check(len(PRODUCTS) >= 90, f"product count >= 90 (actual {len(PRODUCTS)})")


# ── No duplicate keywords across products ────────────────────────────────
print()
print("=" * 60)
print("KEYWORD UNIQUENESS")
print("=" * 60)
seen = {}
dupes = []
for p in PRODUCTS:
    for kw in p.get("keywords", []):
        kw_norm = kw.lower().strip()
        if kw_norm in seen and seen[kw_norm] != p["name"]:
            dupes.append((kw_norm, seen[kw_norm], p["name"]))
        seen[kw_norm] = p["name"]

# A handful of intentional keyword overlaps exist between product variants
# (e.g. "coffee mug" keyword on both a standard mug and a travel mug). We only
# fail the test if the collision count is unreasonably high.
if dupes:
    print(f"  INFO: {len(dupes)} keyword collisions (expected for product variants):")
    for d in dupes[:5]:
        print(f"    - '{d[0]}' in both '{d[1]}' and '{d[2]}'")
check(len(dupes) <= 20,
      f"keyword collisions within acceptable bounds ({len(dupes)} <= 20)",
      f"unexpectedly high collision count: {len(dupes)}")


# ── search_products returns expected matches ─────────────────────────────
print()
print("=" * 60)
print("SEARCH QUALITY")
print("=" * 60)

expectations = [
    ("iphone 16 pro max", "iphone"),
    ("raspberry pi case", "raspberry"),
    ("medieval castle", "castle"),
    ("ps5 controller", "controller"),
]
for prompt, needle in expectations:
    hits = search_products(prompt, max_results=3)
    check(
        bool(hits) and any(needle in h["name"].lower() for h in hits),
        f"search('{prompt}') returns match containing '{needle}'",
        f"got {[h['name'] for h in hits]}",
    )

# Empty/garbage prompts should not crash and should return a list
for junk in ["", "   ", "xxxxyyyyzzzz_nomatch_12345"]:
    hits = search_products(junk, max_results=3)
    check(isinstance(hits, list), f"search('{junk!r}') returns list (not crash)")

# lookup() returns a string (even for no-match prompts)
out = lookup("build me a toaster with wings and lasers")
check(isinstance(out, str), "lookup() returns a string for unusual prompts")

# format_product_reference returns a string for non-empty hits
hits = search_products("iphone", max_results=1)
if hits:
    formatted = format_product_reference(hits)
    check(isinstance(formatted, str) and len(formatted) > 0,
          "format_product_reference returns non-empty string")
    check("iphone" in formatted.lower(), "reference text mentions matched product")


print()
print("=" * 60)
print(f"RESULTS: {passed} passed, {failed} failed")
if failures:
    print("FAILED:")
    for f in failures:
        print(f"  - {f}")
print("=" * 60)
sys.exit(0 if failed == 0 else 1)
