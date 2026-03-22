"""
Citation Cleaner - 清理 Google 界面文本污染

Phase 7 新增功能

问题:
- 引用标题包含 Google 界面文本（如 "在新分頁中開啟", "Open in new tab"）
- 这些文本污染了引用标题，影响可读性

解决方案:
- 自动识别并清理 Google 界面文本
- 支持多语言界面
- 保留原始标题语义完整性

支持的语言:
- 中文 (zh-TW, zh-CN)
- 英文 (en)
- 日文 (ja)
- 德文 (de)
- 荷兰文 (nl)
- 法文 (fr)
- 西班牙文 (es)
- 意大利文 (it)
"""

import re
from typing import List, Optional


class CitationCleaner:
    """
    Google 引用标题清理器

    自动移除 Google 搜索结果中的界面文本污染
    """

    GOOGLE_SUFFIXES = {
        "zh-TW": [
            "在新分頁中開啟",
            "在新分頁中開啟。",
            "。 在新分頁中開啟",
            "在新标签页中打开",
            "。 在新标签页中打开",
            "在新窗口中打开",
            "。 在新窗口中打开",
        ],
        "zh-CN": [
            "在新标签页中打开",
            "。 在新标签页中打开",
            "在新窗口中打开",
            "。 在新窗口中打开",
        ],
        "en": [
            "Open in new tab",
            "Open link in new tab",
            " - Google Search",
            " - Google",
        ],
        "ja": [
            "新しいタブで開く",
            "新しいウィンドウで開く",
            " - Google 検索",
        ],
        "de": [
            "In neuem Tab öffnen",
            "In neuem Fenster öffnen",
            "Link in neuem Tab öffnen",
        ],
        "nl": [
            "Open in nieuw tabblad",
            "Koppeling openen in nieuw tabblad",
        ],
        "fr": [
            "Ouvrir dans un nouvel onglet",
            "Ouvrir le lien dans un nouvel onglet",
        ],
        "es": [
            "Abrir en una nueva pestaña",
            "Abrir enlace en una nueva pestaña",
        ],
        "it": [
            "Apri in una nuova scheda",
            "Apri link in una nuova scheda",
        ],
    }

    GOOGLE_PATTERNS = {
        "zh-TW": [
            r'\s+在新分頁中開啟\.?$',
            r'\s+在新标签页中打开\.?$',
            r'\s+在新窗口中打开\.?$',
        ],
        "zh-CN": [
            r'\s+在新标签页中打开\.?$',
            r'\s+在新窗口中打开\.?$',
        ],
        "en": [
            r'\s+Open in new tab\.?$',
            r'\s+Open link in new tab\.?$',
            r'\s+Open in new window\.?$',
        ],
        "ja": [
            r'\s+新しいタブで開く\.?$',
            r'\s+新しいウィンドウで開く\.?$',
        ],
        "de": [
            r'\s+In neuem Tab öffnen\.?$',
            r'\s+In neuem Fenster öffnen\.?$',
        ],
    }

    def __init__(self, language: Optional[str] = None):
        """
        初始化清理器

        Args:
            language: 界面语言 (默认自动检测)
        """
        self.language = language

    def clean_title(self, title: str, language: Optional[str] = None) -> str:
        """
        清理标题中的 Google 界面文本

        Args:
            title: 原始标题
            language: 界面语言（可选）

        Returns:
            清理后的标题
        """
        if not title:
            return title

        lang = language or self.language or "en"
        cleaned = title

        suffixes = self.GOOGLE_SUFFIXES.get(lang, self.GOOGLE_SUFFIXES["en"])
        for suffix in suffixes:
            if cleaned.endswith(suffix):
                cleaned = cleaned[:-len(suffix)].strip()

        patterns = self.GOOGLE_PATTERNS.get(lang, [])
        for pattern in patterns:
            cleaned = re.sub(pattern, '', cleaned, flags=re.IGNORECASE)

        cleaned = cleaned.strip()

        if cleaned.endswith('...'):
            parts = cleaned.rsplit('...', 1)
            if len(parts[0]) > 3:
                cleaned = parts[0].strip()

        if cleaned.endswith('..'):
            parts = cleaned.rsplit('..', 1)
            if len(parts[0]) > 3:
                cleaned = parts[0].strip()

        cleaned = cleaned.strip()

        if cleaned.endswith('.') and not cleaned.endswith('...'):
            if len(cleaned) > 3:
                cleaned = cleaned[:-1].strip()

        if cleaned.endswith(' - Google'):
            cleaned = cleaned[:-9].strip()
        if cleaned.endswith(' - Wikipedia'):
            cleaned = cleaned[:-11].strip()

        if cleaned.endswith('|'):
            if len(cleaned) > 1:
                cleaned = cleaned[:-1].strip()

        if re.match(r'^[【\[【\[《<].*[】\]]\】\]\】\)]+$', cleaned):
            if len(cleaned) > 4:
                cleaned = cleaned[1:-1].strip()

        if ' | ' in cleaned:
            parts = cleaned.split(' | ')
            if len(parts) > 0:
                cleaned = parts[0].strip()

        if '|' in cleaned:
            cleaned = cleaned.replace('|', ' ').strip()

        if '  ' in cleaned:
            cleaned = ' '.join(cleaned.split())

        cleaned = re.sub(r'\s+', ' ', cleaned)

        return cleaned

    def clean_citation(self, citation: dict, language: Optional[str] = None) -> dict:
        """
        清理引用对象中的标题

        Args:
            citation: 引用字典对象
            language: 界面语言（可选）

        Returns:
            清理后的引用对象
        """
        if not citation:
            return citation

        cleaned_citation = citation.copy()

        if 'title' in cleaned_citation and cleaned_citation['title']:
            cleaned_citation['title'] = self.clean_title(
                cleaned_citation['title'],
                language
            )

        return cleaned_citation

    def clean_citations(self, citations: List[dict], language: Optional[str] = None) -> List[dict]:
        """
        批量清理引用列表中的标题

        Args:
            citations: 引用列表
            language: 界面语言（可选）

        Returns:
            清理后的引用列表
        """
        return [
            self.clean_citation(citation, language)
            for citation in citations
        ]

    def detect_language(self, text: str) -> str:
        """
        自动检测文本语言

        Args:
            text: 待检测文本

        Returns:
            检测到的语言代码
        """
        text_lower = text.lower()

        zh_indicators = ['在新分頁', '在新标签', '在新窗口', '在新分页']
        if any(indicator in text_lower for indicator in zh_indicators):
            return 'zh-TW'

        en_indicators = ['open in new tab', 'open link']
        if any(indicator in text_lower for indicator in en_indicators):
            return 'en'

        ja_indicators = ['新しいタブ', '新しいウィンドウ']
        if any(indicator in text for indicator in ja_indicators):
            return 'ja'

        de_indicators = ['neuem tab öffnen', 'neuem fenster']
        if any(indicator in text_lower for indicator in de_indicators):
            return 'de'

        return 'en'

    def clean_with_auto_detect(self, title: str) -> str:
        """
        自动检测语言并清理标题

        Args:
            title: 原始标题

        Returns:
            清理后的标题
        """
        detected_lang = self.detect_language(title)
        return self.clean_title(title, detected_lang)


def clean_search_result_citations(result: object, language: Optional[str] = None) -> object:
    """
    清理搜索结果中的所有引用标题

    Args:
        result: SearchResult 对象
        language: 界面语言（可选）

    Returns:
        清理后的 SearchResult 对象
    """
    cleaner = CitationCleaner(language)

    if hasattr(result, 'citations') and result.citations:
        for citation in result.citations:
            if hasattr(citation, 'title'):
                citation.title = cleaner.clean_title(citation.title, language)

    return result


def demo():
    """演示 CitationCleaner 的使用"""
    print("=" * 70)
    print("CitationCleaner 演示 - Phase 7")
    print("=" * 70)

    cleaner = CitationCleaner()

    test_cases = [
        ("zh-TW", "“GHOST IN THE SHELL” Celebrates Its 30th Theatrical .... 在新分頁中開啟。"),
        ("zh-CN", "Python 教程 - 完整指南在新标签页中打开"),
        ("en", "JavaScript Tutorial - Complete Guide Open in new tab"),
        ("en", "React Best Practices 2026 - Google"),
        ("ja", "Python チュートリアル - 完全ガイド新しいタブで開く"),
        ("de", "Python Tutorial - Vollständiger Leitfaden In neuem Tab öffnen"),
    ]

    print("\n测试用例:")
    print("-" * 70)

    for lang, title in test_cases:
        cleaned = cleaner.clean_title(title, lang)
        print(f"\n[{lang}]")
        print(f"原始: {title}")
        print(f"清理后: {cleaned}")

    print("\n" + "=" * 70)
    print("自动检测示例:")
    print("-" * 70)

    auto_cases = [
        "Python 教程 ... 在新分頁中開啟",
        "JavaScript Tutorial ... Open in new tab",
        "Python ガイド ... 新しいタブで開く",
    ]

    for title in auto_cases:
        cleaned = cleaner.clean_with_auto_detect(title)
        detected = cleaner.detect_language(title)
        print(f"\n[检测: {detected}]")
        print(f"原始: {title}")
        print(f"清理后: {cleaned}")

    print("\n" + "=" * 70)
    print("批量清理示例:")
    print("-" * 70)

    citations = [
        {"title": "Python Tutorial ... Open in new tab", "url": "https://example.com/1"},
        {"title": "JavaScript Guide ... 在新分頁中開啟", "url": "https://example.com/2"},
        {"title": "React Docs - Google Search", "url": "https://example.com/3"},
    ]

    print("\n原始引用:")
    for c in citations:
        print(f"  - {c['title']}")

    cleaned_citations = cleaner.clean_citations(citations)

    print("\n清理后引用:")
    for c in cleaned_citations:
        print(f"  - {c['title']}")


if __name__ == "__main__":
    demo()
