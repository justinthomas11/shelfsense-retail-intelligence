"""
Integration checks against a live, populated database.

Skipped automatically when no database is reachable, so the default
`pytest` run stays offline. CI runs these after
`scripts/setup_database.py --with-data`.
"""

import re

import pytest

from conftest import PROJECT_ROOT

psycopg2 = pytest.importorskip("psycopg2")

VIEWS = re.findall(
    r"CREATE OR REPLACE VIEW (\w+)",
    (PROJECT_ROOT / "database" / "views" / "analytical_views.sql").read_text(encoding="utf-8"),
)


@pytest.fixture(scope="module")
def conn():
    try:
        from config.db_config import DB_CONFIG
    except ImportError:
        pytest.skip("config/db_config.py not present")
    try:
        connection = psycopg2.connect(**DB_CONFIG, connect_timeout=3)
    except psycopg2.OperationalError:
        pytest.skip("database not reachable")
    yield connection
    connection.close()


def scalar(conn, sql):
    with conn.cursor() as cur:
        cur.execute(sql)
        return cur.fetchone()[0]


def test_fact_tables_are_populated(conn):
    assert scalar(conn, "SELECT COUNT(*) FROM fact_price_history") > 0
    assert scalar(conn, "SELECT COUNT(*) FROM fact_macro_cpi") > 0


@pytest.mark.parametrize("view", VIEWS)
def test_view_returns_rows(conn, view):
    assert scalar(conn, f"SELECT COUNT(*) FROM {view}") > 0


def test_competitor_pricing_excludes_out_of_stock_prices(conn):
    leaked = scalar(conn, """
        SELECT COUNT(*)
        FROM vw_daily_competitor_pricing v
        JOIN dim_product p ON p.product_name = v.product_name
        JOIN fact_price_history f ON f.product_id = p.product_id
        JOIN dim_retailer r ON r.retailer_id = f.retailer_id AND r.retailer_name = 'Zepto'
        WHERE f.price_date = (SELECT MAX(price_date) FROM fact_price_history)
          AND NOT f.is_available
          AND v.zepto_price IS NOT NULL
    """)
    assert leaked == 0
