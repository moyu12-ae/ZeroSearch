"""
DOM 清洗模块 (T3.1.3)
用 BeautifulSoup4 移除 HTML 中无关标签和属性，保留有意义内容。
"""

from __future__ import annotations

import re
from typing import List

from bs4 import BeautifulSoup, Tag

# ---------------------------------------------------------------------------
# 清洗规则常量
# 来源: .anws/v1/04_SYSTEM_DESIGN/content-extractor.md §6.4
# ---------------------------------------------------------------------------

REMOVE_TAGS: List[str] = [
    "script",
    "style",
    "nav",
    "footer",
    "header",
    "aside",
    "noscript",
    "iframe",
    "svg",
    "form",
    "input",
    "button",
]

REMOVE_ATTRIBUTES_PATTERNS: List[str] = [
    "class",
    "style",
    "id",
    r"^data-",           # 所有 data-* 属性
    "jsname",
    "jsaction",
    "jscontroller",
    "onclick",
    "onload",
    r"^aria-",           # ARIA 无障碍标记
]

REMOVE_SELECTORS: List[str] = [
    '[role="navigation"]',
    '[role="banner"]',
    '[role="contentinfo"]',
    '[aria-label*="advertisement"]',
    ".ad-container",
    ".google-ad",
    "#taw",
    "#top_nav",
    "#fbar",
    "#bfoot",
]

# Extra attribute that the acceptance criteria explicitly call out for removal
# beyond the pattern-based ones above (data-ved, jsname, jsaction are already
# covered by ^data- and the explicit entries).
EXTRA_ATTRIBUTES: List[str] = [
    "data-ved",
    "jsaction",
    "onload",
    "jsname",
    "jscontroller",
    "onclick",
    "style",
    "class",
    "id",
]


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _should_remove_attribute(attr_name: str) -> bool:
    """Return True if *attr_name* matches any REMOVE_ATTRIBUTES_PATTERNS."""
    for pattern in REMOVE_ATTRIBUTES_PATTERNS:
        if pattern.startswith("^"):
            if re.match(pattern, attr_name):
                return True
        else:
            if attr_name == pattern:
                return True
    return False


def _clean_attributes(tag: Tag) -> None:
    """Strip unwanted attributes from a BeautifulSoup Tag in-place."""
    attrs_to_remove = [a for a in tag.attrs if _should_remove_attribute(a)]
    for attr in attrs_to_remove:
        del tag[attr]


def _remove_by_selectors(soup: BeautifulSoup) -> None:
    """Remove elements matching CSS selectors in REMOVE_SELECTORS."""
    for sel in REMOVE_SELECTORS:
        for element in soup.select(sel):
            element.decompose()


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def clean_html(raw_html: str) -> str:
    """Clean incoming HTML by removing non-content tags and attributes.

    Parameters
    ----------
    raw_html : str
        Raw HTML string to clean.

    Returns
    -------
    str
        Cleaned HTML string.  Returns an empty string when the input is
        empty or whitespace-only.

    Raises
    ------
    ValueError
        When *raw_html* is empty or whitespace-only.
    """
    # Edge-case: empty input
    if not raw_html or not raw_html.strip():
        return ""

    soup = BeautifulSoup(raw_html, "html.parser")

    # 1. Remove elements matched by CSS selectors (ads, nav roles, etc.)
    _remove_by_selectors(soup)

    # 2. Decompose tags listed in REMOVE_TAGS (script, style, nav, footer, …)
    for tag_name in REMOVE_TAGS:
        for tag in soup.find_all(tag_name):
            tag.decompose()

    # 3. Strip unwanted attributes from remaining tags
    for tag in soup.find_all(True):
        _clean_attributes(tag)

    # Return the string representation of the cleaned body content.
    # When <body> exists we return its inner HTML; otherwise return the soup
    # as a string.
    body = soup.body
    if body is not None:
        return "".join(str(child) for child in body.contents)
    return str(soup)
