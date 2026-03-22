"""
Search Engine - Google AI Mode Search Implementation
Uses agent-browser CLI Connect Mode only (real Chrome via CDP)

Phase 5 Enhanced Features:
- 3-layer CAPTCHA detection (URL/text/length)
- Fingerprint randomization (UA, viewport, timezone, language)
- Balanced rate limiting (15-30s between searches)
- CoolingManager for progressive cooldown
- Session persistence management
- 40-second timeout for AI Mode
"""

import time
import re
import json
import logging
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Optional, Set, Dict
from urllib.parse import quote_plus, urlparse

try:
    from .browser import BrowserManager, BrowserError, BrowserNotRunningError, DEFAULT_PROFILE_DIR, DEFAULT_HEADERS
    from .logger import get_logger
    from .captcha_handler import CaptchaHandler, CaptchaResult, AntiBotDetector
    from .rate_limiter import RateLimiter, RateLimitConfig, RateLimitMode, create_rate_limiter
    from .session_manager import SessionManager, SessionState
    from .fingerprint import FingerprintGenerator
    from .cooling_manager import CoolingManager
    from .citation_cleaner import CitationCleaner
    from .smart_timeout import SmartTimeout, SmartTimeoutConfig, create_smart_timeout
    from .smart_rate_limiter import SmartRateLimiter, SmartRateLimiterConfig
except ImportError:
    from browser import BrowserManager, BrowserError, BrowserNotRunningError, DEFAULT_PROFILE_DIR, DEFAULT_HEADERS
    from logger import get_logger
    from captcha_handler import CaptchaHandler, CaptchaResult, AntiBotDetector
    from rate_limiter import RateLimiter, RateLimitConfig, RateLimitMode, create_rate_limiter
    from session_manager import SessionManager, SessionState
    from fingerprint import FingerprintGenerator
    from cooling_manager import CoolingManager
    from citation_cleaner import CitationCleaner
    from smart_timeout import SmartTimeout, SmartTimeoutConfig, create_smart_timeout
    from smart_rate_limiter import SmartRateLimiter, SmartRateLimiterConfig

logger = get_logger(__name__)


CITATION_SELECTORS = [
    '[aria-label="View related links"]',
    '[aria-label*="Related links"]',
    '[aria-label="Zugehörige Links anzeigen"]',
    '[aria-label*="Zugehörige Links"]',
    '[aria-label*="Gerelateerde links"]',
    'button[aria-label*="links" i]',
]

AI_COMPLETION_TEXT_INDICATORS = [
    'AI-generated', 'AI Overview', 'Generative AI is experimental',
    'KI-generiert', 'KI-Antworten', 'Generative KI',
    'AI-gegenereerd', 'AI-overzicht',
    'Las respuestas de la IA', 'Resumen de IA',
    "Les réponses de l'IA", "Aperçu de l'IA",
    'Risposte IA', "Panoramica IA",
]

AI_MODE_NOT_AVAILABLE = [
    "AI Mode is not available in your country or language",
    "AI Mode isn't available",
    "Der KI-Modus ist in Ihrem Land oder Ihrer Sprache nicht verfügbar",
    "KI-Modus ist nicht verfügbar",
    "El modo de IA no está disponible en tu país o idioma",
    "La modalità IA non è disponibile nel tuo Paese o nella tua lingua",
    "AI-modus is niet beschikbaar in uw land of taal",
    "Le Mode IA n'est pas disponible",
    "Découvrez le Mode IA",
]

CUTOFF_MARKERS = [
    'KI-Antworten können Fehler enthalten',
    'AI-generated answers may contain mistakes',
    'AI can make mistakes',
    'Generative AI is experimental',
    'Las respuestas de la IA pueden contener errores',
    "Les réponses de l'IA peuvent contenir des erreurs",
    "Le risposte dell'IA possono contenere errori",
]


@dataclass
class Citation:
    """Represents a citation with context and URL"""
    index: int
    url: str
    title: str
    context: str
    source: str = ""


@dataclass
class SearchResult:
    """Represents a complete search result"""
    query: str
    url: str
    summary: str
    citations: List[Citation] = field(default_factory=list)
    markdown_output: str = ""
    ai_mode_available: bool = True
    error_message: str = ""
    captcha_detected: bool = False
    rate_limit_wait: float = 0.0


class SearchError(Exception):
    """Base exception for search-related errors"""
    pass


class AIOverviewNotFoundError(SearchError):
    """Raised when AI Overview is not found"""
    pass


class AIModeNotAvailableError(SearchError):
    """Raised when AI Mode is not available in region"""
    def __init__(self, message: str = ""):
        self.message = message
        super().__init__(message)


class CAPTCHAError(SearchError):
    """Raised when CAPTCHA is detected"""
    def __init__(self, message: str = "", result: Optional[CaptchaResult] = None):
        self.message = message
        self.captcha_result = result
        super().__init__(message)


class SearchEngine:
    """
    Google AI Mode Search Engine

    Two modes of operation:
    1. Connect Mode: Connect to existing Chrome via CDP (default)
    2. Stealth Mode: Launch Chrome with anti-detection parameters

    Phase 5 Enhanced Features:
    - FingerprintGenerator: Random browser fingerprint (UA, viewport, timezone, language)
    - AntiBotDetector: 3-layer CAPTCHA detection (URL/text/length)
    - RateLimiter: Balanced rate limiting (15-30s between searches)
    - CoolingManager: Progressive cooldown on CAPTCHA detection
    - SessionManager: Session persistence management
    - 40-second timeout for AI Mode
    - Stealth Mode: Launch Chrome with anti-detection parameters

    Features:
    - 3-layer AI Mode completion detection (SVG/aria-label/text)
    - DOM injection citation extraction
    - AI Mode availability detection
    - Multi-language support
    - Persistent context with cookies storage
    - HTTP Headers customization (Accept-Language)
    """

    GOOGLE_URL = "https://www.google.com"
    AI_MODE_PARAM = "udm=50"

    DEFAULT_PORT = 9222
    DEFAULT_MAX_RETRIES = 3
    AI_MODE_TIMEOUT_MS = 40000

    EXCLUDE_DOMAINS = [
        'google.com', 'google.de', 'gstatic.com',
        'support.google.com', 'maps.google.com',
    ]

    def __init__(
        self,
        connect_port: int = DEFAULT_PORT,
        max_retries: int = DEFAULT_MAX_RETRIES,
        profile_dir: Optional[Path] = None,
        headers: Optional[Dict[str, str]] = None,
        enable_rate_limiting: bool = True,
        enable_session_persistence: bool = True,
        enable_fingerprint: bool = True,
        enable_cooling: bool = True,
        stealth_mode: bool = False,
        auto_launch_stealth: bool = True,
        enable_citation_cleaning: bool = True,
        enable_smart_timeout: bool = True,
        enable_smart_rate_limiter: bool = True,
    ):
        self._connect_port = connect_port
        self._max_retries = max_retries
        self._profile_dir = profile_dir or DEFAULT_PROFILE_DIR
        self._headers = headers or DEFAULT_HEADERS
        self._browser: Optional[BrowserManager] = None
        self._captcha_handler: Optional[CaptchaHandler] = None
        self._rate_limiter: Optional[RateLimiter] = None
        self._smart_rate_limiter: Optional[SmartRateLimiter] = None
        self._session_manager: Optional[SessionManager] = None
        self._fingerprint_generator: Optional[FingerprintGenerator] = None
        self._cooling_manager: Optional[CoolingManager] = None
        self._citation_cleaner: Optional[CitationCleaner] = None
        self._smart_timeout: Optional[SmartTimeout] = None
        self._enable_rate_limiting = enable_rate_limiting
        self._enable_session_persistence = enable_session_persistence
        self._enable_fingerprint = enable_fingerprint
        self._enable_cooling = enable_cooling
        self._stealth_mode = stealth_mode
        self._auto_launch_stealth = auto_launch_stealth
        self._enable_citation_cleaning = enable_citation_cleaning
        self._enable_smart_timeout = enable_smart_timeout
        self._enable_smart_rate_limiter = enable_smart_rate_limiter
        self._owns_chrome = False

        if self._enable_citation_cleaning:
            self._citation_cleaner = CitationCleaner()

        if self._enable_smart_timeout:
            self._smart_timeout = create_smart_timeout(
                state_file=self._profile_dir / "smart_timeout_state.json"
            )

        if self._enable_smart_rate_limiter and self._enable_rate_limiting:
            self._smart_rate_limiter = SmartRateLimiter(
                state_file=self._profile_dir / "smart_rate_limiter_state.json"
            )
            self._rate_limiter = None
        elif self._enable_rate_limiting:
            self._rate_limiter = create_rate_limiter(
                state_file=self._profile_dir / "rate_limit_state.json"
            )

    def _get_browser(self) -> BrowserManager:
        """Get or create browser instance"""
        if self._browser is None:
            self._browser = BrowserManager(
                connect_port=self._connect_port,
                timeout=60,
                max_retries=self._max_retries,
                profile_dir=self._profile_dir,
                headers=self._headers,
            )

            if self._stealth_mode and self._auto_launch_stealth:
                logger.info("Launching stealth Chrome with anti-detection parameters...")
                if self._browser.launch_stealth_chrome():
                    self._owns_chrome = True
                    logger.info("Stealth Chrome launched successfully")
                else:
                    logger.warning("Failed to launch stealth Chrome, falling back to existing Chrome")

        return self._browser

    def launch_stealth_chrome(self) -> bool:
        """
        Launch Chrome with anti-detection parameters.

        This is useful when you want to start stealth Chrome manually
        instead of automatically on first search.

        Returns:
            True if Chrome launched successfully
        """
        if self._browser is None:
            self._get_browser()

        if self._browser:
            result = self._browser.launch_stealth_chrome()
            self._owns_chrome = result
            return result
        return False

    def _get_captcha_handler(self) -> CaptchaHandler:
        """Get or create CAPTCHA handler"""
        if self._captcha_handler is None:
            self._captcha_handler = CaptchaHandler(self._get_browser())
        return self._captcha_handler

    def _get_rate_limiter(self) -> RateLimiter:
        """Get or create rate limiter (Phase 5: balanced mode 15-30s)"""
        if self._rate_limiter is None:
            self._rate_limiter = create_rate_limiter(
                mode=RateLimitMode.BALANCED,
                state_file=self._profile_dir / "rate_limit_state.json"
            )
        return self._rate_limiter

    def _get_fingerprint_generator(self) -> FingerprintGenerator:
        """Get or create fingerprint generator (Phase 5)"""
        if self._fingerprint_generator is None:
            self._fingerprint_generator = FingerprintGenerator()
        return self._fingerprint_generator

    def _get_cooling_manager(self) -> CoolingManager:
        """Get or create cooling manager (Phase 5)"""
        if self._cooling_manager is None:
            self._cooling_manager = CoolingManager(
                state_file=self._profile_dir / "cooling_state.json"
            )
        return self._cooling_manager

    def _clean_citations(self, citations: List[Citation]) -> List[Citation]:
        """
        Clean citation titles by removing Google interface text pollution.

        Phase 7 Feature: Citation Cleaner Integration

        This method:
        1. Auto-detects language from citation content
        2. Removes Google interface text (e.g., "在新分頁中開啟", "Open in new tab")
        3. Preserves original title semantics
        4. Returns cleaned citations

        Args:
            citations: List of Citation objects to clean

        Returns:
            List of Citation objects with cleaned titles
        """
        if not citations or not self._citation_cleaner:
            return citations

        cleaned_citations = []
        for citation in citations:
            cleaned_citation = Citation(
                index=citation.index,
                url=citation.url,
                title=self._citation_cleaner.clean_with_auto_detect(citation.title),
                context=citation.context,
                source=citation.source,
            )
            cleaned_citations.append(cleaned_citation)

        logger.debug(f"Cleaned {len(cleaned_citations)} citation titles")
        return cleaned_citations

    def _get_session_manager(self) -> SessionManager:
        """Get or create session manager"""
        if self._session_manager is None:
            self._session_manager = SessionManager(
                profile_dir=self._profile_dir,
                profile_name="google_search"
            )
        return self._session_manager

    def _check_captcha(self) -> CaptchaResult:
        """
        Check if current page is a CAPTCHA/sorry page.

        Uses 3-layer detection:
        - Layer 1: URL contains /sorry/index
        - Layer 2: Body text contains "unusual traffic"
        - Layer 3: Page content is very short (< 600 chars)

        Returns:
            CaptchaResult with detection details
        """
        handler = self._get_captcha_handler()
        return handler.detect()

    def _apply_rate_limiting(self) -> float:
        """
        Apply rate limiting before search (Phase 5: balanced mode).

        Returns:
            Time waited in seconds
        """
        if not self._enable_rate_limiting:
            return 0.0

        limiter = self._get_rate_limiter()
        return limiter.wait_if_needed()

    def _apply_fingerprint(self) -> None:
        """
        Apply random fingerprint to browser (Phase 5).

        Generates and applies random browser fingerprint including:
        - User-Agent
        - Viewport
        - Timezone
        - Language
        """
        if not self._enable_fingerprint:
            return

        try:
            fp_generator = self._get_fingerprint_generator()
            fp = fp_generator.generate()

            browser = self._get_browser()

            js_code = f"""
(function() {{
    // Apply User-Agent
    Object.defineProperty(navigator, 'userAgent', {{
        get: function() {{ return '{fp.user_agent}'; }}
    }});

    // Apply language
    Object.defineProperty(navigator, 'language', {{
        get: function() {{ return '{fp.language}'; }}
    }});

    // Apply platform
    Object.defineProperty(navigator, 'platform', {{
        get: function() {{ return '{fp.platform}'; }}
    }});

    // Apply hardware concurrency
    Object.defineProperty(navigator, 'hardwareConcurrency', {{
        get: function() {{ return {fp.hardware_concurrency}; }}
    }});

    // Apply device memory
    if (navigator.deviceMemory !== undefined) {{
        Object.defineProperty(navigator, 'deviceMemory', {{
            get: function() {{ return {fp.device_memory}; }}
        }});
    }}

    return true;
}})()
"""
            browser.eval_js(js_code)
            logger.debug(f"Applied fingerprint: {fp.viewport_width}x{fp.viewport_height}, {fp.timezone}, {fp.language}")

        except Exception as e:
            logger.debug(f"Failed to apply fingerprint: {e}")

    def _check_cooling(self) -> bool:
        """
        Check if currently in cooling period (Phase 5).

        Returns:
            True if should wait before search
        """
        if not self._enable_cooling:
            return False

        cooling_manager = self._get_cooling_manager()
        cooling_status = cooling_manager.check_cooling()

        if cooling_status.needs_cooldown:
            remaining = cooling_manager.get_cooldown_remaining()
            logger.warning(f"In cooling period: {remaining:.0f}s remaining")
            logger.warning(f"  Message: {cooling_status.message}")
            return True

        return False

    def _restore_session(self) -> bool:
        """
        Restore session from saved state.

        Returns:
            True if session was restored
        """
        if not self._enable_session_persistence:
            return False

        try:
            session_manager = self._get_session_manager()
            state = session_manager.load_session()

            if not state:
                logger.debug("No saved session to restore")
                return False

            browser = self._get_browser()
            if session_manager.apply_session(browser, state):
                logger.info("Session restored successfully")
                return True

        except Exception as e:
            logger.debug(f"Failed to restore session: {e}")

        return False

    def _save_session(self) -> bool:
        """
        Save current session state.

        Returns:
            True if session was saved
        """
        if not self._enable_session_persistence:
            return False

        try:
            session_manager = self._get_session_manager()
            browser = self._get_browser()
            return session_manager.save_session(browser)
        except Exception as e:
            logger.debug(f"Failed to save session: {e}")
            return False

    def _build_search_url(self, query: str) -> str:
        """Build Google AI Mode search URL"""
        encoded_query = quote_plus(query)
        return f"{self.GOOGLE_URL}/search?q={encoded_query}&{self.AI_MODE_PARAM}"

    def _is_valid_url(self, url: str) -> bool:
        """Check if URL is valid for citation"""
        if not url or not isinstance(url, str):
            return False

        url_lower = url.lower().strip()

        if url_lower.startswith(('javascript:', 'mailto:', 'tel:', '#')):
            return False

        for domain in self.EXCLUDE_DOMAINS:
            if domain in url_lower:
                return False

        return len(url) >= 20

    def _normalize_url(self, url: str) -> str:
        """Normalize URL for deduplication"""
        url = url.strip()
        url = re.sub(r'#.*$', '', url)
        url = re.sub(r'[?&]utm_[^?&]+', '', url)
        return url

    def _check_ai_mode_available(self) -> tuple[bool, str]:
        """
        Check if AI Mode is available in current region.

        Returns:
            Tuple of (is_available, error_message)
        """
        browser = self._get_browser()

        try:
            body_text = browser.eval_js_simple('document.body.innerText') or ''

            for indicator in AI_MODE_NOT_AVAILABLE:
                if indicator in body_text:
                    logger.error(f"AI Mode not available: {indicator}")
                    return False, indicator

        except Exception as e:
            logger.debug(f"AI Mode availability check failed: {e}")

        return True, ""

    def _wait_for_ai_mode_complete(self) -> bool:
        """
        Wait for AI Mode to complete using 3-layer detection.

        Phase 7: Uses SmartTimeout for adaptive waiting strategy.

        Returns:
            True if AI Mode completed, False if timeout
        """
        browser = self._get_browser()

        if self._enable_smart_timeout and self._smart_timeout:
            def check_ai_complete():
                return browser.check_ai_mode_complete()

            logger.info("Using SmartTimeout for AI Mode detection")

            success = self._smart_timeout.wait_for_complete(check_ai_complete)

            wait_time = self._smart_timeout.get_last_actual_time()
            logger.info(f"AI Mode detection completed in {wait_time:.1f}s")

            return success
        else:
            return browser.wait_for_ai_mode_complete(timeout_ms=self.AI_MODE_TIMEOUT_MS)

    def _extract_citations_dom_injection(self) -> List[Citation]:
        """
        Extract citations using DOM injection (adapted from original skill).

        This method:
        1. Finds AI Overview container (main-col)
        2. Clicks citation buttons
        3. Extracts links from rhs-col (right sidebar)
        4. Uses smart title extraction (aria-label > title > parent text > hostname)

        Returns:
            List of Citation objects
        """
        browser = self._get_browser()

        selectors_json = json.dumps(CITATION_SELECTORS)

        js_code = f"""
(function() {{
    function isVisible(el) {{
        if (!el) return false;
        const style = window.getComputedStyle(el);
        const rect = el.getBoundingClientRect();
        return style.display !== 'none' &&
               style.visibility !== 'hidden' &&
               style.opacity !== '0' &&
               el.offsetParent !== null &&
               rect.width > 0 &&
               rect.height > 0;
    }}

    function getTitle(el) {{
        if (!el) return '';
        let title = '';

        // 1. Try aria-label (often has site name for Google results)
        const ariaLabel = el.getAttribute('aria-label');
        if (ariaLabel && ariaLabel.trim()) {{
            title = ariaLabel.trim();
            // Clean up common suffixes like "Open in new tab" in various languages
            // Note: Handle both English "." and Chinese "。" periods
            title = title
                .replace(/[。.]\\s*在新标签页中打开[。.]?$/i, '')
                .replace(/[。.]\\s*Open in new tab[。.]?$/i, '')
                .replace(/[。.]\\s*在新窗口中打开[。.]?$/i, '')
                .replace(/[。.]\\s*In neuem Tab öffnen[。.]?$/i, '')
                .replace(/[。.]\\s*Ouvrir dans un nouvel onglet[。.]?$/i, '')
                .replace(/[。.]\\s*Abrir en nueva pestaña[。.]?$/i, '')
                .replace(/[。.]\\s*Apri in nuova scheda[。.]?$/i, '')
                .trim();
        }}

        // 2. Try title attribute
        if (!title) {{
            const titleAttr = el.getAttribute('title');
            if (titleAttr && titleAttr.trim()) {{
                title = titleAttr.trim();
            }}
        }}

        // 3. Try textContent (full text inside element)
        if (!title) {{
            const text = (el.textContent || '').trim();
            if (text && text.length > 0) {{
                title = text;
            }}
        }}

        // 4. Try parent element's text
        if (!title && el.parentElement) {{
            const parentText = (el.parentElement.textContent || '').trim();
            if (parentText && parentText.length > 0) {{
                title = parentText.substring(0, 100);
            }}
        }}

        return title;
    }}

    const mainCol = document.querySelector('[data-container-id="main-col"]');
    if (!mainCol) return JSON.stringify({{ error: 'main-col not found' }});

    const selectors = {selectors_json};
    let buttons = [];

    for (const selector of selectors) {{
        buttons = Array.from(mainCol.querySelectorAll(selector));
        if (buttons.filter(isVisible).length > 0) {{
            break;
        }}
    }}

    const allCitations = [];
    const seen = new Set();
    let markerIndex = 0;

    for (const btn of buttons) {{
        if (!isVisible(btn)) continue;

        const markerId = markerIndex++;
        const marker = document.createElement('span');
        marker.innerHTML = '[CITE-' + markerId + ']';

        if (btn.nextSibling) {{
            btn.parentNode.insertBefore(marker, btn.nextSibling);
        }} else {{
            btn.parentNode.appendChild(marker);
        }}

        try {{
            btn.scrollIntoView({{ behavior: 'instant', block: 'center' }});

            const countVisibleLinks = () => {{
                const rhsCol = document.querySelector('[data-container-id="rhs-col"]');
                if (!rhsCol) return 0;
                return Array.from(rhsCol.querySelectorAll('a[href]')).filter(isVisible).length;
            }};

            const beforeCount = countVisibleLinks();
            btn.click();

            const startTime = Date.now();
            while (Date.now() - startTime < 300) {{
                if (countVisibleLinks() !== beforeCount) break;
            }}
        }} catch (e) {{
            console.warn('Click failed', e);
        }}

        const sources = [];
        const rhsCol = document.querySelector('[data-container-id="rhs-col"]');

        if (rhsCol) {{
            const links = Array.from(rhsCol.querySelectorAll('a[href]'));
            for (const link of links) {{
                if (!isVisible(link)) continue;

                const url = link.href;
                const title = getTitle(link);
                const skipDomains = ['google.com', 'google.de', 'gstatic.com', 'support.google.com'];

                if (url && url.startsWith('http') &&
                    !skipDomains.some(d => url.includes(d)) &&
                    !seen.has(url)) {{
                    seen.add(url);
                    let hostname = '';
                    try {{ hostname = new URL(url).hostname; }} catch(e) {{}}
                    sources.push({{ title: title, url: url, source: hostname }});
                }}
            }}
        }}

        allCitations.push({{ marker_id: markerId, sources: sources }});
    }}

    return JSON.stringify({{
        html: mainCol.innerHTML,
        citations: allCitations
    }});
}})()
""".strip()

        try:
            result = browser.eval_js(js_code)
            if not result:
                logger.warning("DOM injection returned empty result")
                return []

            data = json.loads(result)

            if 'error' in data and data['error']:
                logger.debug(f"DOM injection error: {data['error']}")
                return []

            citations_list = data.get('citations', [])
            if not citations_list:
                logger.debug("No citations from DOM injection")
                return []

            all_citations = []
            for group in citations_list:
                sources = group.get('sources', [])
                for src in sources:
                    url = src.get('url', '')
                    if not self._is_valid_url(url):
                        continue

                    normalized_url = self._normalize_url(url)

                    title = src.get('title', '') or ''
                    source = src.get('source', '') or ''

                    if not title:
                        try:
                            parsed = urlparse(url)
                            title = parsed.netloc or 'Link'
                        except:
                            title = 'Link'

                    all_citations.append(Citation(
                        index=len(all_citations) + 1,
                        url=normalized_url,
                        title=title[:100],
                        context=title[:80],
                        source=source,
                    ))

            logger.info(f"DOM injection extracted {len(all_citations)} citations")
            return all_citations

        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse DOM injection result: {e}")
        except Exception as e:
            logger.warning(f"DOM injection citation extraction failed: {e}")

        return []

    def _extract_citations_fallback(self) -> List[Citation]:
        """
        Fallback: Extract citations from sidebar without clicking buttons.
        Uses improved title extraction.
        """
        browser = self._get_browser()

        js_code = """
(function() {
    function getTitle(el) {
        if (!el) return '';
        let title = '';

        // 1. Try aria-label (often has site name for Google results)
        const ariaLabel = el.getAttribute('aria-label');
        if (ariaLabel && ariaLabel.trim()) {
            title = ariaLabel.trim();
            // Clean up common suffixes like "Open in new tab" in various languages
            // Note: Handle both English "." and Chinese "。" periods
            title = title
                .replace(/[。.]\s*在新标签页中打开[。.]?$/i, '')
                .replace(/[。.]\s*Open in new tab[。.]?$/i, '')
                .replace(/[。.]\s*在新窗口中打开[。.]?$/i, '')
                .replace(/[。.]\s*In neuem Tab öffnen[。.]?$/i, '')
                .replace(/[。.]\s*Ouvrir dans un nouvel onglet[。.]?$/i, '')
                .replace(/[。.]\s*Abrir en nueva pestaña[。.]?$/i, '')
                .replace(/[。.]\s*Apri in nuova scheda[。.]?$/i, '')
                .trim();
        }

        // 2. Try title attribute
        if (!title) {
            const titleAttr = el.getAttribute('title');
            if (titleAttr && titleAttr.trim()) {
                title = titleAttr.trim();
            }
        }

        // 3. Try textContent (full text inside element)
        if (!title) {
            const text = (el.textContent || '').trim();
            if (text && text.length > 0) {
                title = text;
            }
        }

        // 4. Try parent element's text
        if (!title && el.parentElement) {
            const parentText = (el.parentElement.textContent || '').trim();
            if (parentText && parentText.length > 0) {
                title = parentText.substring(0, 100);
            }
        }

        return title;
    }

    const rhsCol = document.querySelector('[data-container-id="rhs-col"]');
    if (!rhsCol) return '[]';

    const links = Array.from(rhsCol.querySelectorAll('a[href]'));
    const seen = new Set();
    const skipDomains = ['google.com', 'google.de', 'gstatic.com', 'support.google.com'];

    const results = [];
    for (const link of links) {
        const url = link.href;
        if (!url || !url.startsWith('http') || seen.has(url)) continue;
        if (skipDomains.some(d => url.includes(d))) continue;

        seen.add(url);
        let hostname = '';
        try { hostname = new URL(url).hostname; } catch(e) {}

        const title = getTitle(link) || hostname;

        results.push({
            title: title.substring(0, 100),
            url: url.split('#')[0].split('?')[0],
            source: hostname
        });
    }

    return JSON.stringify(results);
})()
""".strip()

        try:
            result = browser.eval_js(js_code)
            if not result:
                return []

            links = json.loads(result)
            if not isinstance(links, list):
                return []

            citations = []
            for i, link in enumerate(links):
                url = link.get('url', '')
                if not self._is_valid_url(url):
                    continue

                normalized_url = self._normalize_url(url)

                title = link.get('title', '') or ''
                source = link.get('source', '') or ''

                if not title:
                    title = source or 'Link'

                citations.append(Citation(
                    index=i + 1,
                    url=normalized_url,
                    title=title[:100],
                    context=title[:80],
                    source=source,
                ))

            logger.info(f"Fallback extraction found {len(citations)} citations")
            return citations

        except Exception as e:
            logger.warning(f"Fallback citation extraction failed: {e}")
            return []

    def _extract_ai_overview_html(self) -> str:
        """
        Extract AI Overview HTML content.
        """
        browser = self._get_browser()

        js_code = """
(function() {
    const mainCol = document.querySelector('[data-container-id="main-col"]');
    if (!mainCol) return '';

    const showMoreBtns = Array.from(mainCol.querySelectorAll('[aria-expanded="false"]'));
    for (const btn of showMoreBtns) {
        if (btn.innerText.includes('Show more') ||
            btn.innerText.includes('Mehr anzeigen') ||
            btn.innerText.includes('Meer weergeven')) {
            try { btn.click(); } catch(e) {}
        }
    }

    return mainCol.innerHTML;
})()
""".strip()

        try:
            return browser.eval_js(js_code) or ""
        except Exception as e:
            logger.debug(f"AI Overview HTML extraction failed: {e}")
            return ""

    def _clean_summary(self, html: str) -> str:
        """Clean AI Overview HTML to plain text."""
        if not html:
            return ""

        soup_text = ""

        try:
            from html.parser import HTMLParser

            class TextExtractor(HTMLParser):
                def __init__(self):
                    super().__init__()
                    self.result = []
                    self.skip = False

                def handle_starttag(self, tag, attrs):
                    attrs_dict = dict(attrs)
                    if tag in ('script', 'style', 'nav', 'header', 'footer'):
                        self.skip = True

                def handle_endtag(self, tag):
                    if tag in ('script', 'style', 'nav', 'header', 'footer'):
                        self.skip = False

                def handle_data(self, data):
                    if not self.skip:
                        text = data.strip()
                        if text:
                            self.result.append(text)

            parser = TextExtractor()
            parser.feed(html)
            soup_text = ' '.join(parser.result)

        except Exception as e:
            logger.debug(f"HTML parsing failed: {e}")
            soup_text = re.sub(r'<[^>]+>', ' ', html)

        soup_text = re.sub(r'\s+', ' ', soup_text)
        soup_text = soup_text.replace('==', '')
        soup_text = re.sub(r'!\[[^\]]*\]\(data:image/[^)]+\)', '', soup_text)
        soup_text = re.sub(r'\[\]\([^)]+\)', '', soup_text)

        for marker in CUTOFF_MARKERS:
            if marker in soup_text:
                soup_text = soup_text.split(marker)[0]

        soup_text = re.sub(r'([^\.\!\?\:\;\n])\n+\s*([a-zäöü])', r'\1 \2', soup_text)
        soup_text = re.sub(r'^\s*\.\s*$', '', soup_text, flags=re.MULTILINE)
        soup_text = re.sub(r'\n{3,}', '\n\n', soup_text)

        return soup_text.strip()[:3000]

    def _generate_markdown(self, query: str, summary: str, citations: List[Citation]) -> str:
        """Generate Markdown output"""
        lines = []

        lines.append(f"## {query}\n")

        if summary:
            lines.append(summary)
            lines.append("")

        if citations:
            lines.append("**Sources:**\n")
            for cite in citations:
                context = cite.context or cite.title or f"Source {cite.index}"
                lines.append(f"- [{context}]({cite.url})")

        return "\n".join(lines)

    def search(self, query: str) -> SearchResult:
        """
        Perform Google AI Mode search.

        Phase 5 Enhanced:
        - Check cooling status before search
        - Apply rate limiting (balanced mode: 15-30s)
        - Apply random fingerprint
        - Session restoration
        - CAPTCHA detection
        - 40-second AI Mode timeout

        Args:
            query: Search query

        Returns:
            SearchResult with summary, citations, and Markdown output
        """
        browser = self._get_browser()
        rate_limit_wait = 0.0

        try:
            logger.info(f"Searching for: {query}")

            if self._check_cooling():
                cooling = self._get_cooling_manager()
                status = cooling.check_cooling()
                return SearchResult(
                    query=query,
                    url="",
                    summary="",
                    citations=[],
                    ai_mode_available=False,
                    captcha_detected=True,
                    rate_limit_wait=0.0,
                    error_message=f"In cooling period: {status.message}",
                    markdown_output=f"## {query}\n\n**In Cooling Period**\n\n{status.message}\n\nPlease wait before trying again.",
                )

            rate_limit_wait = self._apply_rate_limiting()

            self._restore_session()

            browser.set_local_state()

            self._apply_fingerprint()

            search_url = self._build_search_url(query)
            browser.open(search_url)

            captcha_result = self._check_captcha()
            if captcha_result.is_captcha:
                logger.error(f"CAPTCHA detected: {captcha_result.message}")
                logger.error(f"  Reason: {captcha_result.reason}")
                logger.error(f"  Layer: {captcha_result.layer}")

                if self._enable_cooling:
                    cooling_result = self._get_cooling_manager().notify_captcha()
                    logger.warning(f"  Cooling: {cooling_result.wait_minutes} minutes cooldown")
                    logger.warning(f"  Message: {cooling_result.message}")

                page_info = self._get_captcha_handler().get_page_info()
                logger.error(f"  Page URL: {page_info.get('url', 'N/A')[:80]}")

                error_msg = f"CAPTCHA detected: {captcha_result.reason}. "
                if self._enable_cooling:
                    error_msg += f"Cooldown: {cooling_result.wait_minutes} minutes. "

                return SearchResult(
                    query=query,
                    url=browser.get_url(),
                    summary="",
                    citations=[],
                    ai_mode_available=False,
                    captcha_detected=True,
                    rate_limit_wait=rate_limit_wait,
                    error_message=error_msg + "Please solve the CAPTCHA in the browser and try again.",
                    markdown_output=f"## {query}\n\n**CAPTCHA Required**\n\n{captcha_result.reason}\n\n{cooling_result.message if self._enable_cooling else 'Please manually solve the CAPTCHA in the browser, then try again.'}",
                )

            browser.wait_for_network_idle(timeout_ms=10000)

            ai_available, error_msg = self._check_ai_mode_available()
            if not ai_available:
                logger.warning(f"AI Mode not available: {error_msg}")
                return SearchResult(
                    query=query,
                    url=browser.get_url(),
                    summary="",
                    citations=[],
                    ai_mode_available=False,
                    captcha_detected=False,
                    rate_limit_wait=rate_limit_wait,
                    error_message=error_msg or "AI Mode is not available in your country or language.",
                    markdown_output=f"## {query}\n\n**AI Mode is not available in your country or language.**\n\nTry using a VPN or proxy to access from a supported region.",
                )

            logger.info("Waiting for AI Mode to complete (40s timeout)...")
            ai_complete = self._wait_for_ai_mode_complete()

            if not ai_complete:
                logger.warning("AI Mode detection timeout, proceeding anyway")

            html = self._extract_ai_overview_html()
            summary = self._clean_summary(html)

            citations = self._extract_citations_dom_injection()

            if not citations:
                logger.debug("DOM injection found no citations, trying fallback")
                citations = self._extract_citations_fallback()

            if self._enable_citation_cleaning and self._citation_cleaner:
                citations = self._clean_citations(citations)

            self._save_session()
            browser.save_cookies()

            if self._smart_rate_limiter:
                self._smart_rate_limiter.record_search()
            else:
                self._get_rate_limiter().record_search()

            markdown_output = self._generate_markdown(query, summary, citations)

            result = SearchResult(
                query=query,
                url=browser.get_url(),
                summary=summary,
                citations=citations,
                markdown_output=markdown_output,
                ai_mode_available=True,
                captcha_detected=False,
                rate_limit_wait=rate_limit_wait,
            )

            if self._smart_rate_limiter:
                adjustment = self._smart_rate_limiter.adjust_based_on_result(result)
                if adjustment.adjusted:
                    logger.info(f"Rate limit adjusted: {adjustment.reason}")

            logger.info(f"Search complete: {len(citations)} citations found")
            return result

        except BrowserNotRunningError as e:
            raise SearchError(f"Browser error: {e}") from e
        except Exception as e:
            logger.error(f"Search failed: {e}")
            raise SearchError(f"Search failed: {e}") from e

    def close(self):
        """Close the browser if owned by this instance"""
        if self._browser:
            try:
                self._save_session()
                if self._owns_chrome:
                    self._browser.stop_stealth_chrome()
                else:
                    self._browser.close()
            except Exception as e:
                logger.debug(f"Error closing browser: {e}")
            finally:
                self._browser = None
                self._owns_chrome = False

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
        return False


def main():
    """Demo usage"""
    query = "What is the capital of France?"

    with SearchEngine() as engine:
        result = engine.search(query)
        print(result.markdown_output)


if __name__ == "__main__":
    main()
