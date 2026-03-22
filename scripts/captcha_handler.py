"""
CAPTCHA Handler - 3-Layer CAPTCHA Detection (Phase 5)
Based on original Google AI Mode Skill implementation

Features:
- Layer 1: URL contains /sorry/index
- Layer 2: Body text contains "unusual traffic"
- Layer 3: Page content is very short (< 600 chars)

Usage:
    # With browser instance
    from captcha_handler import CaptchaHandler
    handler = CaptchaHandler(browser)
    result = handler.detect()

    # Static detection (for testing)
    from captcha_handler import AntiBotDetector
    result = AntiBotDetector.detect_static(url, body_text)
"""

import logging
import re
from dataclasses import dataclass, field
from typing import Optional, Tuple, List, Dict, Any
from dataclasses import asdict

logger = logging.getLogger(__name__)


@dataclass
class CaptchaResult:
    """Result of CAPTCHA detection"""
    is_captcha: bool = False
    reason: str = ""
    layer: int = 0
    message: str = ""
    url: str = ""
    body_length: int = 0
    confidence: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return asdict(self)

    def __str__(self) -> str:
        if self.is_captcha:
            return f"CAPTCHA detected (Layer {self.layer}): {self.reason}"
        return "No CAPTCHA detected"


class AntiBotDetector:
    """
    Anti-Bot Detection (Static Version)

    Can be used without browser instance for testing and analysis.
    """

    UNUSUAL_TRAFFIC_PATTERNS: List[str] = [
        r'unusual\s*traffic',
        r'ungewöhnlichen\s*datenverkehr',
        r'our\s*systems\s*have\s*detected',
        r'我们的系统检测到',
        r'异常流量',
        r'not\s*a\s*robot',
        r'不是\s*机器人',
        r'captcha',
        r'验证码',
    ]

    SORRY_URL_PATTERNS: List[str] = [
        r'/sorry/',
        r'/sorry/index',
        r'google\.com/sorry',
        r'ipv[46]\.google\.[^/]+/sorry',
    ]

    SHORT_PAGE_THRESHOLD: int = 600
    SUSPICIOUS_PAGE_THRESHOLD: int = 1000

    @classmethod
    def detect_url(cls, url: str) -> Tuple[bool, str, int]:
        """
        Layer 1: Check if URL indicates CAPTCHA/sorry page

        Args:
            url: Current page URL

        Returns:
            Tuple of (is_captcha, reason, layer)
        """
        if not url:
            return False, "", 0

        url_lower = url.lower()
        for pattern in cls.SORRY_URL_PATTERNS:
            if re.search(pattern, url_lower, re.IGNORECASE):
                logger.warning(f"CAPTCHA detected (Layer 1: URL contains /sorry/)")
                return True, "URL contains /sorry/ - CAPTCHA page detected", 1

        return False, "", 0

    @classmethod
    def detect_text(cls, text: str) -> Tuple[bool, str, int]:
        """
        Layer 2: Check if text contains unusual traffic indicators

        Args:
            text: Page body text

        Returns:
            Tuple of (is_captcha, reason, layer)
        """
        if not text:
            return False, "", 0

        text_lower = text.lower()
        for pattern in cls.UNUSUAL_TRAFFIC_PATTERNS:
            if re.search(pattern, text_lower, re.IGNORECASE):
                logger.warning(f"CAPTCHA detected (Layer 2: Text contains unusual traffic pattern)")
                return True, f"Body text contains '{pattern}' - CAPTCHA detected", 2

        return False, "", 0

    @classmethod
    def detect_length(cls, text: str, threshold: int = None) -> Tuple[bool, str, int]:
        """
        Layer 3: Check if page content is suspiciously short

        Args:
            text: Page body text
            threshold: Custom threshold (default: SHORT_PAGE_THRESHOLD)

        Returns:
            Tuple of (is_captcha, reason, layer)
        """
        if threshold is None:
            threshold = cls.SHORT_PAGE_THRESHOLD

        if not text:
            return True, "Empty page content", 3

        text_stripped = text.strip()
        length = len(text_stripped)

        if length < threshold:
            logger.warning(f"CAPTCHA detected (Layer 3: Page too short - {length} chars)")
            return True, f"Page content too short ({length} chars < {threshold}) - likely CAPTCHA", 3

        return False, "", 0

    @classmethod
    def detect_static(cls, url: str = "", body_text: str = "") -> CaptchaResult:
        """
        Run all detection layers on static content (no browser required)

        Args:
            url: Page URL (optional)
            body_text: Page body text (optional)

        Returns:
            CaptchaResult with detection details
        """
        url = url or ""
        body_text = body_text or ""
        body_length = len(body_text.strip())

        is_captcha, reason, layer = cls.detect_url(url)
        if is_captcha:
            return CaptchaResult(
                is_captcha=True,
                reason=reason,
                layer=layer,
                message="CAPTCHA detected via URL check",
                url=url,
                body_length=body_length,
                confidence=0.95
            )

        is_captcha, reason, layer = cls.detect_text(body_text)
        if is_captcha:
            return CaptchaResult(
                is_captcha=True,
                reason=reason,
                layer=layer,
                message="CAPTCHA detected via text analysis",
                url=url,
                body_length=body_length,
                confidence=0.90
            )

        is_captcha, reason, layer = cls.detect_length(body_text)
        if is_captcha:
            return CaptchaResult(
                is_captcha=True,
                reason=reason,
                layer=layer,
                message="CAPTCHA detected via page length analysis",
                url=url,
                body_length=body_length,
                confidence=0.75
            )

        return CaptchaResult(
            is_captcha=False,
            reason="",
            layer=0,
            message="No CAPTCHA detected",
            url=url,
            body_length=body_length,
            confidence=1.0
        )


class CaptchaHandler:
    """
    3-Layer CAPTCHA Detection Handler

    Layer 1: URL contains /sorry/index (Most reliable!)
    Layer 2: Text contains "unusual traffic"
    Layer 3: Page content is very short (< 600 chars)
    """

    UNUSUAL_TRAFFIC_INDICATORS = [
        'unusual traffic',
        'ungewöhnlichen datenverkehr',
        'unsere systeme haben',
        'our systems have detected',
        '我们的系统检测到',
        '异常流量',
    ]

    CAPTCHA_SELECTORS = [
        'div#recaptcha',
        'iframe[src*="recaptcha"]',
        '[id*="captcha"]',
    ]

    def __init__(self, browser):
        """
        Initialize CAPTCHA handler

        Args:
            browser: BrowserManager instance
        """
        self._browser = browser

    def detect_url(self) -> Tuple[bool, str]:
        """
        Layer 1: Check if URL contains /sorry/index

        Google's CAPTCHA pages always redirect to /sorry/index

        Returns:
            Tuple of (is_captcha, reason)
        """
        try:
            current_url = self._browser.get_url()
            if '/sorry/index' in current_url or 'google.com/sorry' in current_url:
                logger.warning(f"CAPTCHA detected (Layer 1: URL contains /sorry/index)")
                return True, "URL contains /sorry/index - CAPTCHA page detected"
        except Exception as e:
            logger.debug(f"URL check failed: {e}")

        return False, ""

    def detect_text(self) -> Tuple[bool, str]:
        """
        Layer 2: Check if body text contains unusual traffic indicators

        CAPTCHA pages contain specific text patterns

        Returns:
            Tuple of (is_captcha, reason)
        """
        try:
            body_text = self._browser.eval_js_simple('document.body.innerText') or ''
            body_lower = body_text.lower()

            for indicator in self.UNUSUAL_TRAFFIC_INDICATORS:
                if indicator.lower() in body_lower:
                    logger.warning(f"CAPTCHA detected (Layer 2: Text contains '{indicator}')")
                    return True, f"Body text contains '{indicator}' - CAPTCHA detected"
        except Exception as e:
            logger.debug(f"Text check failed: {e}")

        return False, ""

    def detect_length(self) -> Tuple[bool, str]:
        """
        Layer 3: Check if page content is very short

        CAPTCHA pages are very short (< 600 chars)
        Real AI Overview pages are much longer (usually > 2000 chars)

        Returns:
            Tuple of (is_captcha, reason)
        """
        try:
            body_text = self._browser.eval_js_simple('document.body.innerText') or ''
            body_length = len(body_text.strip())

            if body_length < 600:
                body_lower = body_text.lower()
                if any(ind.lower() in body_lower for ind in self.UNUSUAL_TRAFFIC_INDICATORS):
                    logger.warning(f"CAPTCHA detected (Layer 3: Page too short - {body_length} chars)")
                    return True, f"Page too short ({body_length} chars) - likely CAPTCHA"

        except Exception as e:
            logger.debug(f"Length check failed: {e}")

        return False, ""

    def detect_element(self) -> Tuple[bool, str]:
        """
        Layer 4 (Legacy): Check for CAPTCHA elements

        Less reliable but catches some edge cases

        Returns:
            Tuple of (is_captcha, reason)
        """
        try:
            for selector in self.CAPTCHA_SELECTORS:
                js_code = f'document.querySelector("{selector}") !== null'
                result = self._browser.eval_js_simple(js_code)
                if result and result.lower() == 'true':
                    logger.warning(f"CAPTCHA detected (Legacy: Element {selector} found)")
                    return True, f"CAPTCHA element found: {selector}"
        except Exception as e:
            logger.debug(f"Element check failed: {e}")

        return False, ""

    def detect(self) -> CaptchaResult:
        """
        Run all 3 layers of CAPTCHA detection

        Returns:
            CaptchaResult with detection details
        """
        is_captcha, reason = self.detect_url()
        if is_captcha:
            return CaptchaResult(
                is_captcha=True,
                reason=reason,
                layer=1,
                message="CAPTCHA detected via URL check"
            )

        is_captcha, reason = self.detect_text()
        if is_captcha:
            return CaptchaResult(
                is_captcha=True,
                reason=reason,
                layer=2,
                message="CAPTCHA detected via text analysis"
            )

        is_captcha, reason = self.detect_length()
        if is_captcha:
            return CaptchaResult(
                is_captcha=True,
                reason=reason,
                layer=3,
                message="CAPTCHA detected via page length analysis"
            )

        is_captcha, reason = self.detect_element()
        if is_captcha:
            return CaptchaResult(
                is_captcha=True,
                reason=reason,
                layer=4,
                message="CAPTCHA detected via element check"
            )

        return CaptchaResult(
            is_captcha=False,
            reason="",
            layer=0,
            message="No CAPTCHA detected"
        )

    def is_sorry_page(self) -> bool:
        """
        Quick check if current page is a sorry/CAPTCHA page

        Returns:
            True if page is sorry/CAPTCHA page
        """
        is_captcha, _ = self.detect_url()
        return is_captcha

    def get_page_info(self) -> dict:
        """
        Get detailed page information for debugging

        Returns:
            Dict with page details
        """
        try:
            url = self._browser.get_url()
            title = self._browser.get_title()
            body_text = self._browser.eval_js_simple('document.body.innerText') or ''

            return {
                'url': url,
                'title': title,
                'body_length': len(body_text),
                'body_preview': body_text[:500] if body_text else '',
                'is_sorry_url': '/sorry/' in url,
                'has_unusual_traffic': any(ind in body_text.lower() for ind in self.UNUSUAL_TRAFFIC_INDICATORS),
            }
        except Exception as e:
            logger.error(f"Failed to get page info: {e}")
            return {}


def create_captcha_handler(browser) -> CaptchaHandler:
    """
    Factory function to create CAPTCHA handler

    Args:
        browser: BrowserManager instance

    Returns:
        CaptchaHandler instance
    """
    return CaptchaHandler(browser)


def demo():
    """演示 AntiBotDetector 的使用"""
    print("=" * 60)
    print("AntiBotDetector 演示 (Phase 5)")
    print("=" * 60)

    detector = AntiBotDetector

    print("\n1. 测试正常 Google 搜索页面:")
    normal_url = "https://www.google.com/search?q=Python"
    normal_text = """
    Python is a high-level, general-purpose programming language. Its design philosophy emphasizes
    code readability with the use of significant indentation. Python is dynamically typed and
    garbage-collected. It supports multiple programming paradigms, including structured,
    procedural, reflective, and object-oriented programming.
    Python consistently ranks among the most popular programming languages.
    The Python Package Index (PyPI) hosts thousands of third-party modules.
    """
    result = detector.detect_static(normal_url, normal_text)
    print(f"   URL: {normal_url}")
    print(f"   Body Length: {len(normal_text.strip())} chars")
    print(f"   Result: {result}")

    print("\n2. 测试 CAPTCHA 页面 (URL 检测):")
    captcha_url = "https://www.google.com/sorry/index?continue=https://www.google.com/search"
    captcha_text = "我们的系统检测到您的计算机网络中存在异常流量"
    result = detector.detect_static(captcha_url, captcha_text)
    print(f"   URL: {captcha_url}")
    print(f"   Body Length: {len(captcha_text)} chars")
    print(f"   Result: {result}")

    print("\n3. 测试短页面检测:")
    short_url = "https://www.google.com/search?q=test"
    short_text = "Error"
    result = detector.detect_static(short_url, short_text)
    print(f"   URL: {short_url}")
    print(f"   Body Length: {len(short_text)} chars")
    print(f"   Result: {result}")

    print("\n4. 测试各种检测模式:")
    test_cases = [
        ("正常URL", "https://www.google.com/search?q=test", ""),
        ("Sorry URL", "https://www.google.com/sorry/", ""),
        ("异常流量文本", "", "我们的系统检测到您的计算机网络中存在异常流量"),
        ("短文本", "", "Error"),
    ]

    for name, url, text in test_cases:
        result = detector.detect_static(url, text)
        status = "🚫 CAPTCHA" if result.is_captcha else "✅ 正常"
        print(f"   [{status}] {name}: Layer {result.layer} - {result.reason[:50]}...")

    print("\n✅ AntiBotDetector 演示完成!")


if __name__ == "__main__":
    demo()
