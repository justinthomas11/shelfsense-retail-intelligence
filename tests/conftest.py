import re
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from scrapers.base_scraper import ScrapedPrice  # noqa: E402

SELECTOR_PATTERN = re.compile(r"^(?P<tag>[a-z0-9]+)?(?P<rest>.*)$")


def element_for(selector, inner=""):
    """
    Build a minimal HTML element that matches the first alternative of a
    CSS selector, e.g. "div.a.b[data-x='y']" → <div class="a b" data-x="y">.
    Lets tests exercise each scraper's real SELECTORS without live pages.
    """
    first = selector.split(",")[0].strip()
    m = SELECTOR_PATTERN.match(first)
    tag = m.group("tag") or "div"
    rest = m.group("rest")

    classes = re.findall(r"\.([\w-]+)", re.sub(r"\[.*?\]", "", rest))
    attrs = {}
    for name, op, value in re.findall(r"\[([\w-]+)(?:([*^$]?=)'([^']*)')?\]", rest):
        if name == "class" and op:
            classes.append(value)
        else:
            attrs[name] = value
    if classes:
        attrs["class"] = " ".join(classes)
    attr_html = "".join(f' {k}="{v}"' for k, v in attrs.items())
    return f"<{tag}{attr_html}>{inner}</{tag}>"


@pytest.fixture
def make_record():
    def _make(**overrides):
        fields = {
            "retailer_name": "BigBasket",
            "product_name": "Amul Butter",
            "selling_price": 250.0,
            "mrp": 285.0,
        }
        fields.update(overrides)
        return ScrapedPrice(**fields)
    return _make
