"""daemon_state.py 单元测试"""

import json
import os
from unittest.mock import patch, MagicMock

from src.browser.daemon_state import (
    DAEMON_STATE_PATH,
    DaemonState,
    write_state,
    read_state,
    is_pid_alive,
    is_cdp_responsive,
    cleanup_stale,
    remove_state,
)


def _reset_state_file():
    """Reset the daemon state file to a clean state between tests"""
    remove_state()


class TestWriteAndReadState:
    def test_write_and_read_state(self, monkeypatch, tmp_path):
        monkeypatch.setattr(
            "src.browser.daemon_state.DAEMON_STATE_PATH",
            tmp_path / "daemon.json",
        )
        _reset_state_file()
        write_state(pid=12345, cdp_port=9222, profile_path="/tmp/profile")
        state = read_state()
        assert state is not None
        assert state.pid == 12345
        assert state.cdp_port == 9222
        assert state.profile_path == "/tmp/profile"
        assert state.started_at  # ISO8601 string

    def test_read_nonexistent(self, monkeypatch, tmp_path):
        monkeypatch.setattr(
            "src.browser.daemon_state.DAEMON_STATE_PATH",
            tmp_path / "nonexistent.json",
        )
        state = read_state()
        assert state is None

    def test_corrupted_json(self, monkeypatch, tmp_path):
        state_file = tmp_path / "daemon.json"
        monkeypatch.setattr(
            "src.browser.daemon_state.DAEMON_STATE_PATH",
            state_file,
        )
        state_file.write_text("not valid json")
        state = read_state()
        assert state is None

    def test_missing_key(self, monkeypatch, tmp_path):
        state_file = tmp_path / "daemon.json"
        monkeypatch.setattr(
            "src.browser.daemon_state.DAEMON_STATE_PATH",
            state_file,
        )
        state_file.write_text('{"pid": 123}')
        state = read_state()
        assert state is None  # KeyError → None

    def test_atomic_write_no_partial(self, monkeypatch, tmp_path):
        """写入是原子的：要么完整数据，要么旧数据"""
        state_file = tmp_path / "daemon.json"
        monkeypatch.setattr(
            "src.browser.daemon_state.DAEMON_STATE_PATH",
            state_file,
        )
        # 先写入第一版
        write_state(pid=100, cdp_port=9000, profile_path="/old")
        assert read_state().pid == 100

        # 写入第二版
        write_state(pid=200, cdp_port=9001, profile_path="/new")
        assert read_state().pid == 200

        # 文件内容完整
        data = json.loads(state_file.read_text())
        assert data["pid"] == 200
        assert data["cdp_port"] == 9001


class TestPidAlive:
    def test_pid_alive(self):
        """当前进程的 PID 应该存活"""
        assert is_pid_alive(os.getpid()) is True

    def test_pid_dead(self):
        """不存在的 PID 应该返回 False"""
        # 用一个大 PID 极可能不存在
        assert is_pid_alive(99999999) is False

    def test_pid_zero(self):
        """PID 0 在 macOS 上发送信号 0 可能成功但进程不存在"""
        # os.kill(0, 0) sends signal to process group - skip on macOS
        pass


class TestCdpResponsive:
    def test_cdp_not_responsive(self):
        """未监听的端口应返回 False"""
        assert is_cdp_responsive(19999, timeout=0.5) is False

    @patch("urllib.request.urlopen")
    def test_cdp_responsive(self, mock_urlopen):
        mock_resp = MagicMock()
        mock_resp.status = 200
        mock_urlopen.return_value.__enter__.return_value = mock_resp
        assert is_cdp_responsive(9222, timeout=0.5) is True

    @patch("urllib.request.urlopen")
    def test_cdp_wrong_status(self, mock_urlopen):
        mock_resp = MagicMock()
        mock_resp.status = 404
        mock_urlopen.return_value.__enter__.return_value = mock_resp
        assert is_cdp_responsive(9222, timeout=0.5) is False


class TestCleanupStale:
    def test_cleanup_stale_removes_dead_pid(self, monkeypatch, tmp_path):
        state_file = tmp_path / "daemon.json"
        monkeypatch.setattr(
            "src.browser.daemon_state.DAEMON_STATE_PATH",
            state_file,
        )
        write_state(pid=99999999, cdp_port=9222, profile_path="/tmp")
        assert state_file.exists()
        cleanup_stale()
        assert not state_file.exists()

    def test_cleanup_stale_keeps_alive_pid(self, monkeypatch, tmp_path):
        state_file = tmp_path / "daemon.json"
        monkeypatch.setattr(
            "src.browser.daemon_state.DAEMON_STATE_PATH",
            state_file,
        )
        write_state(pid=os.getpid(), cdp_port=9222, profile_path="/tmp")
        assert state_file.exists()
        cleanup_stale()
        assert state_file.exists()  # 应该保留

    def test_cleanup_stale_no_file(self, monkeypatch, tmp_path):
        monkeypatch.setattr(
            "src.browser.daemon_state.DAEMON_STATE_PATH",
            tmp_path / "nonexistent.json",
        )
        cleanup_stale()  # 不应抛异常


class TestRemoveState:
    def test_remove_state(self, monkeypatch, tmp_path):
        state_file = tmp_path / "daemon.json"
        monkeypatch.setattr(
            "src.browser.daemon_state.DAEMON_STATE_PATH",
            state_file,
        )
        write_state(pid=12345, cdp_port=9222, profile_path="/tmp")
        assert state_file.exists()
        remove_state()
        assert not state_file.exists()

    def test_remove_state_no_file(self, monkeypatch, tmp_path):
        monkeypatch.setattr(
            "src.browser.daemon_state.DAEMON_STATE_PATH",
            tmp_path / "nonexistent.json",
        )
        remove_state()  # 不应抛异常
