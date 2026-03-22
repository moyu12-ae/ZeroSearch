"""
HTML to Markdown Converter
Enhanced version inspired by html-to-markdown library

Features:
- Converts HTML to clean Markdown
- Code block handling (removes unwanted links)
- Multi-language cut-off markers
- Smart line merging
- Preserves formatting
"""

import re
from typing import Optional, List, Tuple
from bs4 import BeautifulSoup, NavigableString, Tag
import logging

logger = logging.getLogger(__name__)

CUTOFF_MARKERS = [
    "...", "…", "... [", "[…]", "read more", "read more…",
    "... [Mehr", "… [Mehr", "weiterlesen", "mehr anzeigen",
    "... [Meer", "… [Meer", "lees meer", "meer weergeven",
    "... [En savoir plus", "… [En savoir plus", "en savoir plus",
    "... [Más información", "… [Más información", "saber más",
    "... [Scopri di più", "… [Scopri di più", " Ulteriori informazioni",
]

REMOVE_PATTERNS = [
    r'\[\s*…\s*\]',
    r'\[\s*more\s*\]',
    r'\[\s*Mehr\s*\]',
    r'\[\s*Meer\s*\]',
    r'\[\s*En savoir plus\s*\]',
    r'\[\s*Más información\s*\]',
    r'\[\s*Scopri di più\s*\]',
]


class HtmlToMarkdownConverter:
    """
    Converts HTML to clean Markdown format

    Inspired by html-to-markdown library but simplified for our use case.
    """

    def __init__(self):
        self._remove_extra_newlines = True

    def convert(self, html: str) -> str:
        """
        Convert HTML to Markdown

        Args:
            html: HTML content

        Returns:
            Clean Markdown string
        """
        if not html:
            return ""

        try:
            soup = BeautifulSoup(html, 'html.parser')

            text = self._process_element(soup.body if soup.body else soup)

            text = self._post_process(text)

            return text.strip()

        except Exception as e:
            logger.warning(f"HTML conversion failed: {e}")
            return self._fallback_convert(html)

    def _process_element(self, element) -> str:
        """Process a single HTML element"""
        if isinstance(element, NavigableString):
            return str(element)

        if not isinstance(element, Tag):
            return ""

        tag_name = element.name.lower()

        if tag_name in ['script', 'style', 'noscript']:
            return ""

        if tag_name == 'br':
            return '\n'

        if tag_name == 'hr':
            return '\n---\n'

        if tag_name == 'p':
            return self._process_block(element)

        if tag_name in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
            level = int(tag_name[1])
            content = self._process_inline(element)
            return f"{'#' * level} {content}\n\n"

        if tag_name == 'a':
            return self._process_link(element)

        if tag_name == 'code':
            return self._process_code(element)

        if tag_name == 'pre':
            return self._process_pre(element)

        if tag_name == 'ul':
            return self._process_list(element, ordered=False)

        if tag_name == 'ol':
            return self._process_list(element, ordered=True)

        if tag_name == 'li':
            content = self._process_inline(element)
            return f"- {content}\n"

        if tag_name in ['strong', 'b']:
            content = self._process_inline(element)
            return f"**{content}**"

        if tag_name in ['em', 'i']:
            content = self._process_inline(element)
            return f"*{content}*"

        if tag_name == 'blockquote':
            content = self._process_block(element)
            return f"> {content}\n\n"

        if tag_name == 'div':
            return self._process_block(element)

        if tag_name == 'span':
            return self._process_inline(element)

        if tag_name == 'img':
            alt = element.get('alt', '')
            src = element.get('src', '')
            if alt:
                return f"![{alt}]({src})" if src else alt
            return ""

        if tag_name in ['table', 'thead', 'tbody', 'tr', 'th', 'td']:
            return self._process_table(element)

        if tag_name == 'figure':
            return self._process_figure_img(element)

        return self._process_children(element)

    def _process_block(self, element) -> str:
        """Process block-level elements"""
        content = self._process_children(element)
        return f"{content}\n\n"

    def _process_inline(self, element) -> str:
        """Process inline elements"""
        return self._process_children(element)

    def _process_children(self, element) -> str:
        """Process all children of an element"""
        parts = []
        for child in element.children:
            if isinstance(child, NavigableString):
                text = str(child)
                parts.append(text)
            elif isinstance(child, Tag):
                parts.append(self._process_element(child))
        return ''.join(parts)

    def _process_link(self, element) -> str:
        """Process link elements"""
        href = element.get('href', '')
        text = element.get_text(strip=True)

        if not href or not text:
            return text

        if not text.strip():
            return ""

        return f"[{text}]({href})"

    def _process_code(self, element) -> str:
        """Process code elements"""
        text = element.get_text()
        return f"`{text}`"

    def _process_pre(self, element) -> str:
        """Process pre/code blocks"""
        code = element.get_text()
        language = ""

        classes = element.get('class', [])
        for cls in classes:
            if cls.startswith('language-'):
                language = cls.split('-', 1)[1]
                break

        if language:
            return f"```{language}\n{code}\n```\n\n"
        return f"```\n{code}\n```\n\n"

    def _process_list(self, element, ordered: bool = False) -> str:
        """Process list elements"""
        parts = []
        for i, li in enumerate(element.find_all('li', recursive=False)):
            content = li.get_text(strip=True)
            marker = f"{i+1}." if ordered else "-"
            parts.append(f"{marker} {content}")

        sep = "\n" if ordered else "\n"
        return sep.join(parts) + "\n\n"

    def _process_table(self, element) -> str:
        """Process table elements"""
        rows = []

        for tr in element.find_all('tr'):
            cells = []
            for cell in tr.find_all(['th', 'td']):
                cells.append(cell.get_text(strip=True))
            if cells:
                rows.append(cells)

        if not rows:
            return ""

        header = rows[0] if rows else []
        body = rows[1:] if len(rows) > 1 else []

        md_rows = []

        if header:
            md_rows.append("| " + " | ".join(header) + " |")
            md_rows.append("| " + " | ".join(["---"] * len(header)) + " |")

        for row in body:
            md_rows.append("| " + " | ".join(row) + " |")

        return "\n".join(md_rows) + "\n\n"

    def _process_figure_img(self, element) -> str:
        """Process figure elements"""
        img = element.find('img')
        if img:
            alt = img.get('alt', '')
            src = img.get('src', '')
            caption = element.find('figcaption')
            caption_text = caption.get_text(strip=True) if caption else ""

            result = f"![{alt}]({src})"
            if caption_text:
                result += f"\n*{caption_text}*"
            return result + "\n\n"
        return ""

    def _post_process(self, text: str) -> str:
        """Post-process converted text"""
        text = self._remove_cutoff_markers(text)

        text = self._remove_code_block_links(text)

        text = self._smart_line_merge(text)

        text = self._cleanup_whitespace(text)

        return text

    def _remove_cutoff_markers(self, text: str) -> str:
        """Remove cut-off markers like '...' or 'read more'"""
        result = text

        for pattern in REMOVE_PATTERNS:
            result = re.sub(pattern, '', result, flags=re.IGNORECASE)

        return result

    def _remove_code_block_links(self, text: str) -> str:
        """Remove unwanted links from code blocks"""
        lines = text.split('\n')
        in_code_block = False
        result_lines = []

        for line in lines:
            if line.strip().startswith('```'):
                in_code_block = not in_code_block
                result_lines.append(line)
            elif in_code_block:
                line = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', line)
                result_lines.append(line)
            else:
                result_lines.append(line)

        return '\n'.join(result_lines)

    def _smart_line_merge(self, text: str) -> str:
        """Smart merge of incomplete lines"""
        lines = text.split('\n')
        result = []
        buffer = ""

        for line in lines:
            stripped = line.strip()

            if not stripped:
                if buffer:
                    result.append(buffer)
                    buffer = ""
                result.append("")
                continue

            if buffer and not buffer.endswith(('.', '!', '?', ':', ']', ')', '"', "'")):
                if len(stripped) < 80 and not stripped.startswith(('#', '-', '>', '*', '`')):
                    buffer += " " + stripped
                    continue

            if buffer:
                result.append(buffer)
            buffer = stripped

        if buffer:
            result.append(buffer)

        return '\n'.join(result)

    def _cleanup_whitespace(self, text: str) -> str:
        """Clean up extra whitespace"""
        text = re.sub(r'\n\n\n+', '\n\n', text)
        text = re.sub(r'[ \t]+\n', '\n', text)
        text = re.sub(r'\n[ \t]+', '\n', text)
        text = re.sub(r' +', ' ', text)
        return text

    def _fallback_convert(self, html: str) -> str:
        """Fallback conversion when BeautifulSoup fails"""
        text = re.sub(r'<br\s*/?>', '\n', html)
        text = re.sub(r'<[^>]+>', '', text)
        text = re.sub(r'\n\s*\n', '\n\n', text)
        text = text.strip()
        return text


def convert_html_to_markdown(html: str) -> str:
    """
    Convenience function to convert HTML to Markdown

    Args:
        html: HTML content

    Returns:
        Clean Markdown string
    """
    converter = HtmlToMarkdownConverter()
    return converter.convert(html)


def main():
    """Demo usage"""
    sample_html = """
    <div>
        <h1>Python Programming</h1>
        <p>
            Python is a high-level programming language.
            <a href="https://python.org" title="Python">Python.org</a>
            is the official website.
        </p>
        <pre><code class="language-python">
def hello():
    # This is a comment with [link](https://example.com)
    print("Hello, World!")
        </code></pre>
        <ul>
            <li>Easy to learn</li>
            <li>Powerful libraries</li>
        </ul>
    </div>
    """

    converter = HtmlToMarkdownConverter()
    markdown = converter.convert(sample_html)

    print("=== HTML to Markdown Demo ===\n")
    print(markdown)


if __name__ == "__main__":
    main()
