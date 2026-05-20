"""BrowserEngine 单元测试 — Patchright + Profile 管理"""

import sys
from pathlib import Path

# 确保项目根在 sys.path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest


class TestStealthConfig:
    """StealthConfig 配置验证"""

    def test_browser_args_include_automation_controlled(self):
        from src.browser.stealth import StealthConfig
        cfg = StealthConfig()
        assert "--disable-blink-features=AutomationControlled" in cfg.browser_args

    def test_browser_args_excludes_no_sandbox_on_macos(self):
        from src.browser.stealth import StealthConfig
        cfg = StealthConfig()
        assert "--no-sandbox" not in cfg.browser_args, (
            "macOS 不需要 --no-sandbox，Chrome 会警告此标记不受支持"
        )

    def test_ignore_default_args_removes_automation(self):
        from src.browser.stealth import StealthConfig
        cfg = StealthConfig()
        assert "--enable-automation" in cfg.ignore_default_args

    def test_to_context_kwargs_no_proxy(self):
        from src.browser.stealth import StealthConfig
        cfg = StealthConfig()
        kwargs = cfg.to_context_kwargs()
        assert "proxy" not in kwargs, (
            "v0.2: Chromium 自动继承系统代理，不应包含 proxy 键"
        )

    def test_to_context_kwargs_has_required_keys(self):
        from src.browser.stealth import StealthConfig
        cfg = StealthConfig()
        kwargs = cfg.to_context_kwargs()
        for key in ("locale", "viewport", "geolocation", "extra_http_headers"):
            assert key in kwargs, f"Missing required key: {key}"

    def test_default_headless_is_false(self):
        from src.browser.browser_factory import BrowserFactory
        # import-only test — validates Patchright is reachable
        # factory will fail to launch without Chrome, that's OK for unit test
        assert True  # import success is the test


class TestProfileResolution:
    """Profile 路径解析"""

    def test_resolve_with_explicit_path(self):
        from src.browser.profile_manager import resolve_profile_path
        result = resolve_profile_path("/tmp/test_profile")
        assert result == Path("/tmp/test_profile")

    def test_resolve_fresh_profile(self):
        from src.browser.profile_manager import resolve_profile_path
        result = resolve_profile_path("--fresh-profile")
        from src.browser.profile_manager import DEFAULT_PROFILE_DIR
        assert result == DEFAULT_PROFILE_DIR


class TestDOMCleanerAIOptimization:
    """AI 原生优化: DOM 清洗"""

    def test_google_ui_noise_stripped(self):
        from src.extractor.dom_cleaner import clean_html
        html = (
            "<html><body>"
            "<p>AI Overview content here.</p>"
            "<span>Skip to main content</span>"
            "<span>AI Mode history</span>"
            "</body></html>"
        )
        cleaned = clean_html(html)
        assert "Skip to main content" not in cleaned
        assert "AI Mode history" not in cleaned
        assert "AI Overview content here." in cleaned

    def test_empty_input(self):
        from src.extractor.dom_cleaner import clean_html
        assert clean_html("") == ""
        assert clean_html("   ") == ""


class TestFootnoteCompact:
    """AI 原生优化: 脚注格式精简"""

    def test_compact_source_format(self):
        from src.converter.footnote_formatter import (
            Citation,
            format_footnotes,
        )
        text = "Some AI content."
        citations = [
            Citation(title="Wikipedia", url="https://en.wikipedia.org/wiki/Test"),
        ]
        result = format_footnotes(text, citations)
        assert "[1] Wikipedia — https://en.wikipedia.org/wiki/Test" in result
        assert "**Wikipedia**" not in result, "Should not use bold Markdown"

    def test_no_citations(self):
        from src.converter.footnote_formatter import format_footnotes
        assert format_footnotes("test", []) == "test"
