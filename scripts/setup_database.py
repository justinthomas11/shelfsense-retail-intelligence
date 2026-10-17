"""
ShelfSense — Database Setup
============================
One-command bootstrap for the PostgreSQL warehouse. No psql client required.

Steps:
  1. Create the target database if it does not exist
  2. Run the DDL + dimension seed scripts in database/schema/ (in order)
  3. Optionally load simulated price history and CPI data (--with-data)
  4. Create all analytical views in database/views/

Every step is idempotent, so the script is safe to re-run.

Usage:
    python scripts/setup_database.py              # schema + views only
    python scripts/setup_database.py --with-data  # also load simulated data
"""

import argparse
import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import psycopg2
from psycopg2 import sql
from config.db_config import DB_CONFIG

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SCHEMA_DIR = PROJECT_ROOT / "database" / "schema"
VIEWS_DIR = PROJECT_ROOT / "database" / "views"


def ensure_database_exists():
    """Connect to the maintenance DB and create the target DB if missing."""
    admin_config = {**DB_CONFIG, "dbname": "postgres"}
    conn = psycopg2.connect(**admin_config)
    conn.autocommit = True  # CREATE DATABASE cannot run inside a transaction
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT 1 FROM pg_database WHERE datname = %s", (DB_CONFIG["dbname"],))
            if cur.fetchone():
                print(f"  Database '{DB_CONFIG['dbname']}' already exists.")
            else:
                cur.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(DB_CONFIG["dbname"])))
                print(f"  ✅ Created database '{DB_CONFIG['dbname']}'.")
    finally:
        conn.close()


def run_sql_files(directory):
    """Execute every .sql file in a directory, sorted by filename."""
    files = sorted(directory.glob("*.sql"))
    conn = psycopg2.connect(**DB_CONFIG)
    try:
        with conn.cursor() as cur:
            for path in files:
                cur.execute(path.read_text(encoding="utf-8"))
                print(f"  ✅ {path.relative_to(PROJECT_ROOT)}")
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def load_simulated_data():
    """Populate fact tables using the data simulator and CPI loader."""
    from data_simulator import simulate_prices, load_cpi
    simulate_prices.main()
    load_cpi.main()


def main():
    parser = argparse.ArgumentParser(description="Bootstrap the ShelfSense database.")
    parser.add_argument("--with-data", action="store_true",
                        help="load 90 days of simulated prices and CPI data")
    args = parser.parse_args()

    print("=" * 55)
    print("  ShelfSense — Database Setup")
    print("=" * 55)

    print("\n[1/4] Checking database...")
    ensure_database_exists()

    print("\n[2/4] Creating tables and seeding dimensions...")
    run_sql_files(SCHEMA_DIR)

    print("\n[3/4] Loading data...")
    if args.with_data:
        load_simulated_data()
    else:
        print("  Skipped (pass --with-data to load simulated data).")

    print("\n[4/4] Creating analytical views...")
    run_sql_files(VIEWS_DIR)

    print("\n✅ Setup complete!")


if __name__ == "__main__":
    main()
