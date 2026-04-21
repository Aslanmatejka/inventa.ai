"""
Lightweight migration runner for inventa.ai.

Applies each .sql file in migrations/ in lexicographic order against the
Supabase Postgres database. Idempotent: tracks applied migrations in a
`_migrations` table so re-running is a no-op.

Usage:
    python scripts/apply_migrations.py
    python scripts/apply_migrations.py --dry-run
    DATABASE_URL=postgres://... python scripts/apply_migrations.py
"""
from __future__ import annotations

import argparse
import hashlib
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MIGRATIONS_DIR = ROOT / "migrations"


def _get_database_url() -> str | None:
    url = os.environ.get("DATABASE_URL")
    if url:
        return url
    # Fall back to Supabase settings
    try:
        sys.path.insert(0, str(ROOT / "Backend"))
        from config import settings  # noqa: E402
        # Supabase connection strings are not in settings by default.
        # Users should set DATABASE_URL directly.
        return getattr(settings, "DATABASE_URL", None)
    except Exception:
        return None


def _checksum(sql: str) -> str:
    return hashlib.sha256(sql.encode("utf-8")).hexdigest()[:16]


def main() -> int:
    parser = argparse.ArgumentParser(description="Apply pending SQL migrations.")
    parser.add_argument("--dry-run", action="store_true", help="Show what would run.")
    args = parser.parse_args()

    if not MIGRATIONS_DIR.exists():
        print(f"❌ migrations/ directory not found at {MIGRATIONS_DIR}")
        return 1

    migrations = sorted(MIGRATIONS_DIR.glob("*.sql"))
    if not migrations:
        print("ℹ️  No .sql files found in migrations/")
        return 0

    db_url = _get_database_url()
    if not db_url:
        print("❌ DATABASE_URL not set. Export it before running:")
        print('   export DATABASE_URL="postgresql://user:pw@host:5432/db"')
        return 1

    try:
        import psycopg  # type: ignore
    except ImportError:
        try:
            import psycopg2 as psycopg  # type: ignore
        except ImportError:
            print("❌ psycopg (v3) or psycopg2 is required. Install: pip install psycopg[binary]")
            return 1

    if args.dry_run:
        print("DRY RUN — migrations that would apply:")
        for m in migrations:
            print(f"  • {m.name}  (sha256={_checksum(m.read_text(encoding='utf-8'))})")
        return 0

    conn = psycopg.connect(db_url)
    conn.autocommit = False
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS _migrations (
                    name TEXT PRIMARY KEY,
                    checksum TEXT NOT NULL,
                    applied_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                );
                """
            )
        conn.commit()

        applied: set[str] = set()
        with conn.cursor() as cur:
            cur.execute("SELECT name FROM _migrations;")
            applied = {row[0] for row in cur.fetchall()}

        new_count = 0
        for m in migrations:
            if m.name in applied:
                print(f"  ✓ {m.name} (already applied)")
                continue
            sql = m.read_text(encoding="utf-8")
            cksum = _checksum(sql)
            print(f"  → applying {m.name} (sha256={cksum})")
            with conn.cursor() as cur:
                cur.execute(sql)
                cur.execute(
                    "INSERT INTO _migrations (name, checksum) VALUES (%s, %s);",
                    (m.name, cksum),
                )
            conn.commit()
            new_count += 1

        print(f"✅ Migrations complete. {new_count} new, {len(applied)} pre-existing.")
        return 0
    except Exception as e:
        conn.rollback()
        print(f"❌ Migration failed: {e}")
        return 1
    finally:
        conn.close()


if __name__ == "__main__":
    sys.exit(main())
