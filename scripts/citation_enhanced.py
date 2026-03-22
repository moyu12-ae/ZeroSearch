"""
Citation Extractor - Enhanced Version with Multi-language Support
Extracts citations from Google AI Overview

Phase 6 Enhanced Features:
- Multi-language citation button selectors (EN/DE/NL/FR/ES/IT)
- Sidebar fallback extraction
- Show more automatic expansion
- Enhanced HTML to Markdown conversion
"""

import re
import json
from dataclasses import dataclass
from typing import List, Optional, Set, Callable
from bs4 import BeautifulSoup, Tag
import logging

logger = logging.getLogger(__name__)


CITATION_SELECTORS = {
    "en": ["Sources", "Related", "Cited by", "Links"],
    "de": ["Quellen", "Verwandt", "Zitiert von", "Links"],
    "nl": ["Bronnen", "Gerelateerd", "Geciteerd door", "Links"],
    "fr": ["Sources", "Liés", "Cité par", "Liens"],
    "es": ["Fuentes", "Relacionado", "Citado por", "Enlaces"],
    "it": ["Fonti", "Collegato", "Citato da", "Link"],
}

SHOW_MORE_BUTTONS = {
    "en": ["show more", "more results", "more links"],
    "de": ["mehr anzeigen", "mehr ergebnisse", "mehr links"],
    "nl": ["meer weergeven", "meer resultaten", "meer links"],
    "fr": ["afficher plus", "plus de résultats", "plus de liens"],
    "es": ["mostrar más", "más resultados", "más enlaces"],
    "it": ["mostra altro", "altri risultati", "altri link"],
}

SIDEBAR_SELECTORS = [
    "aside",
    '[role="complementary"]',
    ".related",
    "#resources",
    '[aria-label*="Sources"]',
    '[aria-label*="Links"]',
]


@dataclass
class ExtractedCitation:
    """Enhanced citation with context extraction"""
    index: int
    url: str
    title: str
    context: str
    parent_context: Optional[str] = None
    is_citation_marker: bool = False


class CitationExtractorEnhanced:
    """
    Enhanced citation extractor with multi-language support.

    Features:
    - Multi-language citation selectors
    - Sidebar fallback extraction
    - Show more automatic expansion
    - Enhanced link filtering
    """

    CITATION_MARKERS = [
        r'\[(\d+)\]',
        r'citation(\d+)',
        r'cite(\d+)',
    ]

    EXCLUDE_PATTERNS = [
        r'google\.com',
        r'accounts\.google\.com',
        r'support\.google\.com',
        r'maps\.google\.com',
        r'webcache\.googleusercontent\.com',
        r'translate\.google\.com',
        r'://localhost',
        r'://127\.0\.0\.1',
        r'gstatic\.com',
    ]

    def __init__(self, max_citations: int = 20):
        self.max_citations = max_citations
        self._seen_urls: Set[str] = set()
        self._citation_map = {}

    def reset(self):
        """Reset internal state for new extraction"""
        self._seen_urls.clear()
        self._citation_map.clear()

    def is_valid_url(self, url: str) -> bool:
        """Check if URL is valid for citation"""
        if not url or not isinstance(url, str):
            return False

        url_lower = url.lower().strip()

        if url_lower.startswith(('javascript:', 'mailto:', 'tel:', '#')):
            return False

        for pattern in self.EXCLUDE_PATTERNS:
            if re.search(pattern, url_lower):
                return False

        return True

    def normalize_url(self, url: str) -> str:
        """Normalize URL for deduplication"""
        url = url.strip()
        url = re.sub(r'#.*$', '', url)
        url = re.sub(r'\?utm_[^?]+', '', url)
        return url

    def _detect_language(self, html: str) -> str:
        """Detect language from HTML content"""
        for lang, keywords in CITATION_SELECTORS.items():
            for keyword in keywords:
                if keyword.lower() in html.lower():
                    return lang
        return "en"

    def _expand_show_more(self, browser, max_wait: int = 3) -> None:
        """Click show more buttons to expand content"""
        for lang, buttons in SHOW_MORE_BUTTONS.items():
            for button_text in buttons:
                click_script = f"""
                (function() {{
                    var buttons = Array.from(document.querySelectorAll('button, a'));
                    for (var btn of buttons) {{
                        if (btn.textContent.toLowerCase().includes('{button_text.toLowerCase()}')) {{
                            btn.click();
                            return true;
                        }}
                    }}
                    return false;
                }})()
                """
                try:
                    result = browser.eval_js(click_script)
                    if result:
                        logger.info(f"Clicked '{button_text}' button")
                        break
                except Exception:
                    pass

    def _extract_sidebar_fallback(self, html: str) -> List[ExtractedCitation]:
        """Fallback extraction from sidebar/sources section"""
        citations = []

        try:
            soup = BeautifulSoup(html, 'html.parser')

            for selector in SIDEBAR_SELECTORS:
                sidebar = soup.select_one(selector)
                if sidebar:
                    logger.info(f"Found sidebar with selector: {selector}")
                    links = sidebar.find_all('a', href=True)
                    for i, link in enumerate(links[:self.max_citations], 1):
                        url = link.get('href', '')
                        if not self.is_valid_url(url):
                            continue

                        normalized = self.normalize_url(url)
                        if normalized in self._seen_urls:
                            continue
                        self._seen_urls.add(normalized)

                        title = link.get_text(strip=True)[:100]
                        context = link.get('aria-label', '') or title

                        citations.append(ExtractedCitation(
                            index=i,
                            url=normalized,
                            title=title,
                            context=context,
                            is_citation_marker=False,
                        ))

                    if citations:
                        break

        except Exception as e:
            logger.warning(f"Sidebar extraction failed: {e}")

        return citations

    def extract_from_html(self, html: str) -> List[ExtractedCitation]:
        """Extract citations from HTML with multi-language support"""
        self.reset()
        citations = []

        if not html:
            return citations

        try:
            soup = BeautifulSoup(html, 'html.parser')

            lang = self._detect_language(html)
            logger.info(f"Detected language: {lang}")

            links = soup.find_all('a', href=True)

            for link in links:
                url = link.get('href', '')
                if not self.is_valid_url(url):
                    continue

                normalized = self.normalize_url(url)
                if normalized in self._seen_urls:
                    continue

                self._seen_urls.add(normalized)

                title = self._extract_title(link)
                context = self._extract_context(link)

                citations.append(ExtractedCitation(
                    index=len(citations) + 1,
                    url=normalized,
                    title=title,
                    context=context,
                    is_citation_marker=False,
                ))

                if len(citations) >= self.max_citations:
                    break

            if not citations:
                citations = self._extract_sidebar_fallback(html)

        except Exception as e:
            logger.error(f"Citation extraction failed: {e}")

        return citations[:self.max_citations]

    def _extract_title(self, link: Tag) -> str:
        """Extract title from link"""
        title = link.get('title', '')
        if title:
            return title.strip()

        img = link.find('img')
        if img:
            alt = img.get('alt', '')
            if alt:
                return alt.strip()[:100]

        text = link.get_text(strip=True)
        if text:
            return text[:100].strip() if len(text) > 100 else text.strip()

        return link.get('href', '')[:50]

    def _extract_context(self, link: Tag) -> str:
        """Extract context from link"""
        aria_label = link.get('aria-label', '')
        if aria_label:
            return aria_label.strip()[:200]

        title = link.get('title', '')
        if title:
            return title.strip()[:200]

        text = link.get_text(strip=True)
        if text:
            return text[:200].strip() if len(text) > 200 else text.strip()

        return self._extract_parent_context(link)

    def _extract_parent_context(self, link: Tag) -> Optional[str]:
        """Extract context from parent elements"""
        for parent in [link.parent, link.parent.parent if link.parent else None]:
            if not isinstance(parent, Tag):
                continue
            parent_text = parent.get_text(strip=True)
            if parent_text and len(parent_text) > 10:
                return parent_text[:150].strip()
        return None

    def extract_from_js(self, js_evaluator: Callable) -> List[ExtractedCitation]:
        """Extract citations using JavaScript evaluation"""
        self.reset()
        citations = []

        js_code = """
        (function() {
            var links = Array.from(document.querySelectorAll('a[href^="http"]'))
                .filter(function(a) {
                    return !a.href.includes('google.com') &&
                           !a.href.includes('gstatic.com') &&
                           a.href.length > 10;
                })
                .slice(0, 20)
                .map(function(a, i) {
                    return {
                        href: a.href.split('#')[0].split('?')[0],
                        text: (a.textContent || '').trim().substring(0, 100) || ('Link ' + (i + 1)),
                        title: a.title || a.getAttribute('aria-label') || ''
                    };
                });
            return JSON.stringify(links);
        })()
        """

        try:
            result = js_evaluator(js_code)
            if not result:
                logger.warning("JavaScript evaluation returned empty result")
                return citations

            links_data = json.loads(result)
            if not isinstance(links_data, list):
                return citations

            for i, link in enumerate(links_data, 1):
                url = link.get('href', '')
                if not self.is_valid_url(url):
                    continue

                normalized = self.normalize_url(url)
                if normalized in self._seen_urls:
                    continue

                self._seen_urls.add(normalized)

                title = link.get('title', '') or link.get('text', '')
                context = link.get('text', '') or f"Source {i}"

                citations.append(ExtractedCitation(
                    index=i,
                    url=normalized,
                    title=title[:100] if title else f"Source {i}",
                    context=context[:200] if context else f"Source {i}",
                    is_citation_marker=False,
                ))

            logger.info(f"Extracted {len(citations)} citations via JavaScript")

        except Exception as e:
            logger.error(f"JavaScript extraction failed: {e}")

        return citations[:self.max_citations]

    def to_markdown_list(self, citations: List[ExtractedCitation]) -> str:
        """Convert citations to Markdown list format"""
        if not citations:
            return ""

        lines = ["**Sources:**\n"]

        for cite in citations:
            context = cite.context or cite.title or f"Source {cite.index}"
            lines.append(f"- [{context}]({cite.url})")

        return "\n".join(lines)


def main():
    """Demo usage"""
    sample_html = """
    <div class="ai-overview">
        <p>Python is a <a href="https://python.org" title="Python">Python</a></p>
        <aside class="sources">
            <a href="https://docs.python.org">Python Documentation</a>
            <a href="https://realpython.com">Real Python</a>
        </aside>
    </div>
    """

    extractor = CitationExtractorEnhanced()
    citations = extractor.extract_from_html(sample_html)

    print(f"Found {len(citations)} citations")
    for cite in citations:
        print(f"  [{cite.index}] {cite.title}: {cite.url}")


if __name__ == "__main__":
    main()
