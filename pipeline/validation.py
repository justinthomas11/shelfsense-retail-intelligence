"""
ShelfSense — Data Validation & Deduplication
=============================================
Pure functions (no DB access) that sit between extraction and loading.
Bad records are rejected with a reason rather than silently dropped, so
every run can report exactly what it threw away.
"""

from dataclasses import replace

KNOWN_RETAILERS = {"BigBasket", "Blinkit", "Zepto", "JioMart"}
MAX_PRICE = 100_000.0       # anything above this is a parsing error for groceries
MAX_DISCOUNT_PCT = 90.0     # deeper "discounts" are almost always bad MRP parses
MRP_TOLERANCE = 1.05        # allow selling price up to 5% above MRP (rounding, surge)


def validate_record(record):
    """
    Return (cleaned_record, None) if valid, or (None, reason) if rejected.

    Cleaning rules:
      • Missing MRP → assume no discount (MRP = selling price)
      • Selling price slightly above MRP (within tolerance) → raise MRP to match
    """
    if record.retailer_name not in KNOWN_RETAILERS:
        return None, f"unknown retailer '{record.retailer_name}'"
    if not record.product_name or not record.product_name.strip():
        return None, "missing product name"
    if record.selling_price is None or record.selling_price <= 0:
        return None, "non-positive selling price"
    if record.selling_price > MAX_PRICE:
        return None, f"selling price {record.selling_price} exceeds {MAX_PRICE}"

    mrp = record.mrp if record.mrp and record.mrp > 0 else record.selling_price
    if record.selling_price > mrp * MRP_TOLERANCE:
        return None, f"selling price {record.selling_price} far above MRP {mrp}"
    mrp = max(mrp, record.selling_price)

    cleaned = replace(record, product_name=record.product_name.strip(), mrp=mrp)
    if cleaned.discount_pct > MAX_DISCOUNT_PCT:
        return None, f"implausible discount {cleaned.discount_pct}%"
    return cleaned, None


def validate_records(records):
    """Validate a batch. Returns (valid_records, [(record, reason), ...])."""
    valid, rejected = [], []
    for record in records:
        cleaned, reason = validate_record(record)
        if cleaned is None:
            rejected.append((record, reason))
        else:
            valid.append(cleaned)
    return valid, rejected


def deduplicate(records):
    """
    Keep one observation per (retailer, product, date) — the last one seen,
    mirroring the ON CONFLICT DO UPDATE semantics of the loader.
    """
    latest = {}
    for record in records:
        key = (record.retailer_name, record.product_name.lower(), record.price_date)
        latest[key] = record
    return list(latest.values())
