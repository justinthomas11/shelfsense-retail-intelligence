"""
ShelfSense — Warehouse Loader
==============================
Upserts validated ScrapedPrice records into fact_price_history.

  • Resolves retailer and product names to surrogate keys
  • Registers catalog products missing from dim_product on the fly
  • Uses ON CONFLICT DO UPDATE so re-running a day is idempotent
"""

import logging

from psycopg2.extras import execute_values

from data_simulator.product_catalog import PRODUCT_CATALOG

logger = logging.getLogger(__name__)

CATALOG_BY_NAME = {p["name"]: p for p in PRODUCT_CATALOG}

UPSERT_SQL = """
    INSERT INTO fact_price_history
        (product_id, retailer_id, price_date, mrp, selling_price, discount_pct, is_available)
    VALUES %s
    ON CONFLICT (product_id, retailer_id, price_date) DO UPDATE SET
        mrp = EXCLUDED.mrp,
        selling_price = EXCLUDED.selling_price,
        discount_pct = EXCLUDED.discount_pct,
        is_available = EXCLUDED.is_available
"""


def _retailer_ids(cur):
    cur.execute("SELECT retailer_name, retailer_id FROM dim_retailer")
    return dict(cur.fetchall())


def _product_ids(cur):
    cur.execute("SELECT product_name, product_id FROM dim_product")
    return dict(cur.fetchall())


def _register_product(cur, name):
    """Insert a catalog product into dim_product and return its id (or None)."""
    product = CATALOG_BY_NAME.get(name)
    if product is None:
        return None
    cur.execute(
        """INSERT INTO dim_product (product_name, brand, unit_size, category_id)
           SELECT %s, %s, %s, category_id FROM dim_category WHERE category_name = %s
           RETURNING product_id""",
        (product["name"], product["brand"], product["unit"], product["category"]),
    )
    row = cur.fetchone()
    return row[0] if row else None


def load_records(conn, records):
    """Upsert records in a single transaction. Returns number of rows written."""
    with conn.cursor() as cur:
        retailer_ids = _retailer_ids(cur)
        product_ids = _product_ids(cur)

        rows, skipped = [], 0
        for r in records:
            pid = product_ids.get(r.product_name)
            if pid is None:
                pid = _register_product(cur, r.product_name)
                if pid is not None:
                    product_ids[r.product_name] = pid
            rid = retailer_ids.get(r.retailer_name)
            if pid is None or rid is None:
                skipped += 1
                continue
            rows.append((pid, rid, r.price_date, r.mrp, r.selling_price,
                         r.discount_pct if r.is_available else 0.0, r.is_available))

        if skipped:
            logger.warning("Skipped %d records with unknown product/retailer", skipped)
        if rows:
            execute_values(cur, UPSERT_SQL, rows, page_size=1000)
    conn.commit()
    return len(rows)
