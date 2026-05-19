"""
BrowserFactory — Camoufox 浏览器实例工厂

使用 Camoufox (Firefox) 引擎替代原 Patchright。
接口对齐 browser-engine.md §6.1 操作契约。
"""

import os
from contextlib import redirect_stderr
from pathlib import Path
from typing import Optional

_CAMOUFOX_AVAILABLE = False
try:
    from playwright.sync_api import sync_playwright, BrowserContext, Page
    from camoufox.sync_api import NewBrowser
    _CAMOUFOX_AVAILABLE = True
except ImportError:
    sync_playwright = None
    NewBrowser = None
    BrowserContext = None
    Page = None

from .profile_manager import ProfileManager, DEFAULT_PROFILE_DIR
from .stealth import StealthConfig


class BrowserLaunchError(Exception):
    """浏览器启动失败"""


class BrowserFactory:
    """Camoufox 浏览器实例工厂

    使用 Playwright sync_api + Camoufox NewBrowser 启动 Firefox，
    提供持久化 Profile 支持。
    """

    def __init__(
        self,
        headless: bool = True,
        profile_dir: Optional[Path] = None,
    ):
        if not _CAMOUFOX_AVAILABLE:
            raise BrowserLaunchError(
                "Camoufox not found. Run: git submodule update --init"
            )
        self._headless = headless
        self._profile = ProfileManager(profile_dir)
        self._stealth = StealthConfig()
        self._playwright = None
        self._context: Optional[BrowserContext] = None

    @property
    def profile(self) -> ProfileManager:
        return self._profile

    def get_context(self) -> BrowserContext:
        """获取浏览器上下文。首次调用启动 Firefox，后续复用。

        Returns:
            Camoufox BrowserContext（底层为 Firefox 浏览器）
        """
        if self._context is not None:
            try:
                _ = self._context.pages
                return self._context
            except Exception:
                self._context = None

        try:
            profile_path = self._profile.ensure_profile()

            self._playwright = sync_playwright().start()
            with open(os.devnull, 'w') as devnull, redirect_stderr(devnull):
                self._context = NewBrowser(
                    self._playwright,
                    headless=self._headless,
                    persistent_context=True,
                    user_data_dir=str(profile_path),
                    **self._stealth.to_context_kwargs(),
                )
            return self._context
        except Exception as e:
            raise BrowserLaunchError(
                f"Failed to launch Camoufox browser: {e}"
            ) from e

    def navigate(self, url: str) -> None:
        """导航到目标 URL

        Args:
            url: 目标 URL（如 Google AI Mode 搜索页）
        """
        ctx = self.get_context()
        page = ctx.pages[0] if ctx.pages else ctx.new_page()
        page.goto(url, wait_until="domcontentloaded", timeout=15000)

    def close(self) -> None:
        """关闭浏览器上下文和 Playwright 实例"""
        if self._context:
            try:
                self._context.close()
            except Exception:
                pass
            self._context = None
        if self._playwright:
            try:
                self._playwright.stop()
            except Exception:
                pass
            self._playwright = None
