"""
ShelfSense — Streamlit Dashboard
=================================
Usage:
    streamlit run dashboard/app.py
"""

import sys
from pathlib import Path

import streamlit as st

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from dashboard.data import require_connection, sidebar_filters  # noqa: E402

st.set_page_config(page_title="ShelfSense", page_icon="🛒", layout="wide")

# Not named "pages/": that folder name triggers Streamlit's legacy auto-discovery
PAGES = Path(__file__).parent / "views"
nav = st.navigation([
    st.Page(PAGES / "executive.py", title="Executive", icon=":material/insights:", default=True),
    st.Page(PAGES / "operational.py", title="Operational", icon=":material/storefront:"),
    st.Page(PAGES / "trends.py", title="Trends", icon=":material/trending_up:"),
])

st.sidebar.title("🛒 ShelfSense")
st.sidebar.caption("Competitive retail price intelligence")
require_connection()
st.session_state["filters"] = sidebar_filters()
nav.run()
