"""
CLI 入口 (T5.1.1) — argparse 参数解析与退出码路由

设计来源: .anws/v1/04_SYSTEM_DESIGN/search-engine.md §5 CLI 参数规范

调用方式:
    python src/search/cli.py --query "React hooks 2026"
    python src/search/cli.py --query "React hooks" --debug --save
    python src/search/cli.py --query "React hooks" --show-browser
"""

from __future__ import annotations

import argparse
import logging
import sys

# ── 退出码常量 (对齐 search-engine.md §5.2) ──────────────────────────
EXIT_SUCCESS = 0
EXIT_ERROR = 1
EXIT_CAPTCHA = 2
EXIT_BROWSER_CLOSED = 3
EXIT_REGION_UNAVAILABLE = 4
EXIT_INTERRUPTED = 130

# ── 日志级别映射 ─────────────────────────────────────────────────────
_LOG_LEVEL_MAP = {
    True: logging.DEBUG,
    False: logging.WARNING,
}


def build_parser() -> argparse.ArgumentParser:
    """构建 CLI 参数解析器。

    Returns:
        配置好的 argparse.ArgumentParser 实例
    """
    parser = argparse.ArgumentParser(
        description="Google AI Mode Search — 通过 Camoufox 浏览器执行 Google AI Mode 搜索",
    )
    parser.add_argument(
        "--query",
        "-q",
        type=str,
        required=True,
        help="搜索查询字符串 (必填)",
    )
    parser.add_argument(
        "--save",
        action="store_true",
        default=False,
        help="将搜索结果保存到 results/ 目录",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        default=False,
        help="启用调试日志，输出每环节耗时",
    )
    parser.add_argument(
        "--show-browser",
        action="store_true",
        default=False,
        help="显示浏览器窗口 (headless=False)，用于 CAPTCHA 手动解决",
    )
    return parser


def configure_logging(debug: bool) -> None:
    """配置日志级别与输出格式。

    --debug 时日志级别为 DEBUG，输出到 stderr 带时间戳。
    非 debug 时日志级别为 WARNING，静默常规运行噪音。

    Args:
        debug: 是否启用 debug 模式
    """
    level = _LOG_LEVEL_MAP.get(debug, logging.WARNING)
    logger = logging.getLogger("SearchEngine")
    logger.setLevel(level)

    # 避免重复添加 handler
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stderr)
        if debug:
            fmt = "[SearchEngine] %(asctime)s | %(message)s"
            datefmt = "%Y-%m-%d %H:%M:%S"
        else:
            fmt = "[SearchEngine] %(message)s"
            datefmt = ""
        handler.setFormatter(logging.Formatter(fmt, datefmt=datefmt))
        logger.addHandler(handler)


def main(argv: list[str] | None = None) -> int:
    """CLI 主入口。

    解析参数 → 配置日志 → 调用 SearchEngine.search() → 返回退出码。

    Args:
        argv: 命令行参数列表，None 时使用 sys.argv[1:]

    Returns:
        退出码 (0/1/2/3/4/130)
    """
    parser = build_parser()
    args = parser.parse_args(argv)

    configure_logging(args.debug)
    logger = logging.getLogger("SearchEngine")

    logger.debug(
        "CLI 参数解析完成 | query=%r | save=%s | debug=%s | show_browser=%s",
        args.query,
        args.save,
        args.debug,
        args.show_browser,
    )

    # ── 尝试导入并调用 SearchEngine ─────────────────────────────────
    try:
        from src.search.engine import SearchEngine
    except ImportError as exc:
        # SearchEngine 尚未实现：打印确认信息并以通用错误退出
        logger.warning(
            "SearchEngine 模块尚未实现 (ImportError: %s)。"
            " 参数解析成功，当前处于参数验证模式。",
            exc,
        )
        print(f"[cli] 收到查询: {args.query!r}")
        print(f"[cli] save      : {args.save}")
        print(f"[cli] debug     : {args.debug}")
        print(f"[cli] show-brw  : {args.show_browser}")
        return EXIT_ERROR

    # ── 正常工作流 ───────────────────────────────────────────────────
    try:
        engine = SearchEngine(
            headless=not args.show_browser,
            debug=args.debug,
        )
        result = engine.search(query=args.query, save=args.save)

        if result.get("markdown"):
            print(result["markdown"])
        else:
            logger.warning("搜索结果为空，请检查查询条件或网络连接。")

        return EXIT_SUCCESS

    except KeyboardInterrupt:
        logger.info("接收到用户中断信号 (SIGINT)")
        return EXIT_INTERRUPTED

    except Exception as exc:
        exit_code = _extract_exit_code(exc)
        logger.error("搜索失败: %s (exit_code=%d)", exc, exit_code)
        return exit_code


def _extract_exit_code(exc: Exception) -> int:
    """从异常类型推导退出码。

    匹配优先级:
    1. 异常对象上的 exit_code 属性
    2. 异常类名和消息中的关键字

    Args:
        exc: 捕获的异常实例

    Returns:
        对应的退出码常量
    """
    class_name = type(exc).__name__
    message = str(exc)
    combined = (class_name + " " + message).lower()

    # ── 优先检查异常对象上的 exit_code 属性 ────────────────────
    if hasattr(exc, "exit_code"):
        try:
            code = int(getattr(exc, "exit_code"))  # type: ignore[arg-type]
            if code in {EXIT_CAPTCHA, EXIT_BROWSER_CLOSED, EXIT_REGION_UNAVAILABLE}:
                return code
        except (TypeError, ValueError):
            pass

    # ── 按优先级匹配关键字 ─────────────────────────────────────
    if "captcha" in combined:
        return EXIT_CAPTCHA
    if "browser" in combined and ("closed" in combined or "crash" in combined):
        return EXIT_BROWSER_CLOSED
    if "region" in combined or "unavailable" in combined:
        return EXIT_REGION_UNAVAILABLE

    return EXIT_ERROR


if __name__ == "__main__":
    sys.exit(main())
