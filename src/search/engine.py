"""
搜索引擎主逻辑 (SearchEngine)

编排 BrowserEngine → ContentExtractor → MarkdownConverter 全流程。
对齐 search-engine.md §4 泳道图 + §8 性能设计。

v0.3: Chrome Daemon — 冷启动/热连接双路径 + 状态指示
"""

import time
import sys
import atexit
import traceback
from typing import Optional

from ..browser.browser_factory import BrowserFactory
from ..browser.daemon_state import read_state, is_pid_alive, cleanup_stale

from .cache import LRUCache
from .error_handler import ErrorHandler, EXIT_CAPTCHA


class CDPDisconnectError(Exception):
    """CDP 连接断开（Chrome 崩溃/关窗），需要冷启动重试"""
    pass


class SearchEngine:
    """Google AI Mode 搜索引擎 — 全流程编排器

    协调 BrowserEngine (Daemon) → ContentExtractor → MarkdownConverter，
    内建 LRU 缓存 + 分级错误降级。
    """

    CACHE_SIZE = 50
    CACHE_TTL = 300  # 5 分钟

    def __init__(self, headless: bool = False, debug: bool = False):
        self._headless = headless
        self._debug = debug
        self._factory = BrowserFactory(headless=headless)
        self._cache = LRUCache(max_size=self.CACHE_SIZE, ttl_seconds=self.CACHE_TTL)
        self._error_handler = ErrorHandler(max_retries=3)
        atexit.register(self.shutdown)

    def search(self, query: str, save: bool = False) -> dict:
        """执行搜索

        Args:
            query: 搜索查询字符串
            save: 是否保存结果到文件

        Returns:
            {"markdown": str, "citations": list, "cached": bool, "elapsed_ms": float}
        """
        t_start = time.perf_counter()
        self._log(f"开始搜索: {query}")

        # ── Step 1: 检查缓存 ─────────────────────────
        cache_key = query.lower().strip()
        cached = self._cache.get(cache_key)
        if cached is not None:
            elapsed = (time.perf_counter() - t_start) * 1000
            self._log(f"缓存命中, 耗时={elapsed:.0f}ms")
            cached["cached"] = True
            cached["elapsed_ms"] = elapsed
            return cached

        # ── Step 2: 解析浏览器 ─────────────────────────
        try:
            browser, _ = self._resolve_browser()
        except KeyboardInterrupt:
            self._log("用户中断")
            self.shutdown()
            sys.exit(130)
        except Exception as e:
            self._log(f"浏览器解析失败: {e}")
            elapsed = (time.perf_counter() - t_start) * 1000
            return {
                "markdown": f"搜索失败: {e}",
                "citations": [],
                "elapsed_ms": elapsed,
                "cached": False,
            }

        # ── Step 3: 搜索流水线 ─────────────────────────
        try:
            result = self._run_search_pipeline(browser, query)
        except CDPDisconnectError as cdp_err:
            # Ghost Connection: Chrome 中途崩溃/关窗 → 清理 + 冷启动重试
            self._log(f"CDP 断连: {cdp_err}，清理并重试...")
            self._status("检测到浏览器连接断开，重新启动...")
            from ..browser.browser_factory import BrowserFactory
            BrowserFactory.cleanup_daemon()
            try:
                browser, _ = self._resolve_browser()
                result = self._run_search_pipeline(browser, query)
            except Exception as retry_err:
                self._log(f"重试失败: {retry_err}")
                result = {
                    "markdown": f"搜索失败: {retry_err}",
                    "citations": [],
                    "elapsed_ms": (time.perf_counter() - t_start) * 1000,
                    "cached": False,
                }
        except KeyboardInterrupt:
            self._log("用户中断")
            sys.exit(130)
        except Exception as e:
            self._log(f"搜索异常: {e}\n{traceback.format_exc()}")
            result = {
                "markdown": f"搜索失败: {e}",
                "citations": [],
                "elapsed_ms": (time.perf_counter() - t_start) * 1000,
                "cached": False,
            }

        # ── Step 4: 写入缓存 ──────────────────────────
        if result.get("markdown"):
            self._cache.put(cache_key, {
                "markdown": result["markdown"],
                "citations": result.get("citations", []),
                "query": query,
                "timestamp": time.monotonic(),
            })

        # ── Step 5: 保存文件 ──────────────────────────
        if save and result.get("markdown"):
            self._save_result(query, result["markdown"])

        result["cached"] = False
        result["elapsed_ms"] = (time.perf_counter() - t_start) * 1000
        return result

    def _resolve_browser(self):
        """解析浏览器：优先热连接，失败则冷启动

        Returns:
            (browser: Browser, is_hot: bool)
        """
        state = read_state()
        if state is not None and is_pid_alive(state.pid):
            from ..browser.daemon_state import is_cdp_responsive
            if is_cdp_responsive(state.cdp_port, timeout=2.0):
                try:
                    browser = self._factory.connect_to_daemon()
                    self._status("复用浏览器 (热搜索)")
                    return browser, True
                except Exception:
                    # connect 失败但 Chrome 仍存活 → 杀掉重建
                    self._status("热连接失败，重新启动 Chrome...")
                    BrowserFactory.cleanup_daemon()
            else:
                # CDP 无响应但 PID 存活 → 杀掉重建
                self._status("CDP 无响应，重新启动 Chrome...")
                BrowserFactory.cleanup_daemon()
        elif state is not None:
            # PID 死亡 → 清理过期状态
            self._status("检测到浏览器已关闭，正在重新启动...")
            cleanup_stale()

        # 冷启动
        if not BrowserFactory.daemon_is_alive():
            self._status("冷启动 Chrome...")
        browser = self._factory.launch_daemon()
        return browser, False

    def _run_search_pipeline(self, browser, query: str) -> dict:
        """执行搜索流水线 (v0.3: 使用独立 Page)

        Daemon 模式下：new_page() → 导航 → 提取 → page.close()
        不调用 browser.close() —— 浏览器保持存活。
        """
        t_nav = time.perf_counter()

        try:
            page = browser.new_page()
        except Exception as e:
            if _is_cdp_error(e):
                raise CDPDisconnectError(f"CDP 断连 (new_page): {e}") from e
            raise

        google_url = f"https://www.google.com/search?q={query}&udm=50"
        try:
            page.goto(google_url, wait_until="domcontentloaded", timeout=15000)
        except Exception as e:
            if _is_cdp_error(e):
                try:
                    page.close()
                except Exception:
                    pass
                raise CDPDisconnectError(f"CDP 断连 (goto): {e}") from e
            raise
        nav_ms = (time.perf_counter() - t_nav) * 1000
        self._log(f"导航完成, 耗时={nav_ms:.0f}ms")

        # CAPTCHA check
        captcha_msg = self._error_handler.handle_captcha(page)
        if captcha_msg:
            if not self._headless:
                print(
                    "⚠️  检测到 CAPTCHA，请在浏览器窗口中手动完成验证。",
                    file=sys.stderr,
                )
                print(
                    "   验证完成后回到终端按 Ctrl+C 继续搜索...",
                    file=sys.stderr,
                )
                try:
                    time.sleep(600)
                except KeyboardInterrupt:
                    print("\n   继续搜索...", file=sys.stderr)
                page.goto(google_url, wait_until="domcontentloaded", timeout=15000)
                self._log("CAPTCHA 验证后重新导航完成")
            else:
                page.close()
                return {"markdown": captcha_msg, "citations": []}

        # AI wait + extract
        t_ai = time.perf_counter()
        from ..extractor.extractor import extract_content
        extraction = extract_content(page, timeout_ms=15000)
        ai_ms = (time.perf_counter() - t_ai) * 1000
        self._log(f"提取完成 (completed={extraction.completed}), 耗时={ai_ms:.0f}ms")

        # AI unavailable → fallback
        if not extraction.completed and not extraction.ai_text:
            fallback = self._error_handler.handle_ai_unavailable(page)
            if fallback:
                extraction.ai_text = fallback

        # Convert to Markdown
        t_md = time.perf_counter()
        from ..converter.html_to_md import convert_html_to_markdown
        from ..converter.footnote_formatter import format_footnotes, Citation

        md_body = convert_html_to_markdown(
            extraction.raw_html or extraction.ai_text or ""
        )
        citations = [
            Citation(title=c.get("title", ""), url=c.get("url", ""), index=i + 1)
            for i, c in enumerate(extraction.citations or [])
        ]
        final_md = format_footnotes(md_body, citations)
        md_ms = (time.perf_counter() - t_md) * 1000
        self._log(f"Markdown 转换完成, 耗时={md_ms:.0f}ms")

        # Daemon 模式：关闭 Page，不关 Browser
        page.close()

        return {
            "markdown": final_md,
            "citations": [
                {"title": c.title, "url": c.url}
                for c in citations
            ],
        }

    def _save_result(self, query: str, markdown: str) -> None:
        """保存搜索结果到文件"""
        try:
            from ..converter.file_saver import save_result
            path = save_result(markdown, query)
            self._log(f"结果已保存: {path}")
        except Exception as e:
            self._log(f"保存失败: {e}")

    def _log(self, msg: str) -> None:
        """调试日志"""
        if self._debug:
            ts = time.strftime("%Y-%m-%d %H:%M:%S")
            print(f"[SearchEngine] {ts} | {msg}", file=sys.stderr)

    def _status(self, msg: str) -> None:
        """Daemon 状态指示 (总是输出到 stderr)"""
        print(f"[Daemon] {msg}", file=sys.stderr)

    def shutdown(self) -> None:
        """释放资源。注意：Daemon 模式下不关闭 Chrome！"""
        try:
            self._factory.close()
        except Exception:
            pass


def _is_cdp_error(exc: Exception) -> bool:
    """判断异常是否为 CDP 连接断开类错误"""
    msg = str(exc).lower()
    keywords = [
        "target closed",
        "browser closed",
        "browser has been closed",
        "connection closed",
        "websocket closed",
        "protocol error",
        "cdp",
        "target crashed",
        "browser has disconnected",
    ]
    return any(kw in msg for kw in keywords)
