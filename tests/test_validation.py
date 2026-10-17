from datetime import date

from pipeline.validation import deduplicate, validate_record, validate_records


def test_valid_record_passes_unchanged(make_record):
    cleaned, reason = validate_record(make_record())
    assert reason is None
    assert cleaned.mrp == 285.0


def test_missing_mrp_defaults_to_selling_price(make_record):
    cleaned, _ = validate_record(make_record(mrp=None))
    assert cleaned.mrp == 250.0
    assert cleaned.discount_pct == 0.0


def test_selling_slightly_above_mrp_is_clamped(make_record):
    cleaned, reason = validate_record(make_record(selling_price=290.0, mrp=285.0))
    assert reason is None
    assert cleaned.mrp == 290.0


def test_product_name_is_stripped(make_record):
    cleaned, _ = validate_record(make_record(product_name="  Amul Butter "))
    assert cleaned.product_name == "Amul Butter"


def test_rejections(make_record):
    cases = {
        "unknown retailer": make_record(retailer_name="Amazon"),
        "missing product name": make_record(product_name="  "),
        "non-positive": make_record(selling_price=0),
        "exceeds": make_record(selling_price=250_000, mrp=300_000),
        "far above MRP": make_record(selling_price=400, mrp=285),
        "implausible discount": make_record(selling_price=5, mrp=285),
    }
    for expected, record in cases.items():
        cleaned, reason = validate_record(record)
        assert cleaned is None
        assert expected in reason


def test_validate_records_splits_batch(make_record):
    valid, rejected = validate_records([make_record(), make_record(selling_price=-1)])
    assert len(valid) == 1
    assert len(rejected) == 1


def test_deduplicate_keeps_last_observation(make_record):
    first = make_record(selling_price=250.0)
    second = make_record(product_name="amul butter", selling_price=240.0)
    other_day = make_record(price_date=date(2020, 1, 1))
    result = deduplicate([first, second, other_day])
    assert len(result) == 2
    assert 240.0 in [r.selling_price for r in result]
