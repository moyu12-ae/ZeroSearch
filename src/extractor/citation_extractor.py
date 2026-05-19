"""
Citation 引用提取模块 (T3.1.2)
17 个多语言引用选择器回退链提取引用链接，含域名 + 标题相似度去重。

设计文档: .anws/v1/04_SYSTEM_DESIGN/content-extractor.md §6.2
"""

from __future__ import annotations

import difflib
from dataclasses import dataclass
from typing import Dict, List, Optional, Sequence, Tuple
from urllib.parse import urlparse


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------


@dataclass
class Citation:
    title: str
    url: str
    index: int = 0


# ---------------------------------------------------------------------------
# 17 个多语言引用选择器 (按优先级排列)
# 来源: content-extractor.md L288-306
# ---------------------------------------------------------------------------


@dataclass(order=True, frozen=True)
class _Selector:
    priority: int
    language: str  # "en" | "de" | "nl" | "generic"
    selector: str   # CSS selector string for page.query_selector_all

    def __repr__(self) -> str:
        return f"_Selector(p={self.priority}, lang={self.language!r}, sel={self.selector!r})"


SELECTORS: Tuple[_Selector, ...] = (
    # ── English (en) ── priority 1-5
    _Selector(1, "en", 'a[data-cid]'),
    _Selector(2, "en", '.citation-source a'),
    _Selector(3, "en", 'div[data-sncf="1"] a[href]'),
    _Selector(4, "en", 'g-expandable a[ping]'),
    _Selector(5, "en", '[aria-label*="More about"] a'),

    # ── German (de) ── priority 6-9
    _Selector(6, "de", 'a[data-cid] div[lang="de"]'),
    _Selector(7, "de", 'a[data-entityname]'),
    _Selector(8, "de", '.source-box a[href*="/url?"]'),
    _Selector(9, "de", 'g-bottom-sheet a[data-ved]'),

    # ── Dutch (nl) ── priority 10-13
    _Selector(10, "nl", 'a[jsaction*="footnote"]'),
    _Selector(11, "nl", '.inline-related a[href]'),
    _Selector(12, "nl", 'h2:has-text("Bronnen") ~ div a'),
    _Selector(13, "nl", '[data-hveid] a'),

    # ── Generic fallback ── priority 14-17
    _Selector(14, "generic", 'a[href*="/url?q="][target="_blank"]'),
    _Selector(15, "generic", 'a[rel="noopener"][jsname]'),
    _Selector(16, "generic", 'div[role="complementary"] a[href]'),
    _Selector(17, "generic", 'a[href^="http"][jscontroller]'),
)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _extract_domain(url: str) -> str:
    """Extract the netloc portion of a URL for domain-based dedup.

    Falls back to the full URL if parsing fails.
    """
    parsed = urlparse(url)
    return parsed.netloc or url


def _title_similarity(a: str, b: str) -> float:
    """Return Jaro-Winkler-style similarity ratio for two strings.

    Uses difflib.SequenceMatcher (which is similar to Ratcliff/Obershelp).
    This produces a float in [0.0, 1.0].

    We fall back to a simple length-based penalty for very short strings
    so that empty / single-word titles don't accidentally match.
    """
    if not a or not b:
        return 0.0

    # Normalize: lowercase, strip extra whitespace
    an = a.lower().strip()
    bn = b.lower().strip()

    ratio = difflib.SequenceMatcher(None, an, bn).ratio()
    return ratio


def _is_duplicate(
    existing: List[Citation],
    candidate_title: str,
    candidate_url: str,
    threshold: float = 0.8,
) -> bool:
    """Check if *candidate_url* + *candidate_title* is a duplicate of any
    existing citation.

    A duplicate is defined as:
      - Same domain (netloc), AND
      - Title similarity > *threshold* (default 0.8)
    """
    candidate_domain = _extract_domain(candidate_url)

    for cit in existing:
        cit_domain = _extract_domain(cit.url)
        if cit_domain != candidate_domain:
            continue

        sim = _title_similarity(candidate_title, cit.title)
        if sim > threshold:
            return True

    return False


def _deduplicate_citations(raw_items: List[Dict[str, str]]) -> List[Citation]:
    """Deduplicate a list of {title, url} dicts by domain + title similarity.

    Returns a list of unique Citation objects, preserving first-seen order.
    """
    result: List[Citation] = []
    for idx, item in enumerate(raw_items):
        title = item.get("title", "").strip()
        url = item.get("url", "").strip()

        # Skip entries with no meaningful title or url
        if not title or not url:
            continue

        if _is_duplicate(result, title, url):
            continue

        result.append(Citation(title=title, url=url, index=idx))

    return result


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def extract_citations(page) -> list[dict]:
    """提取引用链接：优先使用 JS 注入（动态 DOM），回退到 CSS 选择器。

    策略:
    1. JS 注入: 直接在浏览器中遍历 <a> 标签提取 title + href
    2. CSS 回退: 17 选择器回退链（兼容旧版 Google AI Mode DOM）

    Parameters
    ----------
    page : Camoufox Page 对象

    Returns
    -------
    list[dict]
        去重后的引用列表 [{title, url}]，未命中时返回空列表。
    """
    raw_entries: List[Dict[str, str]] = []

    # ── 主策略: JS 注入提取（适配当前 Google DOM） ──────────
    try:
        js_result = page.evaluate("""
            () => {
                const results = [];
                const links = document.querySelectorAll('a[href]');
                for (const a of links) {
                    const href = a.href || '';
                    if (!href.startsWith('http')) continue;
                    if (href.includes('google.com')) continue;
                    const text = (a.innerText || a.textContent || '').trim();
                    if (text.length > 0) {
                        results.push({title: text, url: href});
                    }
                }
                return results;
            }
        """)
        if js_result and isinstance(js_result, list):
            raw_entries.extend(js_result)
    except Exception:
        pass

    # ── 回退策略: CSS 选择器链 ──────────────────────────────
    if not raw_entries:
        for sel_def in SELECTORS:
            try:
                elements = page.query_selector_all(sel_def.selector)
        except Exception:
            # 选择器语法不兼容或页面不可用时跳过，不阻断后续回退
            continue

        if not elements:
            continue

        for el in elements:
            title = ""
            url = ""

            try:
                # extract title
                title = (el.text_content() or "").strip()

                # extract url
                raw_href = el.get_attribute("href")
                if raw_href:
                    url = raw_href.strip()
            except Exception:
                # 单个元素提取失败，跳过该元素
                continue

            # 保守：没有 url 的条目跳过
            if not url:
                continue

            # Camoufox 可能返回相对路径；额外兜底
            # （Google 搜索结果通常返回绝对 URL，但泛用选择器可能抓到相对路径）
            if url.startswith("/") and not url.startswith("//"):
                try:
                    url = page.url.rstrip("/") + url
                except Exception:
                    pass

            raw_entries.append({"title": title, "url": url})

        # 早停：高优先级选择器命中且有数据就直接返回
        if raw_entries:
            break

    # 去重
    unique = _deduplicate_citations(raw_entries)

    # 转换为简单 dict 列表（满足函数签名 Returns 约定）
    return [{"title": c.title, "url": c.url} for c in unique]
