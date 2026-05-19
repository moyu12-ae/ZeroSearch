"""
搜索引擎主逻辑 (SearchEngine)

编排 BrowserEngine → ContentExtractor → MarkdownConverter 全流程。
对齐 search-engine.md §4 泳道图 + §8 性能设计。
"""

import time
import sys
import traceback
from pathlib import Path
from typing import Optional

from ..browser.context_manager import BrowserContext, BrowserState

from .cache import LRUCache
from .error_handler import ErrorHandler, EXIT_CAPTCHA


class SearchEngine:
    """Google AI Mode 搜索引擎 — 全流程编排器

    协调 BrowserContext → ContentExtractor → MarkdownConverter，
    内建 LRU 缓存 + 分级错误降级。
    """

    CACHE_SIZE = 50
    CACHE_TTL = 300  # 5 分钟

    def __init__(self, headless: bool = True, debug: bool = False):
        self._headless = headless
        self._debug = debug
        self._browser = BrowserContext(headless=headless)
        self._cache = LRUCache(max_size=self.CACHE_SIZE, ttl_seconds=self.CACHE_TTL)
        self._error_handler = ErrorHandler(max_retries=3)

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

        # ── Step 2: 编排搜索全流程 ────────────────────
        try:
            result = self._run_search_pipeline(query)
        except KeyboardInterrupt:
            self._log("用户中断")
            self._browser.shutdown()
            sys.exit(130)
        except Exception as e:
            self._log(f"搜索异常: {e}\n{traceback.format_exc()}")
            result = {
                "markdown": f"搜索失败: {e}",
                "citations": [],
                "elapsed_ms": (time.perf_counter() - t_start) * 1000,
                "cached": False,
            }

        # ── Step 3: 写入缓存 ──────────────────────────
        if result.get("markdown"):
            self._cache.put(cache_key, {
                "markdown": result["markdown"],
                "citations": result.get("citations", []),
                "query": query,
                "timestamp": time.time(),
            })

        # ── Step 4: 保存文件 ──────────────────────────
        if save and result.get("markdown"):
            self._save_result(query, result["markdown"])

        result["cached"] = False
        result["elapsed_ms"] = (time.perf_counter() - t_start) * 1000
        return result

    def _run_search_pipeline(self, query: str) -> dict:
        """执行搜索流水线"""

        # Navigation
        t_nav = time.perf_counter()
        ctx = self._browser.get_context()
        page = ctx.pages[0] if ctx.pages else ctx.new_page()

        google_url = (
            f"https://www.google.com/search?q={query}&udm=50"
        )
        page.goto(google_url, wait_until="domcontentloaded", timeout=15000)
        nav_ms = (time.perf_counter() - t_nav) * 1000
        self._log(f"导航完成, 耗时={nav_ms:.0f}ms")

        # CAPTCHA check
        captcha_msg = self._error_handler.handle_captcha(page)
        if captcha_msg:
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

    def shutdown(self) -> None:
        """关闭搜索引擎，释放浏览器资源"""
        self._browser.shutdown()
