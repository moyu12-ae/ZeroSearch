"""
T5.2.3 分级错误降级处理模块

错误处理策略:
- CAPTCHA 检测 → 退出码 2 + 提示 --show-browser
- 网络超时 (15s) → 自动重试 1 次 → 仍失败返回错误
- AI Mode 不可用 → 尝试普通搜索结果降级
- 连续 3 次任意失败 → 聚合错误摘要，不无限重试

设计来源: .anws/v1/04_SYSTEM_DESIGN/search-engine.md
"""

from __future__ import annotations

import time
from typing import Optional

# 退出码常量 (与 src/search/cli.py 对齐)
EXIT_SUCCESS = 0
EXIT_ERROR = 1
EXIT_CAPTCHA = 2
EXIT_BROWSER_CLOSED = 3
EXIT_REGION_UNAVAILABLE = 4
EXIT_PROFILE_LOCKED = 5

# 网络超时阈值 (秒)
TIMEOUT_SECONDS = 15
# 最大连续失败次数
MAX_FAILURES = 3


class ErrorHandler:
    """分级错误降级处理器。

    职责:
    1. 检测并处理 CAPTCHA 页面
    2. 网络超时自动重试
    3. AI Mode 不可用时降级到普通搜索结果
    4. 连续失败次数追踪，达到阈值后聚合错误摘要

    Usage:
        handler = ErrorHandler(max_retries=3)

        # 检查页面是否为 CAPTCHA
        captcha_msg = handler.handle_captcha(page)
        if captcha_msg:
            print(captcha_msg, file=sys.stderr)  # v0.2: 默认有头，用户直接操作浏览器窗口
            sys.exit(EXIT_CAPTCHA)

        # 网络超时自动重试
        if not handler.handle_timeout(page, query="Python"):
            print("网络超时，请检查连接", file=sys.stderr)

        # AI Mode 不可用时降级
        fallback = handler.handle_ai_unavailable(page)
        if fallback:
            print(fallback)

        # 连续失败检查
        if handler.should_abort():
            print(handler.last_error, file=sys.stderr)
    """

    def __init__(self, max_retries: int = MAX_FAILURES) -> None:
        """初始化错误处理器。

        Args:
            max_retries: 最大连续失败次数，默认 3
        """
        self._max_retries = max_retries
        self._failures: list[dict[str, str | float]] = []
        self._retry_attempted: bool = False  # timeout 重试标记

    # ── 属性 ─────────────────────────────────────────────────────────

    @property
    def failure_count(self) -> int:
        """返回当前连续失败次数。"""
        return len(self._failures)

    @property
    def last_error(self) -> str:
        """返回最近一次错误的描述，无错误时返回空字符串。"""
        if not self._failures:
            return ""
        return self._failures[-1].get("message", "")

    # ── 内部方法 ─────────────────────────────────────────────────────

    def _record_failure(self, error_type: str, message: str) -> None:
        """记录一次失败。

        Args:
            error_type: 错误类型标签 (e.g. "captcha", "timeout", "ai_unavailable")
            message: 人类可读的错误描述
        """
        self._failures.append({
            "type": error_type,
            "message": message,
            "timestamp": time.time(),
        })

    def _build_aggregated_error(self) -> str:
        """构建聚合错误摘要。

        Returns:
            多行错误摘要文本
        """
        if not self._failures:
            return ""

        summary_lines: list[str] = []
        summary_lines.append("=" * 60)
        summary_lines.append(f"错误摘要: 连续 {len(self._failures)} 次失败，已中止重试")
        summary_lines.append("=" * 60)

        for i, failure in enumerate(self._failures, start=1):
            ftype = failure.get("type", "unknown")
            fmsg = failure.get("message", "")
            summary_lines.append(f"  [{i}] [{ftype}] {fmsg}")

        summary_lines.append("")
        summary_lines.append("建议: 请检查网络连接、代理设置。浏览器窗口已打开，可直接手动验证。")
        summary_lines.append("=" * 60)

        return "\n".join(summary_lines)

    # ── CAPTCHA 检测 ─────────────────────────────────────────────────

    def handle_captcha(self, page) -> str:
        """检测页面是否为 Google CAPTCHA/人机验证页面。

        检测逻辑:
        1. 等待 1.5 秒让 reCAPTCHA iframe 渲染
        2. 检查当前 URL 是否包含 /sorry/index
        3. 检查页面文本是否包含 CAPTCHA 关键字
        4. 检查页面标题是否包含 "sorry"

        Args:
            page: Patchright/Playwright Page 对象

        Returns:
            空字符串表示无 CAPTCHA；非空字符串为 CAPTCHA 错误消息
        """
        # 等待 CAPTCHA 页面完全渲染
        try:
            page.wait_for_timeout(1500)
        except Exception:
            pass

        is_captcha = False
        reason = ""

        # 1) 通过 URL 检测
        try:
            url = page.url or ""
            if "/sorry/index" in url:
                is_captcha = True
                reason = f"URL 包含 /sorry/index: {url}"
        except Exception:
            pass

        # 2) 通过页面标题检测
        if not is_captcha:
            try:
                title = (page.title() or "").lower()
                if "sorry" in title:
                    is_captcha = True
                    reason = "页面标题包含 'sorry'"
            except Exception:
                pass

        # 3) 通过页面文本内容检测
        if not is_captcha:
            try:
                body_text = (page.inner_text("body") or "").lower()
                captcha_keywords = [
                    "captcha",
                    "unusual traffic",
                    "automated requests",
                    "not a robot",
                ]
                for kw in captcha_keywords:
                    if kw in body_text:
                        is_captcha = True
                        reason = f"页面文本包含 '{kw}'"
                        break
            except Exception:
                pass

        if is_captcha:
            message = (
                f"[CAPTCHA] 检测到人机验证页面 ({reason})。\n"
                f"浏览器窗口已打开，请在窗口中手动完成验证。"
            )
            self._record_failure("captcha", reason)
            return message

        return ""

    # ── 网络超时处理 ─────────────────────────────────────────────────

    def handle_timeout(self, page, query: str) -> bool:
        """处理网络超时，自动重试一次页面导航。

        超时阈值: 15 秒。
        重试策略: 自动重试 1 次，使用同一 query 重新导航。

        Args:
            page: Patchright/Playwright Page 对象
            query: 搜索查询字符串，用于重试导航

        Returns:
            True 表示重试成功，False 表示重试后仍失败
        """
        if self._retry_attempted:
            # 已经重试过一次，不再重试
            self._record_failure("timeout", f"重试后仍超时: {query}")
            return False

        # 检查是否发生了超时 (通过 Playwright TimeoutError 或 page 状态)
        timeout_occurred = False
        try:
            # 尝试获取页面标题确认页面是否响应
            _ = page.title()
        except Exception as exc:
            class_name = type(exc).__name__
            if "timeout" in class_name.lower():
                timeout_occurred = True
            elif hasattr(exc, "message") and "timeout" in str(getattr(exc, "message", "")).lower():
                timeout_occurred = True

        if not timeout_occurred:
            return True  # 没有超时，正常

        # 执行重试
        self._retry_attempted = True
        try:
            # 构建 Google 搜索 URL 并重新导航
            from urllib.parse import quote_plus
            search_url = f"https://www.google.com/search?q={quote_plus(query)}&udm=50"
            page.goto(search_url, timeout=TIMEOUT_SECONDS * 1000)
            return True
        except Exception:
            self._record_failure("timeout", f"网络超时: query={query}")
            return False

    # ── AI Mode 降级 ─────────────────────────────────────────────────

    def handle_ai_unavailable(self, page) -> Optional[str]:
        """检测 AI Mode 是否可用，不可用时尝试提取普通搜索结果作为降级。

        检测方式: 查找 AI overview 元素 (Google AI Mode 的标志性元素)。
        降级策略: 提取搜索结果的标题和摘要，标记为 [ASSUMPTION: 非 AI 结果]。

        Args:
            page: Patchright/Playwright Page 对象

        Returns:
            - None: AI Mode 可用，无需降级
            - str: 降级后的普通搜索结果文本 (已标记 [ASSUMPTION: 非 AI 结果])
        """
        # 尝试查找 AI overview 元素
        has_ai_overview = False
        try:
            # 常见的 AI overview 选择器
            ai_selectors = [
                "div[data-sncf]",
                "[data-attrid=\"wa_c_\"]",
                ".cUnQKe",
                ".ifM9O",
                # 通用 AI overview 容器
                "div.ULSxyf",
                "[data-hveid] h2",
            ]
            for selector in ai_selectors:
                try:
                    element = page.query_selector(selector)
                    if element:
                        has_ai_overview = True
                        break
                except Exception:
                    continue

            # 备选方案: 检查页面是否包含 AI 生成标记
            if not has_ai_overview:
                page_text = page.inner_text("body") or ""
                ai_indicators = [
                    "AI Overview",
                    "AI 概述",
                    "生成式 AI",
                    "Generative AI",
                ]
                for indicator in ai_indicators:
                    if indicator.lower() in page_text.lower():
                        has_ai_overview = True
                        break
        except Exception:
            pass

        if has_ai_overview:
            return None  # AI Mode 可用，正常流程

        # AI Mode 不可用，尝试提取普通搜索结果
        self._record_failure("ai_unavailable", "未检测到 AI overview 元素")

        fallback_text = self._extract_plain_results(page)
        if fallback_text:
            return (
                "[ASSUMPTION: 非 AI 结果] AI Mode 不可用，以下为普通搜索结果:\n\n"
                + fallback_text
            )

        # 无法提取任何结果
        return None

    @staticmethod
    def _extract_plain_results(page) -> str:
        """从页面中提取普通搜索结果 (标题 + 摘要)。

        Args:
            page: Patchright/Playwright Page 对象

        Returns:
            格式化的搜索结果文本，提取失败返回空字符串
        """
        result_lines: list[str] = []
        try:
            # Google 普通搜索结果的选择器
            result_selectors = [
                "div.g",           # 通用结果容器
                "div[data-sokoban-container]",
                "div.MjjYud",      # 较新的结果容器
            ]

            items = []
            for selector in result_selectors:
                try:
                    elements = page.query_selector_all(selector)
                    if elements:
                        items = elements
                        break
                except Exception:
                    continue

            for idx, item in enumerate(items, start=1):
                try:
                    # 提取标题
                    title_el = item.query_selector("h3")
                    title = title_el.inner_text().strip() if title_el else ""

                    # 提取链接
                    link_el = item.query_selector("a[href]")
                    link = link_el.get_attribute("href") if link_el else ""

                    # 提取摘要
                    snippet_selectors = [
                        "div.VwiC3b",
                        "span.aCOpRe",
                        "div[data-sncf]",
                    ]
                    snippet = ""
                    for sel in snippet_selectors:
                        snippet_el = item.query_selector(sel)
                        if snippet_el:
                            snippet = snippet_el.inner_text().strip()
                            break

                    if title:
                        result_lines.append(f"  {idx}. {title}")
                        if snippet:
                            result_lines.append(f"     {snippet}")
                        if link:
                            result_lines.append(f"     {link}")
                        result_lines.append("")
                except Exception:
                    continue

        except Exception:
            pass

        return "\n".join(result_lines).strip()

    # ── 连续失败中止 ─────────────────────────────────────────────────

    def should_abort(self) -> bool:
        """检查是否应中止操作 (连续失败次数达到阈值)。

        当连续失败次数达到 max_retries 时:
        1. 构建聚合错误摘要
        2. 写入 last_error 属性
        3. 返回 True 表示应中止

        Returns:
            True 表示应中止操作
        """
        if self.failure_count >= self._max_retries:
            # 将聚合错误摘要写入最近一次错误消息
            if self._failures:
                self._failures[-1]["message"] = self._build_aggregated_error()
            return True
        return False
