"""
CLI 入口 (T5.1.1) — argparse 参数解析与退出码路由

设计来源: .anws/v1/04_SYSTEM_DESIGN/search-engine.md §5 CLI 参数规范

调用方式:
    python src/search/cli.py --query "React hooks 2026"
    python src/search/cli.py --query "React hooks" --debug --save
    python src/search/cli.py --query "React hooks" --profile "/path/to/chrome"
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
        description="ZeroSearch — Patchright Chromium Google AI Mode 搜索",
    )
    # 动作组: --query / --start / --stop 互斥
    action_group = parser.add_mutually_exclusive_group(required=True)
    action_group.add_argument(
        "--query",
        "-q",
        type=str,
        help="搜索查询字符串",
    )
    action_group.add_argument(
        "--start",
        action="store_true",
        default=False,
        help="启动 Chrome Daemon（不搜索）",
    )
    action_group.add_argument(
        "--stop",
        action="store_true",
        default=False,
        help="停止 Chrome Daemon",
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
        "CLI 参数解析完成 | query=%r | save=%s | debug=%s",
        args.query,
        args.save,
        args.debug,
    )

    # 确保项目根在 sys.path，支持绝对导入
    _setup_import_path()

    # ── Daemon 管理命令 (--start / --stop) ─────────────────────────
    if args.start or args.stop:
        from src.browser.browser_factory import BrowserFactory

        if args.start:
            if BrowserFactory.daemon_is_alive():
                print("[Daemon] Chrome 已在运行", file=sys.stderr)
                return EXIT_SUCCESS
            print("[Daemon] 正在启动 Chrome...", file=sys.stderr)
            try:
                factory = BrowserFactory(headless=False)
                browser = factory.launch_daemon()
                # 只启动不搜索：立即释放连接
                try:
                    browser.close()
                except Exception:
                    pass
                print("[Daemon] Chrome 已启动", file=sys.stderr)
                return EXIT_SUCCESS
            except Exception as e:
                print(f"[Daemon] 启动失败: {e}", file=sys.stderr)
                return EXIT_ERROR

        if args.stop:
            if not BrowserFactory.daemon_is_alive():
                print("[Daemon] Chrome 未在运行", file=sys.stderr)
                return EXIT_SUCCESS
            print("[Daemon] 正在停止 Chrome...", file=sys.stderr)
            try:
                BrowserFactory.cleanup_daemon()
                print("[Daemon] Chrome 已停止", file=sys.stderr)
                return EXIT_SUCCESS
            except Exception as e:
                print(f"[Daemon] 停止失败: {e}", file=sys.stderr)
                return EXIT_ERROR

    # ── 搜索工作流 (--query) ────────────────────────────────────────
    try:
        from src.search.engine import SearchEngine
    except ImportError as exc:
        logger.warning(
            "SearchEngine 模块尚未实现 (ImportError: %s)。",
            exc,
        )
        return EXIT_ERROR

    try:
        engine = SearchEngine(
            headless=False,  # v0.2: 始终有头
            debug=args.debug,
        )
        try:
            result = engine.search(query=args.query, save=args.save)

            if result.get("markdown"):
                print(result["markdown"])
            else:
                logger.warning("搜索结果为空，请检查查询条件或网络连接。")

            return EXIT_SUCCESS
        finally:
            engine.shutdown()  # 搜索完成后释放资源 (不关闭 Daemon Chrome)

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
    if "profile" in combined and "lock" in combined:
        return EXIT_PROFILE_LOCKED

    return EXIT_ERROR


if __name__ == "__main__":
    sys.exit(main())
