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
from pathlib import Path

# ── 退出码常量 (对齐 search-engine.md §5.2) ──────────────────────────
EXIT_SUCCESS = 0
EXIT_ERROR = 1
EXIT_CAPTCHA = 2
EXIT_BROWSER_CLOSED = 3
EXIT_REGION_UNAVAILABLE = 4
EXIT_PROFILE_LOCKED = 5
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
        "--profile",
        type=str,
        default=None,
        help="Chrome Profile 路径 (由 SKILL.md System 0 传入)",
    )
    parser.add_argument(
        "--fresh-profile",
        action="store_true",
        default=False,
        help="使用独立空白 Profile（忽略 profile_config.json）",
    )
    parser.add_argument(
        "--reconfigure",
        action="store_true",
        default=False,
        help="重新触发 Profile 选择",
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


def _setup_import_path() -> None:
    """确保项目根目录在 sys.path 中，支持绝对导入。

    cli.py 可能通过 run.py 子进程或直接执行调用。
    子进程中 sys.path[0] 是 cli.py 所在目录 (src/search/)，
    需要将项目根加入 path 以支持 `from src.search.engine import ...`。
    """
    cli_dir = Path(__file__).resolve().parent  # src/search/
    project_root = cli_dir.parent.parent       # 项目根
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))


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
        "CLI 参数解析完成 | query=%r | save=%s | debug=%s | profile=%r",
        args.query,
        args.save,
        args.debug,
        args.profile,
    )

    # 确保项目根在 sys.path，支持绝对导入
    _setup_import_path()

    # Profile 路径解析
    if args.reconfigure:
        from src.browser.profile_manager import PROFILE_CONFIG_PATH
        if PROFILE_CONFIG_PATH.exists():
            PROFILE_CONFIG_PATH.unlink()
        print("Profile 配置已清除。下次运行将重新选择。", file=sys.stderr)
        return EXIT_SUCCESS

    from src.browser.profile_manager import resolve_profile_path

    profile_path = resolve_profile_path(
        profile_arg=args.profile or ("--fresh-profile" if args.fresh_profile else None)
    )

    if profile_path is None:
        print(
            "⚠️  首次运行，请在 Claude Code 中触发 /zerosearch "
            "以完成 Profile 配置。",
            file=sys.stderr,
        )
        print("   或使用 --profile <path> 指定 Profile 路径。", file=sys.stderr)
        return EXIT_ERROR

    # ── 尝试导入并调用 SearchEngine ─────────────────────────────────
    try:
        from src.search.engine import SearchEngine
    except ImportError as exc:
        logger.warning(
            "SearchEngine 模块尚未实现 (ImportError: %s)。",
            exc,
        )
        return EXIT_ERROR

    # ── 正常工作流 ───────────────────────────────────────────────────
    try:
        engine = SearchEngine(
            headless=False,  # v0.2: 始终有头
            debug=args.debug,
            profile_path=str(profile_path),
        )
        try:
            result = engine.search(query=args.query, save=args.save)

            if result.get("markdown"):
                print(result["markdown"])
            else:
                logger.warning("搜索结果为空，请检查查询条件或网络连接。")

            return EXIT_SUCCESS
        finally:
            engine.shutdown()  # 搜索完成后立即关闭浏览器

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
            if code in {EXIT_CAPTCHA, EXIT_BROWSER_CLOSED, EXIT_REGION_UNAVAILABLE, EXIT_PROFILE_LOCKED}:
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
