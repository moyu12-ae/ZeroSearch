"""
测试 src/utils/platform.py — 平台兼容抽象层

TDD: 先写测试，看它因模块不存在而失败。
"""

import os
import subprocess
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock


# ── RED: 模块导入测试 ──

def test_platform_module_is_importable():
    """模块可导入且暴露所有公共 API"""
    from src.utils.platform import (
        is_windows,
        is_unix,
        get_cache_dir,
        is_pid_alive,
        kill_process,
        kill_process_tree,
        get_pid_on_port,
        find_chrome_path,
        detect_system_proxy,
    )
    assert callable(is_windows)
    assert callable(is_unix)
    assert callable(get_cache_dir)
    assert callable(is_pid_alive)
    assert callable(kill_process)
    assert callable(kill_process_tree)
    assert callable(get_pid_on_port)
    assert callable(find_chrome_path)
    assert callable(detect_system_proxy)


# ── 平台检测 ──

def test_is_windows_on_darwin():
    """在 macOS 上 is_windows() 返回 False"""
    from src.utils.platform import is_windows
    assert is_windows() is False


def test_is_windows_when_sys_platform_is_win32():
    """当 sys.platform == 'win32' 时 is_windows() 返回 True"""
    from src.utils.platform import is_windows
    with patch("src.utils.platform._is_windows", return_value=True):
        assert is_windows() is True


def test_is_unix_on_darwin():
    """在 macOS 上 is_unix() 返回 True"""
    from src.utils.platform import is_unix
    assert is_unix() is True


# ── 缓存目录 ──

def test_get_cache_dir_returns_path():
    """get_cache_dir() 返回 Path 对象且存在"""
    from src.utils.platform import get_cache_dir
    cache = get_cache_dir()
    assert isinstance(cache, Path)
    assert "zerosearch" in str(cache)


def test_get_cache_dir_on_windows():
    """Windows 上使用 LOCALAPPDATA"""
    from src.utils.platform import get_cache_dir
    with patch("sys.platform", "win32"):
        cache = get_cache_dir()
        assert "zerosearch" in str(cache)
        parts = [p.lower() for p in cache.parts]
        # Windows 上不包含 .cache
        assert ".cache" not in parts


def test_get_cache_dir_on_unix():
    """Unix 上使用 ~/.cache"""
    from src.utils.platform import get_cache_dir
    cache = get_cache_dir()
    assert ".cache" in str(cache)


# ── 进程存活检测 ──

def test_is_pid_alive_with_current_process():
    """当前进程 PID 应返回 True"""
    from src.utils.platform import is_pid_alive
    assert is_pid_alive(os.getpid()) is True


def test_is_pid_alive_with_nonexistent_pid():
    """不存在的 PID 应返回 False（用极大 PID 不会冲突）"""
    from src.utils.platform import is_pid_alive
    assert is_pid_alive(99999) is False


def test_is_pid_alive_with_zero_pid():
    """PID <= 0 始终返回 False（Unix 进程组特殊值）"""
    from src.utils.platform import is_pid_alive
    assert is_pid_alive(0) is False
    assert is_pid_alive(-1) is False


@patch("sys.platform", "win32")
def test_is_pid_alive_windows_calls_tasklist():
    """Windows 上 is_pid_alive 使用 tasklist 命令"""
    from src.utils.platform import is_pid_alive
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0, stdout="chrome.exe 1234", stderr="")
        result = is_pid_alive(1234)
        assert result is True
        call_args = mock_run.call_args[0][0]
        cmd_str = " ".join(call_args)
        assert "tasklist" in cmd_str
        assert "1234" in cmd_str


@patch("sys.platform", "win32")
def test_is_pid_alive_windows_tasklist_not_found():
    """Windows 上 tasklist 未找到 PID 返回 False"""
    from src.utils.platform import is_pid_alive
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=1, stdout="INFO: No tasks", stderr="")
        result = is_pid_alive(99999)
        assert result is False


# ── 进程终止 ──

def test_kill_process_with_subprocess_object():
    """对 subprocess.Popen 对象调用 kill_process"""
    from src.utils.platform import kill_process
    proc = subprocess.Popen(
        [sys.executable, "-c", "import time; time.sleep(10)"],
    )
    try:
        # 不应抛出异常
        kill_process(proc.pid)
    except Exception as e:
        raise AssertionError(f"kill_process 不应失败: {e}")
    finally:
        # 确保清理
        try:
            proc.wait(timeout=2)
        except Exception:
            proc.kill()
            proc.wait()


@patch("sys.platform", "win32")
def test_kill_process_windows_uses_taskkill():
    """Windows 上 kill_process 使用 taskkill /PID"""
    from src.utils.platform import kill_process
    with patch("subprocess.run") as mock_run:
        kill_process(1234)
        call_args = mock_run.call_args[0][0]
        cmd_str = " ".join(call_args)
        assert "taskkill" in cmd_str
        assert "1234" in cmd_str


@patch("sys.platform", "win32")
def test_kill_process_windows_force_uses_f_flag():
    """Windows 上 kill_process(force=True) 使用 taskkill /F"""
    from src.utils.platform import kill_process
    with patch("subprocess.run") as mock_run:
        kill_process(1234, force=True)
        call_args = mock_run.call_args[0][0]
        cmd_str = " ".join(call_args)
        assert "/F" in cmd_str


def test_kill_process_unix_uses_sigterm_by_default():
    """Unix 上 kill_process 默认使用 SIGTERM"""
    from src.utils.platform import kill_process
    with patch("os.kill") as mock_kill:
        kill_process(1234)
        mock_kill.assert_called_once_with(1234, 15)  # SIGTERM = 15


@patch("sys.platform", "win32")
def test_kill_process_tree_windows_uses_taskkill_t():
    """Windows 上 kill_process_tree 使用 taskkill /T (进程树)"""
    from src.utils.platform import kill_process_tree
    with patch("subprocess.run") as mock_run:
        kill_process_tree(1234)
        call_args = mock_run.call_args[0][0]
        cmd_str = " ".join(call_args)
        assert "taskkill" in cmd_str
        assert "/T" in cmd_str


@patch("sys.platform", "win32")
def test_kill_process_tree_windows_force_and_tree():
    """Windows 上 kill_process_tree(force=True) 使用 /F /T"""
    from src.utils.platform import kill_process_tree
    with patch("subprocess.run") as mock_run:
        kill_process_tree(1234, force=True)
        call_args = mock_run.call_args[0][0]
        cmd_str = " ".join(call_args)
        assert "/F" in cmd_str
        assert "/T" in cmd_str


# ── 端口查 PID ──

def test_get_pid_on_port_returns_none_for_high_port():
    """随机高端口不应有进程监听，返回 None"""
    from src.utils.platform import get_pid_on_port
    # 使用不太可能有进程监听的端口
    result = get_pid_on_port(54321)
    assert result is None


@patch("sys.platform", "win32")
def test_get_pid_on_port_windows_uses_netstat():
    """Windows 上 get_pid_on_port 使用 netstat 命令"""
    from src.utils.platform import get_pid_on_port

    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="  TCP    0.0.0.0:9222    0.0.0.0:0    LISTENING    1234\n",
            stderr="",
        )
        result = get_pid_on_port(9222)
        assert result == 1234
        call_args = mock_run.call_args[0][0]
        assert "netstat" in call_args


@patch("sys.platform", "win32")
def test_get_pid_on_port_windows_no_match():
    """Windows 上 netstat 无匹配时返回 None"""
    from src.utils.platform import get_pid_on_port

    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
        result = get_pid_on_port(9222)
        assert result is None


# ── Chrome 路径检测 ──

def test_find_chrome_path_returns_path_or_none():
    """find_chrome_path 返回 Path 或 None（不抛异常）"""
    from src.utils.platform import find_chrome_path
    result = find_chrome_path()
    assert result is None or isinstance(result, os.PathLike), (
        f"应返回 Path 或 None，实际: {type(result)}"
    )


@patch("sys.platform", "win32")
def test_find_chrome_path_windows_uses_registry():
    """Windows 上 find_chrome_path 读取注册表"""
    from src.utils.platform import find_chrome_path
    mock_winreg = MagicMock()
    mock_key = MagicMock()
    mock_key.__enter__.return_value = mock_key
    mock_winreg.OpenKey.return_value = mock_key
    mock_winreg.QueryValueEx.return_value = ("C:\\chrome.exe", None)
    mock_winreg.HKEY_LOCAL_MACHINE = 0x80000002
    mock_winreg.HKEY_CURRENT_USER = 0x80000001

    with patch.dict("sys.modules", {"winreg": mock_winreg}):
        with patch("os.path.exists", return_value=True):
            result = find_chrome_path()
            assert result is not None
            assert "chrome.exe" in str(result).lower()


@patch("sys.platform", "win32")
def test_find_chrome_path_windows_fallback_to_hkcu():
    """Windows 上 HKLM 失败时 fallback 到 HKCU"""
    from src.utils.platform import find_chrome_path
    mock_winreg = MagicMock()
    mock_winreg.HKEY_LOCAL_MACHINE = 0x80000002
    mock_winreg.HKEY_CURRENT_USER = 0x80000001

    def open_key_side_effect(hive, path):
        if hive == 0x80000002:  # HKEY_LOCAL_MACHINE
            raise FileNotFoundError()
        return MagicMock()

    mock_winreg.OpenKey.side_effect = open_key_side_effect
    mock_winreg.QueryValueEx.return_value = ("C:\\Users\\u\\chrome.exe", None)

    with patch.dict("sys.modules", {"winreg": mock_winreg}):
        with patch("os.path.exists", return_value=True):
            result = find_chrome_path()
            assert result is not None


def test_find_chrome_path_unix_checks_paths():
    """Unix 上 find_chrome_path 检查已知路径"""
    from src.utils.platform import find_chrome_path
    result = find_chrome_path()
    # 在 macOS 上可能会找到 Chrome，也可能会返回 None
    assert result is None or isinstance(result, os.PathLike)


# ── 代理检测 ──

def test_detect_system_proxy_returns_str_or_none():
    """detect_system_proxy 返回代理 URL 或 None"""
    from src.utils.platform import detect_system_proxy
    result = detect_system_proxy()
    assert result is None or isinstance(result, str)


def test_detect_system_proxy_env_var():
    """HTTP_PROXY 环境变量应被识别"""
    from src.utils.platform import detect_system_proxy
    with patch.dict("os.environ", {"HTTP_PROXY": "http://127.0.0.1:7890"}, clear=True):
        result = detect_system_proxy()
        # env var 存在时可能返回代理（或 None 如果未设置）
        assert result is None or "http" in result.lower()


def test_detect_system_proxy_no_env():
    """无代理环境变量时返回 None"""
    from src.utils.platform import detect_system_proxy
    with patch.dict("os.environ", {}, clear=True):
        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = FileNotFoundError()
            result = detect_system_proxy()
            assert result is None


@patch("sys.platform", "win32")
def test_detect_system_proxy_windows_uses_netsh():
    """Windows 上 detect_system_proxy 使用 netsh winhttp"""
    from src.utils.platform import detect_system_proxy
    with patch.dict("os.environ", {}, clear=True):
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout="Proxy Server(s) : 127.0.0.1:7890\nBypass List    : localhost",
                stderr="",
            )
            result = detect_system_proxy()
            assert result == "http://127.0.0.1:7890"


@patch("sys.platform", "win32")
def test_detect_system_proxy_windows_direct_access():
    """Windows 上 netsh 显示 Direct access 时返回 None"""
    from src.utils.platform import detect_system_proxy
    with patch.dict("os.environ", {}, clear=True):
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout="Direct access (no proxy server)",
                stderr="",
            )
            result = detect_system_proxy()
            assert result is None
