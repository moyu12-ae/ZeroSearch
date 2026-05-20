"""
浏览器上下文管理器 — 冷启动状态机

对齐 Architecture v2 §2.1 BrowserEngine。
状态机: COLD → WARMING → READY → STALE → DEAD
"""

import time
from enum import Enum, auto
from pathlib import Path
from typing import Optional

from .browser_factory import BrowserFactory, BrowserLaunchError
from .profile_manager import ProfileManager


class BrowserState(Enum):
    COLD = auto()      # 无浏览器进程
    WARMING = auto()   # 浏览器启动中
    READY = auto()     # 浏览器就绪，可接受请求
    STALE = auto()     # 连接超时/无响应
    DEAD = auto()      # 进程崩溃


class BrowserContext:
    """浏览器实例上下文

    持有 Patchright Chromium 进程引用、Page 对象、状态机逻辑。
    向上层 SearchEngine 暴露统一的 get_context() / navigate() / shutdown() 接口。
    """

    IDLE_TIMEOUT = 300  # 5 分钟闲置视为 STALE

    def __init__(
        self,
        headless: bool = False,  # v0.2: 默认有头
        profile_dir: Optional[Path] = None,
    ):
        self._state = BrowserState.COLD
        self._factory = BrowserFactory(headless=headless, profile_dir=profile_dir)
        self._context = None
        self._last_used: float = 0.0

    # ── Public API ──────────────────────────────────────────

    @property
    def state(self) -> BrowserState:
        return self._state

    @property
    def profile(self) -> ProfileManager:
        return self._factory.profile

    def get_context(self):
        """获取就绪的浏览器上下文。首次调用启动 Chrome，后续复用。

        Returns:
            Patchright BrowserContext
        """
        if self._state == BrowserState.READY:
            if self._health_check():
                self._last_used = time.time()
                return self._context
            else:
                self._state = BrowserState.STALE

        if self._state == BrowserState.STALE:
            if self._try_reconnect():
                self._state = BrowserState.READY
                self._last_used = time.time()
                return self._context
            else:
                self._state = BrowserState.COLD

        if self._state == BrowserState.DEAD:
            self._cleanup()
            self._state = BrowserState.COLD

        return self._cold_start()

    def navigate(self, url: str) -> None:
        """导航到目标 URL"""
        self._factory.navigate(url)

    def shutdown(self) -> None:
        """优雅关闭浏览器，释放资源"""
        self._factory.close()
        self._state = BrowserState.DEAD

    def health_check(self) -> dict:
        """检查浏览器健康状态

        Returns:
            {status: str, state: str, uptime_seconds: float}
        """
        status = "healthy" if self._health_check() else "unhealthy"
        return {
            "status": status,
            "state": self._state.name,
            "uptime_seconds": (
                time.time() - self._last_used if self._last_used else 0
            ),
        }

    # ── Internal ────────────────────────────────────────────

    def _health_check(self) -> bool:
        """检查浏览器连接是否存活"""
        try:
            if self._context is None:
                return False
            _ = self._context.pages
            return True
        except Exception:
            return False

    def _try_reconnect(self) -> bool:
        """尝试重新连接已存在的浏览器上下文"""
        try:
            _ = self._context.pages
            return True
        except Exception:
            return False

    def _cold_start(self):
        """COLD → WARMING → READY"""
        self._state = BrowserState.WARMING
        try:
            self._context = self._factory.get_context()
            self._last_used = time.time()
            self._state = BrowserState.READY
            return self._context
        except BrowserLaunchError:
            self._state = BrowserState.COLD
            raise

    def _cleanup(self) -> None:
        """清理残留资源"""
        self._context = None
