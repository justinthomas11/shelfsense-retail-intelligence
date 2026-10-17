from datetime import date

import pytest

from pipeline import loader


class FakeCursor:
    """Answers the loader's lookup queries from in-memory dimension tables."""

    def __init__(self, db):
        self.db = db
        self._result = []

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def execute(self, query, params=None):
        if "FROM dim_retailer" in query:
            self._result = list(self.db["retailers"].items())
        elif "SELECT product_name, product_id" in query:
            self._result = list(self.db["products"].items())
        elif "INSERT INTO dim_product" in query:
            new_id = max(self.db["products"].values(), default=0) + 1
            self.db["products"][params[0]] = new_id
            self._result = [(new_id,)]

    def fetchall(self):
        return self._result

    def fetchone(self):
        return self._result[0] if self._result else None


class FakeConnection:
    def __init__(self, db):
        self.db = db
        self.committed = False

    def cursor(self):
        return FakeCursor(self.db)

    def commit(self):
        self.committed = True


@pytest.fixture
def db(monkeypatch):
    state = {
        "retailers": {"BigBasket": 1, "Zepto": 3},
        "products": {"Amul Butter": 10},
        "upserted": [],
    }
    monkeypatch.setattr(loader, "execute_values",
                        lambda cur, sql, rows, page_size: state["upserted"].extend(rows))
    return state


def test_load_records_upserts_with_resolved_keys(db, make_record):
    conn = FakeConnection(db)
    day = date(2026, 10, 17)
    written = loader.load_records(conn, [
        make_record(price_date=day),
        make_record(retailer_name="Zepto", is_available=False, price_date=day),
    ])

    assert written == 2
    assert conn.committed
    assert db["upserted"][0] == (10, 1, day, 285.0, 250.0, 12.28, True)
    # Unavailable items record no discount
    assert db["upserted"][1][-2:] == (0.0, False)


def test_unknown_catalog_product_is_registered(db, make_record):
    loader.load_records(FakeConnection(db), [make_record(product_name="Exo Dishwash Bar")])
    assert db["products"]["Exo Dishwash Bar"] == 11
    assert db["upserted"][0][0] == 11


def test_unresolvable_records_are_skipped(db, make_record):
    written = loader.load_records(FakeConnection(db), [
        make_record(product_name="Not In Catalog"),
        make_record(retailer_name="JioMart"),
    ])
    assert written == 0
    assert db["upserted"] == []
