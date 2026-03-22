"""
Multi-Language Selector - Language-aware CSS selector management
Supports English, German, Chinese, and other languages
"""

import locale
import os
import logging
from dataclasses import dataclass
from typing import Dict, List, Optional
from enum import Enum

logger = logging.getLogger(__name__)


class Language(Enum):
    """Supported languages"""
    ENGLISH = "en"
    GERMAN = "de"
    CHINESE = "zh"
    SPANISH = "es"
    FRENCH = "fr"
    ITALIAN = "it"
    DUTCH = "nl"
    UNKNOWN = "unknown"


@dataclass
class SelectorSet:
    """Collection of CSS selectors for a specific element type"""
    name: str
    selectors: List[str]


class LanguageSelector:
    """
    Manages language-specific CSS selectors for Google AI Mode

    Features:
    - Auto-detects browser language from system locale
    - Falls back to English for unknown languages
    - Provides selectors for:
      - Citation buttons
      - AI Overview container
      - Search input
      - Submit button
    """

    CITATION_SELECTORS = {
        Language.ENGLISH: [
            '[aria-label="View related links"]',
            '[aria-label*="Related links"]',
            'button[aria-label*="links" i]',
        ],
        Language.GERMAN: [
            '[aria-label="Zugehörige Links anzeigen"]',
            '[aria-label*="Zugehörige Links"]',
        ],
        Language.CHINESE: [
            '[aria-label="查看相关链接"]',
            '[aria-label*="相关链接"]',
        ],
        Language.SPANISH: [
            '[aria-label="Ver enlaces relacionados"]',
            '[aria-label*="enlaces relacionados"]',
        ],
        Language.FRENCH: [
            '[aria-label="Afficher les liens associés"]',
            '[aria-label*="liens associés"]',
        ],
        Language.ITALIAN: [
            '[aria-label="Visualizza link correlati"]',
            '[aria-label*="link correlati"]',
        ],
        Language.DUTCH: [
            '[aria-label="Gerelateerde links weergeven"]',
            '[aria-label*="Gerelateerde links"]',
        ],
    }

    AI_OVERVIEW_SELECTORS = {
        Language.ENGLISH: [
            '[data-ai-overview-had-ai]',
            '.ai-overview',
            '[data-container-id="main-col"]',
        ],
        Language.GERMAN: [
            '[data-ai-overview-had-ai]',
            '.ai-overview',
            '[data-container-id="main-col"]',
        ],
        Language.CHINESE: [
            '[data-ai-overview-had-ai]',
            '.ai-overview',
            '[data-container-id="main-col"]',
        ],
    }

    SEARCH_INPUT_SELECTORS = {
        Language.ENGLISH: [
            'textarea[name="q"]',
            'input[name="q"]',
            'input[title="Search"]',
            '[aria-label="Search"]',
        ],
        Language.GERMAN: [
            'textarea[name="q"]',
            'input[name="q"]',
            'input[title="Suche"]',
            '[aria-label="Suche"]',
        ],
        Language.CHINESE: [
            'textarea[name="q"]',
            'input[name="q"]',
            'input[title="搜索"]',
            '[aria-label="搜索"]',
        ],
    }

    SUBMIT_BUTTON_SELECTORS = {
        Language.ENGLISH: [
            'input[name="btnK"]',
            'input[value="Google Search"]',
            'input[value="手气不错"]',
            '[aria-label="Google Search"]',
        ],
        Language.GERMAN: [
            'input[name="btnK"]',
            'input[value="Google Suche"]',
            '[aria-label="Google Suche"]',
        ],
        Language.CHINESE: [
            'input[name="btnK"]',
            'input[value="Google 搜索"]',
            'input[value="搜索"]',
            '[aria-label="搜索"]',
        ],
    }

    LANGUAGE_CODE_MAP = {
        'en': Language.ENGLISH,
        'de': Language.GERMAN,
        'zh': Language.CHINESE,
        'es': Language.SPANISH,
        'fr': Language.FRENCH,
        'it': Language.ITALIAN,
        'nl': Language.DUTCH,
        'pt': Language.SPANISH,
        'ru': Language.ENGLISH,
        'ja': Language.ENGLISH,
        'ko': Language.ENGLISH,
    }

    def __init__(self, language: Optional[Language] = None):
        """
        Initialize LanguageSelector

        Args:
            language: Explicit language, or None for auto-detection
        """
        if language:
            self.language = language
        else:
            self.language = self.detect_language()

        logger.info(f"LanguageSelector initialized with language: {self.language.value}")

    def detect_language(self) -> Language:
        """
        Detect language from system locale

        Returns:
            Detected Language enum
        """
        detected = Language.UNKNOWN

        try:
            system_locale = locale.getdefaultlocale()[0]
            if system_locale:
                lang_code = system_locale.split('_')[0].lower()
                detected = self.LANGUAGE_CODE_MAP.get(lang_code, Language.ENGLISH)
        except Exception as e:
            logger.warning(f"Could not detect language from locale: {e}")
            detected = Language.ENGLISH

        env_lang = os.environ.get('LANG', '')
        if not detected or detected == Language.UNKNOWN:
            if 'de' in env_lang.lower():
                detected = Language.GERMAN
            elif 'zh' in env_lang.lower():
                detected = Language.CHINESE
            elif 'es' in env_lang.lower():
                detected = Language.SPANISH
            elif 'fr' in env_lang.lower():
                detected = Language.FRENCH
            elif 'it' in env_lang.lower():
                detected = Language.ITALIAN
            elif 'nl' in env_lang.lower():
                detected = Language.DUTCH
            else:
                detected = Language.ENGLISH

        logger.debug(f"Detected language: {detected.value}")
        return detected

    def get_citation_selectors(self) -> List[str]:
        """Get citation button selectors for current language"""
        return self.CITATION_SELECTORS.get(
            self.language,
            self.CITATION_SELECTORS[Language.ENGLISH]
        )

    def get_ai_overview_selectors(self) -> List[str]:
        """Get AI Overview container selectors for current language"""
        return self.AI_OVERVIEW_SELECTORS.get(
            self.language,
            self.AI_OVERVIEW_SELECTORS[Language.ENGLISH]
        )

    def get_search_input_selectors(self) -> List[str]:
        """Get search input selectors for current language"""
        return self.SEARCH_INPUT_SELECTORS.get(
            self.language,
            self.SEARCH_INPUT_SELECTORS[Language.ENGLISH]
        )

    def get_submit_button_selectors(self) -> List[str]:
        """Get submit button selectors for current language"""
        return self.SUBMIT_BUTTON_SELECTORS.get(
            self.language,
            self.SUBMIT_BUTTON_SELECTORS[Language.ENGLISH]
        )

    def get_selector_set(self, selector_type: str) -> SelectorSet:
        """
        Get a complete selector set for a specific type

        Args:
            selector_type: One of 'citation', 'ai_overview', 'search_input', 'submit_button'

        Returns:
            SelectorSet with name and list of selectors
        """
        selector_map = {
            'citation': (self.get_citation_selectors, 'Citation Buttons'),
            'ai_overview': (self.get_ai_overview_selectors, 'AI Overview'),
            'search_input': (self.get_search_input_selectors, 'Search Input'),
            'submit_button': (self.get_submit_button_selectors, 'Submit Button'),
        }

        if selector_type not in selector_map:
            raise ValueError(f"Unknown selector type: {selector_type}")

        get_selectors, name = selector_map[selector_type]
        return SelectorSet(name=name, selectors=get_selectors())

    def get_all_selectors(self) -> Dict[str, List[str]]:
        """Get all selector sets as a dictionary"""
        return {
            'citation': self.get_citation_selectors(),
            'ai_overview': self.get_ai_overview_selectors(),
            'search_input': self.get_search_input_selectors(),
            'submit_button': self.get_submit_button_selectors(),
        }

    @classmethod
    def get_supported_languages(cls) -> List[Language]:
        """Get list of supported languages"""
        return [
            Language.ENGLISH,
            Language.GERMAN,
            Language.CHINESE,
            Language.SPANISH,
            Language.FRENCH,
            Language.ITALIAN,
            Language.DUTCH,
        ]


def main():
    """Demo usage"""
    print("=== Language Selector Demo ===\n")

    selector = LanguageSelector()
    print(f"Detected language: {selector.language.value}\n")

    print("Citation Selectors:")
    for sel in selector.get_citation_selectors():
        print(f"  - {sel}")

    print("\nAI Overview Selectors:")
    for sel in selector.get_ai_overview_selectors():
        print(f"  - {sel}")

    print("\n--- Testing German ---")
    german_selector = LanguageSelector(Language.GERMAN)
    print(f"German Citation Selectors:")
    for sel in german_selector.get_citation_selectors():
        print(f"  - {sel}")

    print("\n--- Testing Chinese ---")
    chinese_selector = LanguageSelector(Language.CHINESE)
    print(f"Chinese Citation Selectors:")
    for sel in chinese_selector.get_citation_selectors():
        print(f"  - {sel}")

    print("\n=== Demo Complete ===")


if __name__ == "__main__":
    main()
