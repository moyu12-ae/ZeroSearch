"""
提取协调器 (Extractor Coordinator)

编排 AI 检测 → 引用提取 → DOM 清洗 三个阶段。
对齐 content-extractor.md §4 组件图 + §5 接口设计。
"""

import time
from dataclasses import dataclass, field
from typing import Optional

from .ai_detector import detect_ai_completion
from .citation_extractor import extract_citations, Citation
from .dom_cleaner import clean_html


@dataclass
class ExtractionResult:
    """内容提取的完整输出"""
    ai_text: str = ""
    citations: list = field(default_factory=list)
    raw_html: str = ""
    completed: bool = True
    extraction_time_ms: float = 0.0


def extract_content(page, timeout_ms: int = 15000) -> ExtractionResult:
    """从 Google AI Mode 页面提取 AI 概述和引用

    调用序列:
    1. detect_ai_completion(page) → AI 文本 + 完成状态
    2. extract_citations(page) → 引用列表
    3. clean_html(raw_html) → 清洗后 HTML

    步骤 1 超时时，步骤 2/3 仍会执行（不中断流程）。

    Args:
        page: Camoufox 渲染完成的 Page 对象
        timeout_ms: AI 完成检测总超时 (ms)

    Returns:
        ExtractionResult (ai_text, citations, raw_html, completed, extraction_time_ms)
    """
    t_start = time.perf_counter()

    # 阶段 1: AI 完成检测
    ai_text, completed = detect_ai_completion(page, timeout_ms=timeout_ms)

    # 阶段 2: 引用提取（即使 AI 未完成也执行）
    citations = []
    try:
        citations = extract_citations(page)
    except Exception:
        pass  # 引用提取失败不中断流程

    # 阶段 3: DOM 清洗
    raw_html = ""
    try:
        raw_html = page.content()
    except Exception:
        pass

    cleaned_html = ""
    if raw_html:
        try:
            cleaned_html = clean_html(raw_html)
        except Exception:
            cleaned_html = raw_html  # 清洗失败保留原始 HTML

    t_end = time.perf_counter()
    extraction_time_ms = (t_end - t_start) * 1000

    return ExtractionResult(
        ai_text=ai_text or "",
        citations=citations or [],
        raw_html=cleaned_html,
        completed=completed,
        extraction_time_ms=extraction_time_ms,
    )
