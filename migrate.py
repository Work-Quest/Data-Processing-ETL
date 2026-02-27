import os
import psycopg2
from pathlib import Path

from config import FEATURE_DB_URL

MIGRATIONS_DIR = Path("migrations")


def ensure_migration_table(conn):
    """Create migration tracking table if not exists"""
    with conn.cursor() as cur:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS schema_migrations (
                version TEXT PRIMARY KEY,
                applied_at TIMESTAMP DEFAULT NOW()
            );
        """)
        conn.commit()


def get_applied_migrations(conn):
    with conn.cursor() as cur:
        cur.execute("SELECT version FROM schema_migrations;")
        rows = cur.fetchall()
        return {row[0] for row in rows}


def apply_migration(conn, filepath):
    version = filepath.name

    print(f"Applying {version}...")

    with open(filepath, "r", encoding="utf-8") as f:
        sql = f.read()

    with conn.cursor() as cur:
        cur.execute(sql)
        cur.execute(
            "INSERT INTO schema_migrations (version) VALUES (%s);",
            (version,)
        )
        conn.commit()

    print(f"✓ Applied {version}")


def run():
    conn = psycopg2.connect(FEATURE_DB_URL)

    ensure_migration_table(conn)
    applied = get_applied_migrations(conn)

    migration_files = sorted(MIGRATIONS_DIR.glob("*.sql"))

    for filepath in migration_files:
        if filepath.name not in applied:
            apply_migration(conn, filepath)
        else:
            print(f"Skipping {filepath.name} (already applied)")

    conn.close()
    print("All migrations completed.")


if __name__ == "__main__":
    run()