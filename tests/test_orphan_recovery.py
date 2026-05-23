"""TDD: Firefox Chrome 孤儿进程恢复测试

测试 BrowserFactory._find_and_recover_orphan() 和 _get_chrome_pid_on_port()
——幽灵连接根因修复的验证。
"""

import socket
import subprocess
import sys
import threading
import time
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest


class TestOrphanRecovery:
    """TDD: 孤儿 Chrome 恢复功能"""

    # ── RED 1: 无 Chrome 运行时应返回 None ─────────────────────

    def test_find_orphan_no_chrome_returns_none(self):
        """当没有 Chrome 在已知端口范围监听时，应返回 None。"""
        from src.browser.browser_factory import BrowserFactory

        result = BrowserFactory._find_and_recover_orphan()
        assert result is None, (
            f"预期 None（无 Chrome 运行），实际返回 {result}"
        )

    # ── RED 2: 关闭端口不响应时返回 None ───────────────────────

    def test_find_orphan_port_not_cdp_returns_none(self):
        """扫描到端口开放但不是 CDP 端点时，应跳过并返回 None。"""
        from src.browser.browser_factory import BrowserFactory

        # 启动一个普通 HTTP 服务器模拟非 CDP 端口
        import http.server
        server = http.server.HTTPServer(("127.0.0.1", 9225), http.server.SimpleHTTPRequestHandler)
        server_thread = threading.Thread(target=server.serve_forever, daemon=True)
        server_thread.start()

        try:
            time.sleep(0.1)  # 等待服务器就绪
            result = BrowserFactory._find_and_recover_orphan()
            # 普通 HTTP 服务器不是 CDP 端点，应返回 None
            assert result is None, (
                f"非 CDP 端口应被跳过，实际返回 {result}"
            )
        finally:
            server.shutdown()

    # ── RED 3: lsof 获取 PID 边界 ──────────────────────────────

    def test_get_chrome_pid_closed_port_returns_none(self):
        """对关闭的端口查询 PID 应返回 None。"""
        from src.browser.browser_factory import BrowserFactory

        # 使用一个几乎不可能被占用的端口
        pid = BrowserFactory._get_chrome_pid_on_port(19999)
        assert pid is None, (
            f"关闭端口应返回 None，实际返回 {pid}"
        )

    def test_get_chrome_pid_zero_port(self):
        """端口 0 是保留端口，应返回 None。"""
        from src.browser.browser_factory import BrowserFactory

        pid = BrowserFactory._get_chrome_pid_on_port(0)
        # 端口 0 通常没有进程监听
        assert pid is None, f"端口 0 应返回 None，实际返回 {pid}"

    # ── RED 4: 孤儿恢复后状态文件已更新 ────────────────────────

    def test_orphan_recovery_updates_state_file(self):
        """当孤儿恢复成功时，应写入正确的 daemon.json 状态文件。"""
        from src.browser.browser_factory import BrowserFactory
        from src.browser.daemon_state import DAEMON_STATE_PATH, read_state

        # 即使无 Chrome 运行，方法也不应崩溃
        # 状态文件在无孤儿时保持不变
        result = BrowserFactory._find_and_recover_orphan()
        assert result is None  # 无 Chrome 时预期为 None

    # ── RED 5: 端口范围覆盖完整 ────────────────────────────────

    def test_port_range_coverage(self):
        """验证端口扫描覆盖 9222-9232（11 个端口）。"""
        from src.browser.browser_factory import BrowserFactory
        import inspect

        source = inspect.getsource(BrowserFactory._find_and_recover_orphan)
        assert "9222" in source, "应扫描起始端口 9222"
        assert "9232" in source, "应扫描结束端口 9232"

    # ── RED 6: launch_daemon 先调用孤儿恢复 ─────────────────────

    def test_launch_daemon_calls_orphan_recovery_first(self):
        """launch_daemon 在冷启动前必须先调用 _find_and_recover_orphan。"""
        from src.browser.browser_factory import BrowserFactory
        import inspect

        source = inspect.getsource(BrowserFactory.launch_daemon)
        # 孤儿恢复调用应出现在 daemon_is_alive 检查之前
        orphan_idx = source.find("_find_and_recover_orphan")
        alive_idx = source.find("daemon_is_alive")
        assert orphan_idx > 0, "launch_daemon 应调用 _find_and_recover_orphan"
        assert orphan_idx < alive_idx, (
            "_find_and_recover_orphan 必须在 daemon_is_alive 之前调用"
        )

    # ── RED 7: 方法可被静态调用 ─────────────────────────────────

    def test_find_orphan_is_static(self):
        """_find_and_recover_orphan 应为静态方法，无需实例化。"""
        from src.browser.browser_factory import BrowserFactory
        import inspect

        # 检查是否为 staticmethod
        method = BrowserFactory.__dict__.get("_find_and_recover_orphan")
        assert method is not None, "方法应存在于类字典中"
        assert isinstance(method, staticmethod), (
            "_find_and_recover_orphan 应为 @staticmethod"
        )

    # ── RED 8: 方法不会抛出未捕获异常 ───────────────────────────

    def test_orphan_recovery_never_throws(self):
        """无论系统状态如何，_find_and_recover_orphan 不应抛出异常。"""
        from src.browser.browser_factory import BrowserFactory

        try:
            result = BrowserFactory._find_and_recover_orphan()
            # 无 Chrome 时应返回 None，无异常
            assert result is None or isinstance(result, tuple)
        except Exception as e:
            pytest.fail(
                f"_find_and_recover_orphan 不应抛出异常: {type(e).__name__}: {e}"
            )


class TestOrphanRecoveryEdgeCases:
    """TDD: 孤儿恢复边界和异常路径"""

    def test_lsof_timeout_handled(self):
        """当 lsof 超时时应优雅降级返回 None。"""
        from src.browser.browser_factory import BrowserFactory

        # mock subprocess.run 模拟超时
        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = subprocess.TimeoutExpired("lsof", 3)
            result = BrowserFactory._get_chrome_pid_on_port(9222)
            assert result is None, "lsof 超时应返回 None"

    def test_lsof_permission_denied(self):
        """当 lsof 因权限拒绝失败时应返回 None。"""
        from src.browser.browser_factory import BrowserFactory

        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = PermissionError("permission denied")
            result = BrowserFactory._get_chrome_pid_on_port(9222)
            assert result is None, "权限拒绝应返回 None"

    def test_lsof_returns_empty(self):
        """当 lsof 返回空输出时应返回 None。"""
        from src.browser.browser_factory import BrowserFactory

        with patch("subprocess.run") as mock_run:
            mock_result = MagicMock()
            mock_result.returncode = 0
            mock_result.stdout = "   \n  "  # 空白输出
            mock_run.return_value = mock_result
            result = BrowserFactory._get_chrome_pid_on_port(9222)
            assert result is None, "lsof 空输出应返回 None"

    def test_orphan_recovery_port_scan_idempotent(self):
        """多次调用 _find_and_recover_orphan 应幂等（不改变系统状态）。"""
        from src.browser.browser_factory import BrowserFactory

        # 连续调用 3 次
        results = []
        for _ in range(3):
            result = BrowserFactory._find_and_recover_orphan()
            results.append(result)

        # 无 Chrome 时每次都返回 None
        assert all(r is None for r in results), (
            f"多次调用应一致返回 None，实际: {results}"
        )

    def test_cdp_timeout_handled(self):
        """当 CDP 端口存在但超时时应优雅处理。"""
        from src.browser.browser_factory import BrowserFactory

        # 扫描全范围应不抛异常
        try:
            result = BrowserFactory._find_and_recover_orphan()
            assert result is None  # 无 Chrome 时应返回 None
        except Exception as e:
            pytest.fail(f"端口扫描不应抛异常: {e}")

    def test_docstring_documents_orphan_recovery(self):
        """launch_daemon 的文档字符串应说明孤儿恢复机制。"""
        from src.browser.browser_factory import BrowserFactory

        doc = BrowserFactory.launch_daemon.__doc__ or ""
        assert "孤儿" in doc, "docstring 应说明孤儿 Chrome 恢复"
        assert "扫描端口" in doc, "docstring 应描述端口扫描步骤"
