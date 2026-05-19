"""
HTML -> Markdown converter with three-library fallback chain.

Fallback chain:
  1. html-to-markdown (primary) -- DOM-based, best for nested divs
  2. markdownify (fallback 1) -- regex-based with bs4
  3. html2text (fallback 2) -- stdlib-like, zero-dependency reliability
  4. naive regex strip (final safety net) -- always succeeds

Performance target: < 200ms for typical Google AI page (~200KB HTML).
"""

from __future__ import annotations

import re
from typing import Callable


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def convert_html_to_markdown(html: str) -> str:
    """Convert an HTML string to Markdown using the fallback chain.

    Args:
        html: Raw HTML string to convert.

    Returns:
        Markdown string (never None; empty input yields empty string).

    Raises:
        TypeError: If *html* is not a string.
    """
    if not isinstance(html, str):
        raise TypeError(f"html must be str, got {type(html).__name__}")

    if not html.strip():
        return ""

    fallback_name, result = _run_fallback_chain(html)
    return result


# ---------------------------------------------------------------------------
# Fallback chain engine
# ---------------------------------------------------------------------------

def _run_fallback_chain(html: str) -> tuple[str, str]:
    """Try each converter in order; return (lib_name, markdown_text).

    The chain is defined lazily inside the function so that function
    references are resolved at call time (after the module is fully loaded).
    """
    chain: list[tuple[str, Callable[[str], str]]] = [
        ("html-to-markdown", _convert_with_html_to_markdown),
        ("markdownify", _convert_with_markdownify),
        ("html2text", _convert_with_html2text),
    ]
    for name, convert_func in chain:
        try:
            return name, convert_func(html)
        except ImportError:
            continue
        except Exception:
            continue

    # Final safety net -- guaranteed to never fail
    return "naive", _naive_strip_tags(html)


# ---------------------------------------------------------------------------
# Library-specific converters (each returns str, raises on failure)
# ---------------------------------------------------------------------------

def _convert_with_html_to_markdown(html: str) -> str:
    """Primary: html-to-markdown (DOM traversal via BeautifulSoup)."""
    from html_to_markdown import convert as _do_convert
    result = _do_convert(html)
    # html-to-markdown v3 returns ConversionResult; extract .content
    if hasattr(result, "content"):
        return result.content
    return str(result)


def _convert_with_markdownify(html: str) -> str:
    """Fallback 1: markdownify (regex + bs4)."""
    from markdownify import markdownify as _do_convert
    return _do_convert(html)


def _convert_with_html2text(html: str) -> str:
    """Fallback 2: html2text (mature, stdlib-like)."""
    import html2text
    converter = html2text.HTML2Text()
    converter.ignore_links = False
    converter.ignore_images = True
    converter.body_width = 0  # no line wrapping
    return converter.handle(html)


# ---------------------------------------------------------------------------
# Naive regex strip -- absolute last resort
# ---------------------------------------------------------------------------

_TAG_RE = re.compile(r"<[^>]*?>", re.DOTALL)
_ENTITY_RE = re.compile(r"&[#a-zA-Z0-9]+;")
_MULTI_NEWLINE_RE = re.compile(r"\n{3,}")
_BR_TAG_RE = re.compile(r"<br\s*/?>", re.IGNORECASE)
_P_TAG_RE = re.compile(r"</?p[^>]*?>", re.IGNORECASE)

_ENTITY_MAP: dict[str, str] = {
    "&amp;": "&",
    "&lt;": "<",
    "&gt;": ">",
    "&quot;": '"',
    "&#39;": "'",
    "&apos;": "'",
    "&nbsp;": " ",
    "&#160;": " ",
}


def _naive_strip_tags(html: str) -> str:
    """Remove all HTML tags and decode common entities using naive regex.

    This is the absolute last resort -- used only when all three
    conversion libraries are unavailable.
    """
    text = html
    # Replace <br> and <p> tags with newlines before stripping
    text = _BR_TAG_RE.sub("\n", text)
    text = _P_TAG_RE.sub("\n", text)
    # Strip all remaining tags
    text = _TAG_RE.sub("", text)
    # Decode common HTML entities
    for entity, char in _ENTITY_MAP.items():
        text = text.replace(entity, char)
    # Decode numeric entities like &#8226;
    text = _ENTITY_RE.sub(_decode_entity, text)
    # Collapse whitespace
    text = _MULTI_NEWLINE_RE.sub("\n\n", text)
    text = "\n".join(line.strip() for line in text.splitlines())
    return text.strip()


def _decode_entity(match: re.Match) -> str:
    """Decode a single HTML entity reference."""
    entity = match.group(0)
    if entity.startswith("&#x"):
        try:
            return chr(int(entity[3:-1], 16))
        except (ValueError, OverflowError):
            return entity
    if entity.startswith("&#"):
        try:
            return chr(int(entity[2:-1]))
        except (ValueError, OverflowError):
            return entity
    # Named entity not in our map -- leave as-is (unlikely)
    return entity
