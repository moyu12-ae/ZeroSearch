"""
BrowserFactory — Patchright 浏览器实例工厂

使用 Patchright (undetected Chromium) 替代 Camoufox。
接口对齐 Architecture v2 §2.1 BrowserEngine 操作契约。

v0.3: 新增 Daemon 方法 — launch_daemon(), connect_to_daemon(), cleanup_daemon()
"""

from __future__ import annotations

import json
import os
import socket
import subprocess
import sys
import time
import urllib.request
from pathlib import Path
from typing import Optional

from src.utils.platform import kill_process, kill_process_tree, get_pid_on_port, get_cache_dir

_PATCHRIGHT_AVAILABLE = False
try:
    from patchright.sync_api import sync_playwright, Browser, BrowserContext, Page
    _PATCHRIGHT_AVAILABLE = True
except ImportError:
    sync_playwright = None
    Browser = None
    BrowserContext = None
    Page = None

from .profile_manager import ProfileManager, DEFAULT_PROFILE_DIR
from .stealth import StealthConfig
from .daemon_state import (
    DAEMON_STATE_PATH,
    read_state,
    is_pid_alive,
    is_cdp_responsive,
    cleanup_stale,
    remove_state,
)


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

            self._playwright = sync_playwright().start()

            launch_kwargs = {
                "channel": "chrome",
                "headless": self._headless,
                "user_data_dir": str(profile_path),
                "args": self._stealth.browser_args,
                "ignore_default_args": self._stealth.ignore_default_args,
                "no_viewport": True,   # Patchright 推荐：不强制 viewport
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
        """关闭浏览器上下文和 Playwright 实例 (v0.2 兼容)"""
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

    # ── v0.3 Daemon 方法 ──────────────────────────────────────────

    @staticmethod
    def _find_free_port(start: int = 9222, end: int = 9232) -> int:
        """扫描空闲 TCP 端口"""
        for port in range(start, end + 1):
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                try:
                    s.bind(("127.0.0.1", port))
                    return port
                except OSError:
                    continue
        raise BrowserLaunchError(
            f"No free port in range {start}-{end}",
            exit_code=1,
        )

    @staticmethod
    def _wait_for_cdp(port: int, timeout: float = 15.0) -> None:
        """轮询等待 CDP 端点就绪"""
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            try:
                url = f"http://127.0.0.1:{port}/json/version"
                req = urllib.request.Request(url)
                with urllib.request.urlopen(req, timeout=2) as resp:
                    if resp.status == 200:
                        return
            except Exception:
                pass
            time.sleep(0.5)
        raise BrowserLaunchError(
            f"CDP endpoint not ready on port {port} after {timeout}s",
            exit_code=1,
        )

    @staticmethod
    def _find_and_recover_orphan() -> tuple[int, str] | None:
        """扫描端口范围，查找孤儿 Chrome 进程并尝试恢复。

        当 daemon_runner 崩溃但 Chrome 仍存活时（start_new_session=True），
        状态文件可能丢失或损坏。此方法扫描已知端口范围，检测是否有可恢复的
        Chrome 实例。

        找到可恢复实例时，更新状态文件以反映当前状态。
        找到不可恢复实例时，kill 该进程释放端口。

        Returns:
            (cdp_port, profile_path) 如果找到可恢复的 Chrome，否则 None
        """
        import urllib.request as _ur

        for port in range(9222, 9232 + 1):
            try:
                url = f"http://127.0.0.1:{port}/json/version"
                req = _ur.Request(url)
                with _ur.urlopen(req, timeout=1.0) as resp:
                    if resp.status == 200:
                        data = json.loads(resp.read().decode())
                        # 尝试获取 profile 路径（Chrome 可能不暴露此信息）
                        profile_path = data.get(
                            "userDataDir",
                            str(get_cache_dir() / "chrome_profile"),
                        )
                        # 尝试 connect_over_cdp 验证连接可用
                        try:
                            pw = sync_playwright().start()
                            browser = pw.chromium.connect_over_cdp(
                                f"http://127.0.0.1:{port}"
                            )
                            # 连接成功 → 更新状态文件
                            pid = get_pid_on_port(port)
                            from src.browser.daemon_state import write_state
                            write_state(
                                pid=pid or 0,
                                cdp_port=port,
                                profile_path=str(profile_path),
                            )
                            # 释放测试连接
                            try:
                                browser.close()
                            except Exception:
                                pass
                            try:
                                pw.stop()
                            except Exception:
                                pass
                            return port, str(profile_path)
                        except Exception:
                            pass
                        try:
                            pw.stop()
                        except Exception:
                            pass
            except Exception:
                continue
        return None

    def launch_daemon(self, profile_path: Optional[Path] = None) -> "Browser":
        """冷启动 Chrome Daemon（Patchright 守护进程）

        1. 先扫描端口查找孤儿 Chrome → 如可恢复则直接连接（根治幽灵连接）
        2. subprocess 启动 daemon_runner.py（Patchright launch_persistent_context）
        3. 等待 CDP 端点就绪
        4. 读取 daemon.json
        5. connect_over_cdp 获取 Browser 对象
        6. 返回 Browser

        Returns:
            Patchright Browser 对象（通过 connect_over_cdp 连接）
        """
        # ── Step 0: 孤儿进程恢复 ──
        orphan = BrowserFactory._find_and_recover_orphan()
        if orphan is not None:
            orphan_port, _ = orphan
            print(f"[Daemon] 恢复孤儿 Chrome (端口 {orphan_port})", file=sys.stderr)
            try:
                return self.connect_to_daemon()
            except Exception as e:
                print(f"[Daemon] 孤儿 Chrome 连接失败: {e}，重新冷启动", file=sys.stderr)

        # 守卫：如果已有存活 Daemon，直接连接返回
        if BrowserFactory.daemon_is_alive():
            return self.connect_to_daemon()

        if profile_path is None:
            profile_path = Path(DEFAULT_PROFILE_DIR)

        port = self._find_free_port()
        state_path = str(DAEMON_STATE_PATH)
        runner = Path(__file__).resolve().parent / "daemon_runner.py"

        cmd = [
            sys.executable,
            str(runner),
            "--port", str(port),
            "--profile", str(profile_path),
            "--state", state_path,
        ]

        try:
            proc = subprocess.Popen(
                cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True,
            )
        except Exception as e:
            raise BrowserLaunchError(
                f"Failed to start daemon runner: {e}"
            ) from e

        # 等待 CDP 就绪（守护进程启动 Patchright + Chrome 需要时间）
        try:
            self._wait_for_cdp(port, timeout=30.0)
        except BrowserLaunchError:
            kill_process(proc.pid)
            raise

        # daemon.json 已由守护进程写入，connect_over_cdp 获取 Browser
        if not _PATCHRIGHT_AVAILABLE:
            raise BrowserLaunchError("Patchright not found.")

        if self._playwright is None:
            self._playwright = sync_playwright().start()

        endpoint = f"http://127.0.0.1:{port}"
        browser = self._playwright.chromium.connect_over_cdp(
            endpoint, timeout=10000
        )

        return browser

    def connect_to_daemon(self) -> "Browser":
        """连接到已有 Chrome Daemon（热连接）

        读取 daemon.json → 检测存活 → connect_over_cdp → 返回 Browser。
        如果 Daemon 不存活，抛出 BrowserLaunchError（调用方降级为冷启动）。

        Returns:
            Patchright Browser 对象
        """
        if not _PATCHRIGHT_AVAILABLE:
            raise BrowserLaunchError("Patchright not found.")

        state = read_state()
        if state is None:
            raise BrowserLaunchError(
                "No daemon state file found. Run launch_daemon first.",
                exit_code=1,
            )

        if not is_pid_alive(state.pid):
            cleanup_stale()
            raise BrowserLaunchError(
                "Daemon Chrome process is dead. Restarting...",
                exit_code=1,
            )

        if not is_cdp_responsive(state.cdp_port, timeout=2.0):
            # CDP 端口无响应，尝试 kill 旧进程
            kill_process(state.pid, force=True)
            cleanup_stale()
            raise BrowserLaunchError(
                "Daemon CDP unresponsive. Restarting...",
                exit_code=1,
            )

        if self._playwright is None:
            self._playwright = sync_playwright().start()

        endpoint = f"http://127.0.0.1:{state.cdp_port}"
        try:
            browser = self._playwright.chromium.connect_over_cdp(
                endpoint, timeout=5000
            )
        except Exception as e:
            cleanup_stale()
            raise BrowserLaunchError(
                f"Failed to connect to daemon: {e}"
            ) from e

        return browser

    @staticmethod
    def daemon_is_alive() -> bool:
        """检测 Daemon 是否存活（快速检查，不建立连接）"""
        state = read_state()
        if state is None:
            return False
        if not is_pid_alive(state.pid):
            cleanup_stale()
            return False
        return True

    @staticmethod
    def cleanup_daemon() -> None:
        """停止 Chrome Daemon：SIGTERM → 3s → SIGKILL → 删除状态文件"""
        state = read_state()
        if state is None:
            return

        if is_pid_alive(state.pid):
            kill_process(state.pid)
            # 等待优雅退出
            for _ in range(30):  # 3s, 每 100ms 检查
                time.sleep(0.1)
                if not is_pid_alive(state.pid):
                    break
            else:
                # 优雅退出超时，强制终止
                kill_process(state.pid, force=True)

            # 清理孤儿子进程 (Chrome Helper / Renderer / GPU)
            time.sleep(0.5)
            kill_process_tree(state.pid)

        remove_state()
