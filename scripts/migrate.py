"""
Database migration runner for TEX v2.

Reads .sql files from backend/migrations/, applies them in filename order,
and tracks applied migrations in a schema_migrations table.

Usage:
    python scripts/migrate.py

Requires NEON_HOST, NEON_DB, NEON_USER, NEON_PASSWORD environment variables.
"""

import os
import sys

import psycopg2

MIGRATIONS_DIR = os.path.join(os.path.dirname(__file__), "..", "backend", "migrations")


def get_connection():
    return psycopg2.connect(
        host=os.environ["NEON_HOST"],
        database=os.environ["NEON_DB"],
        user=os.environ["NEON_USER"],
        password=os.environ["NEON_PASSWORD"],
        sslmode="require",
        connect_timeout=10,
    )


def ensure_schema_migrations_table(conn):
    with conn.cursor() as cur:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS schema_migrations (
                filename   text        PRIMARY KEY,
                applied_at timestamptz NOT NULL DEFAULT now()
            );
        """)
    conn.commit()


def get_applied_migrations(conn):
    with conn.cursor() as cur:
        cur.execute("SELECT filename FROM schema_migrations ORDER BY filename;")
        return {row[0] for row in cur.fetchall()}


def get_pending_migrations(applied):
    files = sorted(f for f in os.listdir(MIGRATIONS_DIR) if f.endswith(".sql"))
    return [f for f in files if f not in applied]


def apply_migration(conn, filename):
    filepath = os.path.join(MIGRATIONS_DIR, filename)
    with open(filepath, "r") as f:
        sql = f.read()

    with conn.cursor() as cur:
        cur.execute(sql)
        cur.execute(
            "INSERT INTO schema_migrations (filename) VALUES (%s);",
            (filename,),
        )
    conn.commit()


def main():
    # Load .env if python-dotenv is available (local dev)
    try:
        from dotenv import load_dotenv
        load_dotenv(os.path.join(os.path.dirname(__file__), "..", "backend", ".env"))
    except ImportError:
        pass

    for var in ("NEON_HOST", "NEON_DB", "NEON_USER", "NEON_PASSWORD"):
        if not os.environ.get(var):
            print(f"ERROR: {var} environment variable is not set.")
            sys.exit(1)

    conn = get_connection()
    try:
        ensure_schema_migrations_table(conn)
        applied = get_applied_migrations(conn)
        pending = get_pending_migrations(applied)

        if not pending:
            print("All migrations already applied.")
            return

        for filename in pending:
            print(f"Applying {filename}...", end=" ")
            try:
                apply_migration(conn, filename)
                print("done.")
            except Exception as e:
                conn.rollback()
                print(f"FAILED.\n  Error: {e}")
                sys.exit(1)

        print(f"\n{len(pending)} migration(s) applied successfully.")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
