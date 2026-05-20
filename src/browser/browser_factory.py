"""
BrowserFactory — Patchright 浏览器实例工厂

使用 Patchright (undetected Chromium) 替代 Camoufox。
接口对齐 Architecture v2 §2.1 BrowserEngine 操作契约。
"""

import subprocess
import time
import json
from pathlib import Path
from typing import Optional

_PATCHRIGHT_AVAILABLE = False
try:
    from patchright.sync_api import sync_playwright, BrowserContext, Page
    _PATCHRIGHT_AVAILABLE = True
except ImportError:
    sync_playwright = None
    BrowserContext = None
    Page = None

from .profile_manager import ProfileManager, DEFAULT_PROFILE_DIR
from .stealth import StealthConfig


class BrowserLaunchError(Exception):
    """浏览器启动失败"""

    def __init__(self, message: str, exit_code: int = 1):
        super().__init__(message)
        self.exit_code = exit_code


class BrowserFactory:
    """Patchright 浏览器实例工厂

    使用 Playwright sync_api + Patchright chromium.launch_persistent_context。
    默认有头模式（可见窗口），通过 Chromium 自动继承系统代理。
    """

    def __init__(
        self,
        headless: bool = False,  # v0.2: 默认有头
        profile_dir: Optional[Path] = None,
    ):
        if not _PATCHRIGHT_AVAILABLE:
            raise BrowserLaunchError(
                "Patchright not found. Run: pip install patchright"
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
        """获取浏览器上下文。首次调用启动 Chrome，后续复用。

        Returns:
            Patchright BrowserContext（底层为真 Chrome）
        """
        if self._context is not None:
            try:
                _ = self._context.pages
                return self._context
            except Exception:
                self._context = None

        try:
            profile_path = self._profile.ensure_profile()

            # 写入英文语言偏好 (借鉴原版 google-ai-mode-skill)
            self._write_language_prefs(profile_path)

            # Option A: 使用真实 Chrome Profile → 自动关闭正在运行的 Chrome
            self._auto_close_chrome(profile_path)

            self._playwright = sync_playwright().start()

            launch_kwargs = {
                "channel": "chrome",
                "headless": self._headless,
                "user_data_dir": str(profile_path),
                "args": self._stealth.browser_args,
                "ignore_default_args": self._stealth.ignore_default_args,
                "no_viewport": False,
                "accept_downloads": False,
            }
            launch_kwargs.update(self._stealth.to_context_kwargs())

            self._context = self._playwright.chromium.launch_persistent_context(
                **launch_kwargs
            )
            return self._context
        except Exception as e:
            # Chrome Profile 锁定检测
            msg = str(e).lower()
            if "profile" in msg and ("lock" in msg or "use" in msg or "already" in msg):
                raise BrowserLaunchError(
                    "Chrome Profile 已被锁定。请先关闭所有 Chrome 窗口，"
                    "或使用 --fresh-profile 切换到独立 Profile。",
                    exit_code=5,
                ) from e
            raise BrowserLaunchError(
                f"Failed to launch Chrome browser: {e}"
            ) from e

    @staticmethod
    def _auto_close_chrome(profile_path: Path) -> None:
        """若使用真实 Chrome Profile，自动关闭正在运行的 Chrome。

        真实 Chrome Profile 不能被两个进程同时使用。
        macOS 通过 osascript 发送 quit 命令优雅退出。
        """
        import sys
        from pathlib import Path as _Path

        # 仅对真实 Chrome Profile 执行（路径包含 "Application Support/Google/Chrome"）
        chrome_app_path = _Path.home() / "Library" / "Application Support" / "Google" / "Chrome"
        try:
            if profile_path.resolve() != chrome_app_path.resolve():
                return  # 不是真实 Chrome Profile，无须关闭
        except OSError:
            return

        # 检测 Chrome 是否正在运行
        try:
            result = subprocess.run(
                ["pgrep", "-x", "Google Chrome"],
                capture_output=True, text=True, timeout=5,
            )
            if result.returncode != 0:
                return  # Chrome 未运行
        except Exception:
            return

        print(
            "⚠️  检测到 Chrome 正在运行，正在自动关闭...",
            file=sys.stderr,
        )
        try:
            subprocess.run(
                ["osascript", "-e", 'quit app "Google Chrome"'],
                capture_output=True, text=True, timeout=15,
            )
            # 等待 Chrome 完全退出（释放 Profile 锁）
            time.sleep(2)
            print("    Chrome 已关闭，继续启动搜索...", file=sys.stderr)
        except Exception:
            print(
                "    ⚠️  无法自动关闭 Chrome，请手动关闭后重试。",
                file=sys.stderr,
            )

    def _write_language_prefs(self, profile_path: Path) -> None:
        """写入英文语言偏好到 Chrome Profile。

        借鉴原版 google-ai-mode-skill 的做法：
        1. 写入 "Local State" 文件（app_locale + accept_languages）
        2. 写入 "Default/Preferences" 文件（详细语言配置）
        """
        # 1. Local State
        local_state_path = profile_path / "Local State"
        local_state = {}
        if local_state_path.exists():
            try:
                local_state = json.loads(local_state_path.read_text())
            except (json.JSONDecodeError, IOError):
                pass
        local_state.setdefault("app_locale", "en")
        local_state.setdefault("accept_languages", "en-US,en")
        try:
            local_state_path.write_text(json.dumps(local_state, indent=2))
        except (IOError, OSError):
            pass

        # 2. Default/Preferences
        default_dir = profile_path / "Default"
        default_dir.mkdir(parents=True, exist_ok=True)
        prefs_path = default_dir / "Preferences"
        prefs = {}
        if prefs_path.exists():
            try:
                prefs = json.loads(prefs_path.read_text())
            except (json.JSONDecodeError, IOError):
                pass
        prefs.setdefault("accept_languages", "en-US,en")
        prefs.setdefault("selected_languages", "en-US,en")
        prefs.setdefault("intl", {}).setdefault("accept_languages", "en-US,en")
        prefs.setdefault("intl", {}).setdefault("selected_languages", "en-US,en")
        prefs.setdefault("translate", {}).setdefault("enabled", False)
        try:
            prefs_path.write_text(json.dumps(prefs, indent=2))
        except (IOError, OSError):
            pass

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
