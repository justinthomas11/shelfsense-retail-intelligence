"""
Data access for the dashboard: one cached SQLAlchemy engine and cached
queries against the analytical views. Every page reads through here.
"""

import sys
from pathlib import Path

import pandas as pd
import streamlit as st
from sqlalchemy import create_engine, text

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from dashboard.analytics import RETAILERS, apply_filters, coerce_decimals  # noqa: E402

CACHE_TTL = 600  # seconds — the pipeline only writes once a day


@st.cache_resource(show_spinner=False)
def get_engine():
    from config.db_config import CONNECTION_STRING
    # Pin the driver: SQLAlchemy 2.1+ defaults postgresql:// to psycopg 3
    url = CONNECTION_STRING.replace("postgresql://", "postgresql+psycopg2://", 1)
    return create_engine(url, pool_pre_ping=True)


@st.cache_data(ttl=CACHE_TTL, show_spinner=False)
def query(sql, params=None):
    with get_engine().connect() as conn:
        return coerce_decimals(pd.read_sql(text(sql), conn, params=params))


def view(name):
    """SELECT * from an analytical view (name must be a vw_* identifier)."""
    if not name.startswith("vw_") or not name.replace("_", "").isalnum():
        raise ValueError(f"not an analytical view: {name}")
    return query(f"SELECT * FROM {name}")


def require_connection():
    """Stop the page with setup instructions if the warehouse is unreachable."""
    try:
        query("SELECT 1 FROM fact_price_history LIMIT 1")
    except Exception as exc:
        st.error("Can't reach the ShelfSense database.")
        st.markdown(
            "Start PostgreSQL and load data first:\n\n"
            "```bash\ndocker compose up -d\npython scripts/setup_database.py --with-data\n```\n\n"
            "Connection settings live in `config/db_config.py` / `.env`."
        )
        with st.expander("Error details"):
            st.code(str(exc))
        st.stop()


@st.cache_data(ttl=CACHE_TTL, show_spinner=False)
def categories():
    return query("SELECT category_name FROM dim_category ORDER BY category_name")["category_name"].tolist()


def latest_date():
    return query("SELECT MAX(price_date) AS d FROM fact_price_history")["d"].iloc[0]


def sidebar_filters():
    """Shared category/retailer filters; selections persist across pages."""
    st.sidebar.header("Filters")
    cats = st.sidebar.multiselect("Category", categories(), key="filter_categories",
                                  placeholder="All categories")
    rets = st.sidebar.multiselect("Retailer", RETAILERS, key="filter_retailers",
                                  placeholder="All retailers")
    st.sidebar.caption(f"Data through **{latest_date():%d %b %Y}**")
    return cats, rets


def filtered(name, cats, rets):
    return apply_filters(view(name), cats, rets)
