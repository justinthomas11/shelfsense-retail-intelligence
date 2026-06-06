"""
ShelfSense — Macroeconomic CPI Data Loader
===========================================
Generates and seeds monthly Consumer Price Index (CPI) and YoY inflation data
into the fact_macro_cpi table. Covers the period from Jan 2024 to Dec 2026.

This data supports View 10 (vw_inflation_adjusted_pricing).
"""

import sys
import os
import random
from datetime import date
from decimal import Decimal, ROUND_HALF_UP

# Allow importing config
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import psycopg2
from config.db_config import DB_CONFIG

# Baseline parameters by parent category
PARENT_PARAMS = {
    "Staples":       {"base_cpi": 180.0, "annual_growth": 0.055, "volatility": 0.008},
    "Dairy":         {"base_cpi": 175.0, "annual_growth": 0.048, "volatility": 0.005},
    "Snacks":        {"base_cpi": 168.0, "annual_growth": 0.040, "volatility": 0.004},
    "Beverages":     {"base_cpi": 172.0, "annual_growth": 0.042, "volatility": 0.004},
    "Personal Care": {"base_cpi": 165.0, "annual_growth": 0.035, "volatility": 0.003},
    "Household":     {"base_cpi": 160.0, "annual_growth": 0.038, "volatility": 0.003},
}

DEFAULT_PARAMS = {"base_cpi": 170.0, "annual_growth": 0.045, "volatility": 0.005}

# Seed random for reproducibility
random.seed(101)

def round_value(val, decimals=2):
    """Round to specified decimal places."""
    fmt = "0." + "0" * (decimals - 1) + "1" if decimals > 0 else "0"
    return float(Decimal(str(val)).quantize(Decimal(fmt), rounding=ROUND_HALF_UP))

def get_monthly_dates(start_year=2023, end_year=2026):
    """Generate first day of each month between start_year and end_year."""
    dates = []
    for y in range(start_year, end_year + 1):
        for m in range(1, 13):
            dates.append(date(y, m, 1))
    return dates

def get_seasonality_factor(month):
    """Simulate Indian food pricing seasonality (summer spikes, winter drops)."""
    # May, June, July (Summer) often have higher food inflation
    # October, November (Festivals) have high demand
    # December, January (Winter harvest) have lower prices
    if month in (5, 6, 7):
        return 0.002
    elif month in (10, 11):
        return 0.003
    elif month in (12, 1):
        return -0.002
    return 0.0

def main():
    print("=" * 55)
    print("  ShelfSense — Macro CPI Data Loader")
    print("=" * 55)
    
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    
    try:
        # Step 1: Fetch categories
        cur.execute("SELECT category_name, parent_category FROM dim_category")
        categories = cur.fetchall()
        if not categories:
            print("❌ No categories found in dim_category. Please seed dimensions first.")
            return
            
        print(f"  Loaded {len(categories)} categories from database.")
        
        # Step 2: Generate monthly CPI
        all_dates = get_monthly_dates(2023, 2026)
        cpi_data = {}  # key: (category_name, date), value: cpi_index
        
        for cat_name, parent in categories:
            params = PARENT_PARAMS.get(parent, DEFAULT_PARAMS)
            
            # Start CPI in Jan 2023 with category-specific variation
            current_cpi = params["base_cpi"] + random.uniform(-4.0, 4.0)
            
            # Generate chronologically month by month
            for dt in all_dates:
                # Calculate growth rate for this month
                base_monthly_rate = params["annual_growth"] / 12.0
                jitter = random.normalvariate(0, params["volatility"])
                seasonality = get_seasonality_factor(dt.month) if parent in ("Staples", "Dairy") else 0.0
                
                # Apply growth
                growth_factor = 1.0 + base_monthly_rate + jitter + seasonality
                current_cpi = current_cpi * growth_factor
                
                # Store
                cpi_data[(cat_name, dt)] = round_value(current_cpi, 2)
        
        # Step 3: Compute YoY Inflation and Filter to 2024-2026
        records = []
        # We only load 2024 to 2026 because we need 2023 as baseline for YoY comparison
        target_dates = [d for d in all_dates if d.year >= 2024]
        
        for cat_name, _ in categories:
            for dt in target_dates:
                current_cpi = cpi_data[(cat_name, dt)]
                
                # Retrieve same month in previous year
                prev_year_date = date(dt.year - 1, dt.month, 1)
                prev_cpi = cpi_data.get((cat_name, prev_year_date))
                
                if prev_cpi:
                    yoy_inflation = ((current_cpi - prev_cpi) / prev_cpi) * 100.0
                else:
                    # Fallback (should not happen since we have 2023 data)
                    yoy_inflation = 5.0
                    
                records.append((
                    dt,
                    cat_name,
                    current_cpi,
                    round_value(yoy_inflation, 2)
                ))
                
        print(f"  Generated {len(records)} monthly macro records (2024-2026).")
        
        # Step 4: Batch insert with ON CONFLICT DO UPDATE
        insert_sql = """
            INSERT INTO fact_macro_cpi (report_month, category_name, cpi_index, yoy_inflation)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (report_month, category_name) DO UPDATE SET
                cpi_index = EXCLUDED.cpi_index,
                yoy_inflation = EXCLUDED.yoy_inflation;
        """
        
        cur.executemany(insert_sql, records)
        conn.commit()
        print(f"  ✅ Successfully loaded CPI records into database!")
        
        # Print summary
        cur.execute("SELECT COUNT(*) FROM fact_macro_cpi")
        count = cur.fetchone()[0]
        print(f"  Total records in fact_macro_cpi: {count}")
        
        cur.execute("""
            SELECT category_name, ROUND(AVG(cpi_index), 2), ROUND(AVG(yoy_inflation), 2)
            FROM fact_macro_cpi
            GROUP BY category_name
            ORDER BY category_name LIMIT 5
        """)
        print("\n  Sample averages (first 5 categories):")
        for cat, avg_cpi, avg_inf in cur.fetchall():
            print(f"    - {cat:<22} Avg CPI: {avg_cpi:<8} Avg Inflation: {avg_inf}%")
            
    except Exception as e:
        conn.rollback()
        print(f"❌ Error seeding CPI data: {e}")
        raise
    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    main()
