"""Test database connection (PostgreSQL or SQLite).

This script intentionally does NOT hardcode credentials. It uses `DATABASE_URL`
from your environment / `python-scrapper/.env`.
"""

from __future__ import annotations

import os
import sys
from urllib.parse import urlparse


def safe_db_label(database_url: str) -> str:
    """Return a redacted, human-friendly label for logs."""
    parsed = urlparse(database_url)
    host = parsed.hostname or "unknown-host"
    port = str(parsed.port) if parsed.port else ""
    db_name = (parsed.path or "").lstrip("/") or "unknown-db"
    return f"{host}{(':' + port) if port else ''}/{db_name}"


def main() -> int:
    # Best-effort load of `python-scrapper/.env` for local development.
    try:
        from dotenv import load_dotenv  # type: ignore

        load_dotenv(override=False)
    except Exception:
        pass

    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        print("ERROR: DATABASE_URL is not set.")
        print("Set it in `python-scrapper/.env` or your shell environment.")
        return 1

    try:
        from app.core.db import engine
        from sqlalchemy import text

        print("=" * 60)
        print("Testing Database Connection")
        print("=" * 60)
        print(f"Target: {safe_db_label(database_url)}")
        print("=" * 60)

        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))

            if engine.dialect.name == "postgresql":
                version = conn.execute(text("SELECT version();")).fetchone()[0]
                db_name = conn.execute(text("SELECT current_database();")).fetchone()[0]
                print("OK: Connection successful")
                print(f"PostgreSQL version: {version}")
                print(f"Current database: {db_name}")

                rows = conn.execute(
                    text(
                        """
                        SELECT table_name
                        FROM information_schema.tables
                        WHERE table_schema = 'public'
                        ORDER BY table_name;
                        """
                    )
                ).fetchall()
                tables = [row[0] for row in rows]
                print(f"\nTables in database: {len(tables)}")
                for table in tables[:10]:
                    print(f"  - {table}")
                if len(tables) > 10:
                    print(f"  ... and {len(tables) - 10} more")
            else:
                print("OK: Connection successful")
                print(f"Dialect: {engine.dialect.name}")

        print("\n" + "=" * 60)
        print("OK: Database connection test PASSED")
        print("=" * 60)
        return 0

    except Exception as exc:
        print("\n" + "=" * 60)
        print("ERROR: Database connection test FAILED")
        print("=" * 60)
        print(f"Error: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
