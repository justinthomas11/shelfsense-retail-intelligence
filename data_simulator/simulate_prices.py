"""
ShelfSense — Realistic Price Data Simulator
=============================================
Generates 90 days of daily pricing data across 4 retailers and ~75 products,
producing ~27,000 rows of realistic time-series data in fact_price_history.

Realistic behaviors modeled:
  • Each retailer has a different pricing strategy (discount range)
  • Daily price jitter (±2%) simulates real market fluctuations
  • Weekend/festival sale events with deeper discounts
  • Random stockout events (~5% chance per product per day)
  • Gradual inflation trend (~0.1% per week on base prices)
  • Category-specific volatility (oils more volatile than biscuits)

Usage:
    python data_simulator/simulate_prices.py
"""

import sys
import os
import random
from datetime import date, timedelta
from decimal import Decimal, ROUND_HALF_UP

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import psycopg2
from config.db_config import DB_CONFIG
from data_simulator.product_catalog import PRODUCT_CATALOG

# ── Configuration ──────────────────────────────────────────────────────
SIMULATION_DAYS = 90   # 3 months of historical data
END_DATE = date.today()
START_DATE = END_DATE - timedelta(days=SIMULATION_DAYS - 1)

# Retailer-specific pricing strategies
# (min_discount%, max_discount%, stockout_probability)
RETAILER_STRATEGIES = {
    "BigBasket":  {"min_disc": 2,  "max_disc": 18, "stockout_prob": 0.03, "bias": -0.02},
    "Blinkit":    {"min_disc": 5,  "max_disc": 25, "stockout_prob": 0.05, "bias":  0.01},
    "Zepto":      {"min_disc": 3,  "max_disc": 22, "stockout_prob": 0.04, "bias":  0.00},
    "JioMart":    {"min_disc": 8,  "max_disc": 30, "stockout_prob": 0.02, "bias": -0.03},
}

# Category-specific price volatility multipliers
CATEGORY_VOLATILITY = {
    "Rice & Grains": 0.8,       "Pulses & Lentils": 1.2,
    "Cooking Oil": 1.5,         "Spices & Masala": 0.6,
    "Flour & Atta": 0.7,        "Sugar & Jaggery": 1.3,
    "Milk": 0.3,                "Curd & Yogurt": 0.4,
    "Paneer & Cheese": 0.5,     "Butter & Ghee": 0.6,
    "Biscuits & Cookies": 0.3,  "Chips & Namkeen": 0.4,
    "Chocolates": 0.3,          "Tea & Coffee": 0.8,
    "Soft Drinks & Juices": 0.5,"Soap & Bodywash": 0.3,
    "Shampoo & Conditioner": 0.4,"Toothpaste": 0.3,
    "Detergent": 0.5,           "Dishwash": 0.4,
}

# Sale events (simulating Big Billion Days, Republic Day Sale, etc.)
SALE_EVENTS = [
    # (start_offset_from_end, duration_days, extra_discount_pct)
    (85, 4, 12),   # ~3 months ago: "New Year Sale"
    (60, 3, 15),   # ~2 months ago: "Republic Day Sale"
    (30, 5, 18),   # ~1 month ago: "Big Savings Week"
    (10, 3, 10),   # ~10 days ago: "Weekend Special"
]

random.seed(42)  # Reproducible results


def round_price(value):
    """Round price to 2 decimal places."""
    return float(Decimal(str(value)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))


def is_sale_day(day_offset):
    """Check if a given day falls within any sale event."""
    for start, duration, extra_disc in SALE_EVENTS:
        if start <= day_offset < start + duration:
            return extra_disc
    return 0


def get_weekend_boost(current_date):
    """Weekends get slightly higher discounts."""
    if current_date.weekday() in (5, 6):  # Saturday, Sunday
        return random.uniform(2, 5)
    return 0


def insert_products(cur):
    """Insert products from catalog into dim_product, return product_id mapping."""
    product_ids = {}

    # Get category_id mapping
    cur.execute("SELECT category_id, category_name FROM dim_category")
    category_map = {row[1]: row[0] for row in cur.fetchall()}

    for product in PRODUCT_CATALOG:
        cat_id = category_map.get(product["category"])
        if cat_id is None:
            print(f"  ⚠️  Category '{product['category']}' not found, skipping {product['name']}")
            continue

        # Check if product already exists
        cur.execute(
            "SELECT product_id FROM dim_product WHERE product_name = %s AND brand = %s",
            (product["name"], product["brand"])
        )
        row = cur.fetchone()
        if row:
            product_ids[product["name"]] = row[0]
        else:
            cur.execute(
                """INSERT INTO dim_product (product_name, brand, unit_size, category_id)
                   VALUES (%s, %s, %s, %s) RETURNING product_id""",
                (product["name"], product["brand"], product["unit"], cat_id)
            )
            product_ids[product["name"]] = cur.fetchone()[0]

    return product_ids


def insert_retailers(cur):
    """Get retailer_id mapping."""
    cur.execute("SELECT retailer_id, retailer_name FROM dim_retailer")
    return {row[1]: row[0] for row in cur.fetchall()}


def generate_prices(product_ids, retailer_ids):
    """Generate all price records."""
    records = []
    total_products = len(PRODUCT_CATALOG)

    for p_idx, product in enumerate(PRODUCT_CATALOG):
        pid = product_ids.get(product["name"])
        if pid is None:
            continue

        base_mrp = product["base_mrp"]
        category = product["category"]
        volatility = CATEGORY_VOLATILITY.get(category, 0.5)

        for retailer_name, strategy in RETAILER_STRATEGIES.items():
            rid = retailer_ids.get(retailer_name)
            if rid is None:
                continue

            # Each retailer has a slightly different MRP perception
            retailer_mrp = base_mrp * (1 + strategy["bias"])

            for day_offset in range(SIMULATION_DAYS):
                current_date = START_DATE + timedelta(days=day_offset)

                # ── Inflation trend: ~0.1% per week ──
                weeks_elapsed = day_offset / 7.0
                inflation_factor = 1 + (0.001 * weeks_elapsed)

                # ── Daily price jitter (±2% scaled by category volatility) ──
                jitter = random.gauss(0, 0.02 * volatility)

                # ── Calculate MRP for this day ──
                mrp = retailer_mrp * inflation_factor * (1 + jitter)
                mrp = round_price(mrp)

                # ── Stockout check ──
                if random.random() < strategy["stockout_prob"]:
                    records.append((
                        pid, rid, current_date,
                        mrp, mrp,  # selling_price = mrp when unavailable
                        0.0, False
                    ))
                    continue

                # ── Calculate discount ──
                base_discount = random.uniform(strategy["min_disc"], strategy["max_disc"])

                # Sale event bonus
                sale_bonus = is_sale_day(day_offset)

                # Weekend bonus
                weekend_bonus = get_weekend_boost(current_date)

                total_discount = min(base_discount + sale_bonus + weekend_bonus, 45)  # cap at 45%

                # ── Selling price ──
                selling_price = mrp * (1 - total_discount / 100)
                selling_price = round_price(selling_price)
                discount_pct = round_price(total_discount)

                records.append((
                    pid, rid, current_date,
                    mrp, selling_price,
                    discount_pct, True
                ))

        # Progress indicator
        if (p_idx + 1) % 10 == 0 or p_idx == total_products - 1:
            print(f"  Generated prices for {p_idx + 1}/{total_products} products...")

    return records


def main():
    print("=" * 55)
    print("  ShelfSense — Price Data Simulator")
    print("=" * 55)
    print(f"\n  Date range:  {START_DATE} → {END_DATE}")
    print(f"  Days:        {SIMULATION_DAYS}")
    print(f"  Products:    {len(PRODUCT_CATALOG)}")
    print(f"  Retailers:   {len(RETAILER_STRATEGIES)}")
    print(f"  Expected rows: ~{SIMULATION_DAYS * len(PRODUCT_CATALOG) * len(RETAILER_STRATEGIES):,}")
    print()

    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()

    try:
        # Step 1: Insert products
        print("[1/3] Inserting products into dim_product...")
        product_ids = insert_products(cur)
        conn.commit()
        print(f"  ✅ {len(product_ids)} products loaded.\n")

        # Step 2: Get retailers
        print("[2/3] Loading retailer mapping...")
        retailer_ids = insert_retailers(cur)
        print(f"  ✅ {len(retailer_ids)} retailers found.\n")

        # Step 3: Generate & insert price data
        print("[3/3] Generating price history...")
        records = generate_prices(product_ids, retailer_ids)
        print(f"\n  Total records generated: {len(records):,}")
        print("  Inserting into database (batch insert)...")

        # Batch insert using executemany with ON CONFLICT
        insert_sql = """
            INSERT INTO fact_price_history 
                (product_id, retailer_id, price_date, mrp, selling_price, discount_pct, is_available)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (product_id, retailer_id, price_date) DO UPDATE SET
                mrp = EXCLUDED.mrp,
                selling_price = EXCLUDED.selling_price,
                discount_pct = EXCLUDED.discount_pct,
                is_available = EXCLUDED.is_available
        """

        # Insert in batches of 5000
        batch_size = 5000
        for i in range(0, len(records), batch_size):
            batch = records[i:i + batch_size]
            cur.executemany(insert_sql, batch)
            print(f"    Inserted batch {i // batch_size + 1}/{(len(records) // batch_size) + 1}")

        conn.commit()
        print(f"\n  ✅ {len(records):,} price records inserted!")

        # ── Summary stats ──
        print("\n" + "-" * 55)
        print("  Database Summary")
        print("-" * 55)

        cur.execute("SELECT COUNT(*) FROM dim_product")
        print(f"  dim_product:         {cur.fetchone()[0]:,} products")

        cur.execute("SELECT COUNT(*) FROM fact_price_history")
        print(f"  fact_price_history:  {cur.fetchone()[0]:,} price records")

        cur.execute("SELECT COUNT(*) FROM fact_price_history WHERE is_available = FALSE")
        print(f"  Stockout records:    {cur.fetchone()[0]:,}")

        cur.execute("SELECT MIN(price_date), MAX(price_date) FROM fact_price_history")
        min_d, max_d = cur.fetchone()
        print(f"  Date range:          {min_d} → {max_d}")

        cur.execute("""
            SELECT r.retailer_name, COUNT(*), ROUND(AVG(f.discount_pct), 1)
            FROM fact_price_history f
            JOIN dim_retailer r ON f.retailer_id = r.retailer_id
            GROUP BY r.retailer_name ORDER BY r.retailer_name
        """)
        print("\n  Per-retailer breakdown:")
        for name, count, avg_disc in cur.fetchall():
            print(f"    {name:<12} {count:>6,} records  |  avg discount: {avg_disc}%")

        print("\n✅ Simulation complete! Your database is ready for analysis.")

    except Exception as e:
        conn.rollback()
        print(f"\n❌ Error: {e}")
        raise
    finally:
        cur.close()
        conn.close()


if __name__ == "__main__":
    main()
