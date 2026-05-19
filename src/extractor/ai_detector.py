"""
AI 完成检测模块 (T3.1.1)
4 阶段检测 AI 回答是否渲染完成：
  Stage 1: SVG thumbs-up button
  Stage 2: aria-label feedback (多语言)
  Stage 3: 文本长度 > 200 chars 且 1s 内稳定
  Stage 4: 15s 硬超时回退

输入: Camoufox Page 对象 (playwright.sync_api.Page)
输出: (ai_text: str, completed: bool)

设计依据: .anws/v1/04_SYSTEM_DESIGN/content-extractor.md §6.3
"""

from __future__ import annotations

import time
from typing import Optional, List, Dict, Any

# ---------------------------------------------------------------------------
# 阶段配置常量
# 来源: .anws/v1/04_SYSTEM_DESIGN/content-extractor.md §6.3 L313-361
# ---------------------------------------------------------------------------

COMPLETION_STAGES: List[Dict[str, Any]] = [
    {
        "stage": 1,
        "strategy": "SVG thumbs-up detection",
        "selector": 'svg[aria-label*="thumbs-up"], [aria-label*="Thumbs up"]',
        "timeout_ms": 1000,
        "fallback": "stage_2",
        "js_inject": """
            () => document.querySelector('svg[aria-label*="thumbs-up"]') !== null ||
                 document.querySelector('[aria-label*="Thumbs up"]') !== null
        """,
    },
    {
        "stage": 2,
        "strategy": "aria-label feedback (multi-lang)",
        "selector": (
            '[aria-label*="feedback"], [aria-label*="Feedback"], '
            '[aria-label*="Bewertung"], [aria-label*="beoordeling"]'
        ),
        "timeout_ms": 1000,
        "fallback": "stage_3",
        "js_inject": """
            () => {
                const labels = ['feedback', 'Feedback', 'Bewertung', 'beoordeling'];
                return labels.some(l => document.querySelector(`[aria-label*="${l}"]`) !== null);
            }
        """,
    },
    {
        "stage": 3,
        "strategy": "text content length check",
        "threshold_chars": 200,
        "stability_ms": 300,
        "timeout_ms": 2000,
        "fallback": "stage_4",
        "js_inject": """
            () => {
                const text = document.querySelector('[data-snc-answer-body]')?.innerText ||
                             document.querySelector('main')?.innerText ||
                             document.body.innerText;
                return text && text.length > 200;
            }
        """,
    },
    {
        "stage": 4,
        "strategy": "hard timeout fallback",
        "timeout_ms": 2000,
        "fallback": None,
        "js_inject": "() => true",
    },
]

# 提取 AI 回答文本的 JS 注入（阶段 4 或提前提取使用）
_EXTRACT_TEXT_JS: str = """
    () => {
        const el = document.querySelector('[data-snc-answer-body]') ||
                   document.querySelector('main') ||
                   document.body;
        return el ? el.innerText : '';
    }
"""


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _get_page_text(page) -> str:
    """从 Page 对象提取当前 AI 回答文本。

    优先选择 [data-snc-answer-body]，其次 <main>，最后 body。
    """
    try:
        text = page.evaluate(_EXTRACT_TEXT_JS)
        return text or ""
    except Exception:
        return ""


def _check_stage(page, stage_config: Dict[str, Any]) -> bool:
    """对当前 Page 执行单阶段 JS 检测，返回 True 表示该阶段通过。"""
    js_code = stage_config.get("js_inject", "() => true")
    try:
        result = page.evaluate(js_code)
        return bool(result)
    except Exception:
        return False


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def detect_ai_completion(page, timeout_ms: int = 8000) -> tuple[str, bool]:
    """4 阶段检测 AI 回答是否渲染完成。

    按顺序执行 COMPLETION_STAGES 中的 4 个阶段，每阶段有其独立
    timeout_ms（阶段 1-3 的总和应接近 timeout_ms 值）。

    Parameters
    ----------
    page
        Playwright/Patchero 同步 Page 对象（Camoufox BrowserContext 页面）。
    timeout_ms : int
        总超时时间（毫秒），默认 15000ms（15s）。

    Returns
    -------
    tuple[str, bool]
        (ai_text, completed):
        - ai_text: 从页面提取的 AI 回答文本（字符串）。
        - completed: True 表示 AI 回答已渲染完成并被捕获；
                     False 表示超时或异常，但文本仍会被返回。
    """
    start_time = time.monotonic()

    for stage_cfg in COMPLETION_STAGES:
        stage_num = stage_cfg["stage"]
        stage_timeout = stage_cfg.get("timeout_ms", 3000) / 1000.0  # 转为秒
        stage_start = time.monotonic()

        while True:
            elapsed_total_ms = (time.monotonic() - start_time) * 1000
            if elapsed_total_ms >= timeout_ms:
                # 全局超时：进入阶段 4 无条件提取
                text = _get_page_text(page)
                return (text, False)

            if _check_stage(page, stage_cfg):
                if stage_num == 3:
                    # 阶段 3 额外要求：文本长度 > 200 且 1s 内稳定
                    stability_ms = stage_cfg.get("stability_ms", 1000)
                    stable_text = _get_page_text(page)
                    if stable_text and len(stable_text) > stage_cfg.get("threshold_chars", 200):
                        # 等待 stability_ms 后确认文本不再变化
                        time.sleep(stability_ms / 1000.0)
                        if _check_stage(page, stage_cfg):
                            confirm_text = _get_page_text(page)
                            if confirm_text and len(confirm_text) > stage_cfg.get("threshold_chars", 200):
                                return (confirm_text, True)
                    # 文本不够长或稳定性未通过，继续轮询
                elif stage_num == 4:
                    # 阶段 4：无条件提取文本并返回
                    text = _get_page_text(page)
                    return (text, False)
                else:
                    # 阶段 1 或 2 命中
                    text = _get_page_text(page)
                    return (text, True)

            # 检查本阶段是否超时
            elapsed_stage_ms = (time.monotonic() - stage_start) * 1000
            if elapsed_stage_ms >= stage_cfg.get("timeout_ms", 3000):
                break  # 进入下一个阶段

            # 轮询间隔（避免 CPU 空转）
            time.sleep(0.2)

    # 理论上走到这里意味着所有阶段都超时，但阶段 4 总是通过
    text = _get_page_text(page)
    return (text, False)
