"""Static checks that keep the SQL layer consistent (no database required)."""

import re

from conftest import PROJECT_ROOT

VIEWS_FILE = PROJECT_ROOT / "database" / "views" / "analytical_views.sql"
QUERIES_DIR = PROJECT_ROOT / "sql_queries"
SCHEMA_DIR = PROJECT_ROOT / "database" / "schema"

VIEW_NAME = re.compile(r"CREATE OR REPLACE VIEW (\w+)", re.IGNORECASE)


def test_twenty_views_defined():
    views = VIEW_NAME.findall(VIEWS_FILE.read_text(encoding="utf-8"))
    assert len(views) == 20
    assert len(set(views)) == 20


def test_every_view_has_a_standalone_query_file():
    views = set(VIEW_NAME.findall(VIEWS_FILE.read_text(encoding="utf-8")))
    query_views = set()
    for path in QUERIES_DIR.glob("*.sql"):
        query_views.update(VIEW_NAME.findall(path.read_text(encoding="utf-8")))
    assert views == query_views


def test_query_files_are_numbered_and_documented():
    files = sorted(QUERIES_DIR.glob("*.sql"))
    assert [int(f.name[:2]) for f in files] == list(range(1, 21))
    for f in files:
        assert "Business Problem:" in f.read_text(encoding="utf-8"), f.name


def test_schema_scripts_are_idempotent():
    ddl = (SCHEMA_DIR / "01_create_tables.sql").read_text(encoding="utf-8")
    for statement in re.findall(r"CREATE (?:TABLE|INDEX)[^;]*", ddl):
        assert "IF NOT EXISTS" in statement, statement.splitlines()[0]
    seed = (SCHEMA_DIR / "02_seed_dimensions.sql").read_text(encoding="utf-8")
    assert seed.count("INSERT INTO") == seed.count("ON CONFLICT")
