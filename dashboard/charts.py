"""
Chart styling for the dashboard.

Retailer colors are the first four slots of a validated categorical palette
(checked for colorblind separation in both light and dark themes), assigned
to retailers in a fixed order so a filter never repaints the survivors.
Brand colors were not used: Blinkit/BigBasket yellow-greens fail contrast.
"""

import plotly.graph_objects as go
import streamlit as st

from dashboard.analytics import RETAILERS

_RETAILER_COLORS = {
    "light": ["#2a78d6", "#eb6834", "#1baf7a", "#eda100"],
    "dark": ["#3987e5", "#d95926", "#199e70", "#c98500"],
}
_CATEGORICAL = {  # full 8-slot sequence, for non-retailer series (e.g. categories)
    "light": ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300", "#6250d6", "#e34948"],
    "dark": ["#3987e5", "#d95926", "#199e70", "#c98500", "#d55181", "#008300", "#9085e9", "#e66767"],
}
MAX_SERIES = 8
_DIVERGING = {  # blue (cheaper / price fell) ↔ gray ↔ red (pricier / price rose)
    "light": ["#2a78d6", "#f0efec", "#e34948"],
    "dark": ["#3987e5", "#383835", "#e66767"],
}
SEQUENTIAL_BLUE = ["#cde2fb", "#86b6ef", "#3987e5", "#1c5cab", "#0d366b"]
SINGLE_SERIES = {"light": "#2a78d6", "dark": "#3987e5"}


def _mode():
    try:
        return "dark" if st.context.theme.type == "dark" else "light"
    except Exception:
        return "light"


def retailer_colors():
    return dict(zip(RETAILERS, _RETAILER_COLORS[_mode()]))


def categorical_colors(names):
    """Fixed-order colours for up to MAX_SERIES non-retailer series."""
    return dict(zip(names, _CATEGORICAL[_mode()]))


def single_color():
    return SINGLE_SERIES[_mode()]


def diverging_scale():
    low, mid, high = _DIVERGING[_mode()]
    return [[0.0, low], [0.5, mid], [1.0, high]]


def style(fig, height=380, legend=True):
    """Recessive axes/grid, compact margins, legend above the plot."""
    fig.update_layout(
        height=height,
        margin=dict(l=8, r=8, t=36 if legend else 8, b=8),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0, title=None),
        showlegend=legend,
        hoverlabel=dict(namelength=-1),
        bargap=0.35,
    )
    fig.update_xaxes(showgrid=False, title_font_size=12)
    fig.update_yaxes(gridwidth=1, zeroline=False, title_font_size=12)
    fig.update_traces(selector=dict(type="bar"), marker_cornerradius=4)
    fig.update_traces(selector=dict(type="scatter"), line_width=2)
    return fig


def show(fig, **kwargs):
    st.plotly_chart(style(fig, **kwargs), width="stretch",
                    config={"displaylogo": False})


__all__ = ["go", "retailer_colors", "categorical_colors", "MAX_SERIES", "single_color", "diverging_scale",
           "SEQUENTIAL_BLUE", "style", "show"]
