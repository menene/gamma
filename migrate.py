#!/usr/bin/env python3
"""
GAMMA migration runner.

Runs every .sql file in db/migrations/ that hasn't been applied yet, tracked
in public.schema_migrations. Idempotent and safe to re-run.

Usage (from anywhere with the env vars + db reachable):
    python migrate.py            # apply all pending migrations
    python migrate.py --status   # show which are applied / pending
    python migrate.py --dry-run  # show what would run, don't execute

Inside a container:
    docker compose exec api python migrate.py

Required env vars (matches api/app/db/__init__.py):
    DB_USER, DB_PASSWORD, DB_HOST, DB_PORT, DB_NAME
"""
import os
import sys
from pathlib import Path

import psycopg2


def _find_migrations_dir() -> Path:
    here = Path(__file__).resolve().parent
    candidates = [
        here / "db" / "migrations",     # repo root
        here / "migrations",            # mounted inside container
        Path("/app/migrations"),        # explicit container path
    ]
    for c in candidates:
        if c.is_dir():
            return c
    sys.exit(f"ERROR: no migrations dir found. Looked at: {[str(c) for c in candidates]}")


def _connect():
    missing = [v for v in ("DB_USER", "DB_PASSWORD", "DB_HOST", "DB_PORT", "DB_NAME") if not os.environ.get(v)]
    if missing:
        sys.exit(f"ERROR: missing env vars: {', '.join(missing)}")
    return psycopg2.connect(
        host=os.environ["DB_HOST"],
        port=os.environ["DB_PORT"],
        user=os.environ["DB_USER"],
        password=os.environ["DB_PASSWORD"],
        dbname=os.environ["DB_NAME"],
    )


def _ensure_tracking_table(conn):
    with conn.cursor() as cur:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS public.schema_migrations (
                filename    TEXT PRIMARY KEY,
                applied_at  TIMESTAMPTZ NOT NULL DEFAULT now()
            )
        """)
    conn.commit()


def _applied(conn) -> set[str]:
    with conn.cursor() as cur:
        cur.execute("SELECT filename FROM public.schema_migrations")
        return {row[0] for row in cur.fetchall()}


def _list_files(mig_dir: Path) -> list[Path]:
    return sorted(p for p in mig_dir.iterdir() if p.suffix == ".sql")


def cmd_status(mig_dir: Path):
    conn = _connect()
    _ensure_tracking_table(conn)
    done = _applied(conn)
    files = _list_files(mig_dir)
    print(f"Migrations dir: {mig_dir}")
    print(f"Total: {len(files)}  Applied: {len(done)}  Pending: {len(files) - len([f for f in files if f.name in done])}")
    print()
    for f in files:
        mark = "[x]" if f.name in done else "[ ]"
        print(f"  {mark} {f.name}")
    conn.close()


def cmd_run(mig_dir: Path, dry_run: bool):
    conn = _connect()
    _ensure_tracking_table(conn)
    done = _applied(conn)
    pending = [f for f in _list_files(mig_dir) if f.name not in done]

    if not pending:
        print("Nothing to do — all migrations applied.")
        conn.close()
        return

    print(f"Pending: {len(pending)} migration(s)")
    for f in pending:
        print(f"  → {f.name}")
    print()

    if dry_run:
        print("Dry run — no changes made.")
        conn.close()
        return

    for f in pending:
        sql = f.read_text()
        print(f"Applying {f.name} ...", end=" ", flush=True)
        try:
            with conn:
                with conn.cursor() as cur:
                    cur.execute(sql)
                    cur.execute(
                        "INSERT INTO public.schema_migrations (filename) VALUES (%s)",
                        (f.name,),
                    )
            print("OK")
        except Exception as e:
            print("FAILED")
            print(f"  {type(e).__name__}: {e}")
            sys.exit(1)

    print()
    print(f"Done. Applied {len(pending)} migration(s).")
    conn.close()


def main():
    args = sys.argv[1:]
    mig_dir = _find_migrations_dir()

    if "--status" in args:
        cmd_status(mig_dir)
    else:
        cmd_run(mig_dir, dry_run="--dry-run" in args)


if __name__ == "__main__":
    main()
