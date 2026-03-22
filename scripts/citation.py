"""
Citation Extractor - Extract citations from Google AI Overview
Converts citations to Markdown format [context](url)

Supports two extraction modes:
1. HTML parsing - Fast, good for static content
2. JavaScript evaluation - Required for dynamically rendered content (AI Overview)
"""

import re
import json
from dataclasses import dataclass
from typing import List, Optional, Set, Tuple, Callable
from bs4 import BeautifulSoup, NavigableString, Tag
import logging

logger = logging.getLogger(__name__)


@dataclass
class ExtractedCitation:
    """Enhanced citation with context extraction"""
    index: int
    url: str
    title: str
    context: str
    parent_context: Optional[str] = None
    is_citation_marker: bool = False


class CitationExtractor:
    """
    Extracts citations from Google AI Overview HTML

    Features:
    - Extracts citations from button markers [1], [2], etc.
    - Associates citations with surrounding context
    - Deduplicates URLs
    - Converts to Markdown format [context](url)
    """

    CITATION_MARKERS = [
        r'\[(\d+)\]',  # [1], [2], etc.
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
    ]

    def __init__(self, max_citations: int = 20):
        self.max_citations = max_citations
        self._seen_urls: Set[str] = set()
        self._citation_map: dict[int, str] = {}

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

    def extract_from_html(self, html: str) -> List[ExtractedCitation]:
        """
        Extract citations from AI Overview HTML

        Args:
            html: HTML content of AI Overview

        Returns:
            List of ExtractedCitation objects
        """
        self.reset()
        citations: List[ExtractedCitation] = []

        if not html:
            return citations

        try:
            soup = BeautifulSoup(html, 'html.parser')

            citation_map = self._build_citation_map(soup)

            links = soup.find_all('a', href=True)

            for link in links:
                url = link.get('href', '')

                if not self.is_valid_url(url):
                    continue

                normalized_url = self.normalize_url(url)
                if normalized_url in self._seen_urls:
                    continue

                self._seen_urls.add(normalized_url)

                title = self._extract_link_title(link)
                context = self._extract_context(link)
                parent_context = self._extract_parent_context(link)

                index = len(citations) + 1

                citations.append(ExtractedCitation(
                    index=index,
                    url=normalized_url,
                    title=title,
                    context=context,
                    parent_context=parent_context,
                    is_citation_marker=False,
                ))

                if len(citations) >= self.max_citations:
                    break

            if not citations:
                citations = self._fallback_extract(soup)

        except ImportError:
            logger.warning("BeautifulSoup not available, using regex fallback")
            citations = self._regex_extract(html)
        except Exception as e:
            logger.error(f"Citation extraction failed: {e}")

        return citations[:self.max_citations]

    def _build_citation_map(self, soup: BeautifulSoup) -> dict:
        """Build map of citation markers to URLs"""
        citation_map = {}

        for pattern in self.CITATION_MARKERS:
            markers = soup.find_all(string=re.compile(pattern, re.IGNORECASE))
            for marker in markers:
                match = re.search(pattern, str(marker), re.IGNORECASE)
                if match:
                    num = int(match.group(1))
                    parent = marker.parent
                    if parent and parent.name == 'a':
                        href = parent.get('href', '')
                        if self.is_valid_url(href):
                            citation_map[num] = href

        self._citation_map = citation_map
        return citation_map

    def _extract_link_title(self, link: Tag) -> str:
        """Extract title from link element"""
        title = link.get('title', '')
        if title:
            return title.strip()

        img = link.find('img')
        if img:
            alt = img.get('alt', '')
            if alt:
                return alt.strip()

        text = link.get_text(strip=True)
        if text:
            return text[:100].strip() if len(text) > 100 else text.strip()

        return link.get('href', '')[:50]

    def _extract_context(self, link: Tag) -> str:
        """Extract context around the link"""
        aria_label = link.get('aria-label', '')
        if aria_label:
            return aria_label.strip()

        title = link.get('title', '')
        if title:
            return title.strip()

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

    def _fallback_extract(self, soup: BeautifulSoup) -> List[ExtractedCitation]:
        """Fallback extraction when link parsing fails"""
        citations = []
        text = soup.get_text()

        url_pattern = r'https?://[^\s<>"\'\)\]]+'
        urls = re.findall(url_pattern, text)

        for i, url in enumerate(set(urls), 1):
            if self.is_valid_url(url):
                normalized = self.normalize_url(url)
                if normalized not in self._seen_urls:
                    self._seen_urls.add(normalized)
                    citations.append(ExtractedCitation(
                        index=i,
                        url=normalized,
                        title=url.split('/')[-1][:50],
                        context=f"Source {i}",
                    ))

        return citations

    def _regex_extract(self, html: str) -> List[ExtractedCitation]:
        """Regex-based extraction fallback"""
        citations = []

        url_pattern = r'href="(https?://[^"]+)"'
        matches = re.findall(url_pattern, html)

        for i, url in enumerate(matches[:self.max_citations], 1):
            if self.is_valid_url(url):
                normalized = self.normalize_url(url)
                if normalized not in self._seen_urls:
                    self._seen_urls.add(normalized)
                    citations.append(ExtractedCitation(
                        index=i,
                        url=normalized,
                        title=url.split('/')[-1][:50],
                        context=f"Source {i}",
                    ))

        return citations

    def extract_from_js(self, js_evaluator: Callable[[str], str]) -> List[ExtractedCitation]:
        """
        Extract citations using JavaScript evaluation.
        This is required for dynamically rendered content like Google AI Overview.

        Args:
            js_evaluator: A callable that takes JavaScript code and returns the result.
                         For agent-browser, use a callable that executes 'eval <js_code>' command.

        Returns:
            List of ExtractedCitation objects
        """
        self.reset()
        citations: List[ExtractedCitation] = []

        js_code = (
            "(function() {"
            "  var links = Array.from(document.querySelectorAll('a[href^=\"http\"]'))"
            "    .filter(function(a) { return !a.href.includes('google.com') && !a.href.includes('gstatic.com'); })"
            "    .slice(0, " + str(self.max_citations) + ")"
            "    .map(function(a, i) {"
            "      return {"
            "        href: a.href.split('#')[0].split('?')[0],"
            "        text: (a.textContent || '').trim().substring(0, 100) || ('Link ' + (i + 1)),"
            "        title: a.title || a.getAttribute('aria-label') || ''"
            "      };"
            "    });"
            "  return JSON.stringify(links);"
            "})()"
        )

        try:
            result = js_evaluator(js_code)
            if not result:
                logger.warning("JavaScript evaluation returned empty result")
                return citations

            links_data = json.loads(result)
            if not isinstance(links_data, list):
                logger.warning("JavaScript evaluation did not return an array")
                return citations

            for i, link in enumerate(links_data, 1):
                url = link.get('href', '')
                if not self.is_valid_url(url):
                    continue

                normalized_url = self.normalize_url(url)
                if normalized_url in self._seen_urls:
                    continue

                self._seen_urls.add(normalized_url)

                title = link.get('title', '') or link.get('text', '')
                context = link.get('text', '') or f"Source {i}"

                citations.append(ExtractedCitation(
                    index=i,
                    url=normalized_url,
                    title=title[:100] if title else f"Source {i}",
                    context=context[:200] if context else f"Source {i}",
                    is_citation_marker=False,
                ))

            logger.info(f"Extracted {len(citations)} citations via JavaScript")

        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse JavaScript result: {e}")
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

    def to_markdown_inline(self, citations: List[ExtractedCitation], text: str) -> str:
        """Insert citations inline into text using [text](url) format"""
        if not citations:
            return text

        url_map = {}
        for cite in citations:
            key = cite.context or cite.title
            if key:
                url_map[key] = cite.url

        result = text
        for context, url in url_map.items():
            if context in result:
                result = result.replace(context, f"[{context}]({url})")

        return result


class MarkdownFormatter:
    """
    Formats search results as Markdown
    """

    @staticmethod
    def format_search_result(
        query: str,
        summary: str,
        citations: List[ExtractedCitation],
        include_sources: bool = True
    ) -> str:
        """
        Format search result as Markdown

        Args:
            query: Search query
            summary: AI Overview summary text
            citations: List of extracted citations
            include_sources: Whether to include sources section

        Returns:
            Markdown formatted string
        """
        lines = []

        lines.append(f"## {query}\n")

        if summary:
            summary = summary.strip()
            lines.append(summary)
            lines.append("")

        if include_sources and citations:
            lines.append(MarkdownFormatter.to_markdown_list(citations))

        return "\n".join(lines)

    @staticmethod
    def to_markdown_list(citations: List[ExtractedCitation]) -> str:
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
        <p>
            Python is a high-level programming language.
            <a href="https://python.org" title="Python Official Site">Python.org</a>
            is the official website.
        </p>
        <p>
            Learn more about
            <a href="https://docs.python.org" aria-label="Python Documentation">Python Documentation</a>
        </p>
    </div>
    """

    extractor = CitationExtractor()
    citations = extractor.extract_from_html(sample_html)

    print("=== Citation Extraction Demo ===\n")
    print(f"Found {len(citations)} citations:\n")

    for cite in citations:
        print(f"[{cite.index}] {cite.title}")
        print(f"    URL: {cite.url}")
        print(f"    Context: {cite.context}")
        print()

    print("\n--- Markdown Output ---\n")
    print(extractor.to_markdown_list(citations))


if __name__ == "__main__":
    main()
