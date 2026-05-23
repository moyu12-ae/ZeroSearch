"""
平台兼容抽象层 (Platform Abstraction Layer)

统一封装 Windows / macOS / Linux 平台差异：
- 进程管理 (terminate, kill, alive check, port→PID)
- 文件系统路径 (cache dir, config dir)
- 平台检测 (is_windows, is_unix)

调用方无需关心平台细节，通过此模块即可获得跨平台行为。
"""

from __future__ import annotations

import os
import signal
import subprocess
import sys
from pathlib import Path
from typing import Optional


# ── 平台检测 ──────────────────────────────────────────

def _is_windows() -> bool:
    """内部：检测是否为 Windows 平台"""
    return sys.platform == "win32"


def is_windows() -> bool:
    """公共：检测是否为 Windows 平台"""
    return _is_windows()


def is_unix() -> bool:
    """公共：检测是否为 Unix 平台 (macOS / Linux)"""
    return not _is_windows()


# ── 缓存/配置目录 ─────────────────────────────────────

def get_cache_dir() -> Path:
    """获取跨平台缓存目录。

    Unix:    ~/.cache/zerosearch/
    Windows: %LOCALAPPDATA%/zerosearch/
    """
    if is_windows():
        local_appdata = os.environ.get("LOCALAPPDATA", str(Path.home() / "AppData" / "Local"))
        return Path(local_appdata) / "zerosearch"
    return Path.home() / ".cache" / "zerosearch"


# ── 进程存活检测 ──────────────────────────────────────

def is_pid_alive(pid: int) -> bool:
    """跨平台检测 PID 是否存活。

    Unix:    os.kill(pid, 0) — 信号 0 不发送信号，仅检查权限/存活
    Windows: tasklist /FI "PID eq {pid}" 检查进程是否存在

    PID <= 0 为特殊值，始终返回 False。
    """
    if pid <= 0:
        return False
    if is_windows():
        try:
            result = subprocess.run(
                ["tasklist", "/FI", f"PID eq {pid}"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            return str(pid) in result.stdout
        except Exception:
            return False
    else:
        try:
            os.kill(pid, 0)
            return True
        except (OSError, ProcessLookupError):
            return False


# ── 进程终止 ──────────────────────────────────────────

def kill_process(pid: int, force: bool = False) -> None:
    """跨平台终止进程（按 PID）。

    Unix:    os.kill(pid, SIGTERM) 默认，force=True → SIGKILL
    Windows: taskkill /PID {pid} 默认，force=True → taskkill /F /PID {pid}

    所有异常内部吞掉，调用方不需要 try/except。
    """
    try:
        if is_windows():
            cmd = ["taskkill"]
            if force:
                cmd.append("/F")
            cmd.extend(["/PID", str(pid)])
            subprocess.run(cmd, capture_output=True, timeout=5)
        else:
            sig = signal.SIGKILL if force else signal.SIGTERM
            os.kill(pid, sig)
    except Exception:
        pass


def kill_process_tree(pid: int, force: bool = False) -> None:
    """跨平台终止进程树（父进程 + 子进程）。

    Unix:    pkill -P {pid}
    Windows: taskkill /T /PID {pid}

    用于清理孤儿 Chrome Helper / Renderer / GPU 子进程。
    """
    try:
        if is_windows():
            cmd = ["taskkill", "/T"]
            if force:
                cmd.append("/F")
            cmd.extend(["/PID", str(pid)])
            subprocess.run(cmd, capture_output=True, timeout=5)
        else:
            subprocess.run(
                ["pkill", "-P", str(pid)],
                capture_output=True,
                timeout=3,
            )
    except Exception:
        pass


# ── 端口查 PID ────────────────────────────────────────

def get_pid_on_port(port: int) -> Optional[int]:
    """跨平台获取监听指定 TCP 端口的进程 PID。

    Unix:    lsof -ti tcp:{port}
    Windows: netstat -ano -p tcp | findstr :{port}

    未找到则返回 None。
    """
    try:
        if is_windows():
            result = subprocess.run(
                ["netstat", "-ano", "-p", "tcp"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            for line in result.stdout.splitlines():
                parts = line.split()
                if len(parts) >= 5 and f":{port}" in parts[1]:
                    return int(parts[-1])
            return None
        else:
            result = subprocess.run(
                ["lsof", "-ti", f"tcp:{port}"],
                capture_output=True,
                text=True,
                timeout=3,
            )
            if result.returncode == 0 and result.stdout.strip():
                return int(result.stdout.strip().split("\n")[0])
            return None
    except Exception:
        return None


# ── Chrome 路径检测 ────────────────────────────────────

def find_chrome_path() -> Optional[Path]:
    """跨平台自动检测 Chrome 可执行文件路径。

    Windows: 从注册表 HKEY_LOCAL_MACHINE (fallback HKEY_CURRENT_USER) 读取。
    Unix:    检查 /Applications/Google Chrome.app (macOS) 和 PATH 中的 google-chrome。

    Returns:
        Chrome 可执行文件路径，找不到则返回 None。
    """
    if is_windows():
        try:
            import winreg
            for hive, name in [
                (winreg.HKEY_LOCAL_MACHINE, "HKLM"),
                (winreg.HKEY_CURRENT_USER, "HKCU"),
            ]:
                try:
                    with winreg.OpenKey(hive, r"SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\chrome.exe") as key:
                        chrome_path, _ = winreg.QueryValueEx(key, "")
                        if os.path.exists(chrome_path):
                            return Path(chrome_path)
                except (FileNotFoundError, OSError):
                    continue
        except Exception:
            pass
        return None
    else:
        # macOS
        mac_app = Path("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome")
        if mac_app.exists():
            return mac_app
        # Linux / FreeBSD: check PATH
        import shutil
        chrome_in_path = shutil.which("google-chrome") or shutil.which("google-chrome-stable")
        if chrome_in_path:
            return Path(chrome_in_path)
        return None


# ── 系统代理检测 ───────────────────────────────────────

def detect_system_proxy() -> Optional[str]:
    """跨平台检测系统代理设置。

    优先级:
    1. HTTP_PROXY / HTTPS_PROXY 环境变量
    2. Windows: netsh winhttp show proxy
    3. Windows: Internet Settings 注册表 (HKCU\\...\\Internet Settings)

    Returns:
        代理 URL 字符串 (e.g. "http://127.0.0.1:7890")，未检测到则返回 None。
    """
    # 1. 环境变量 (跨平台)
    for env_var in ("HTTPS_PROXY", "HTTP_PROXY", "https_proxy", "http_proxy"):
        value = os.environ.get(env_var)
        if value:
            return value

    # 2. Windows 系统代理
    if is_windows():
        # 2a. netsh winhttp show proxy
        try:
            result = subprocess.run(
                ["netsh", "winhttp", "show", "proxy"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            if result.returncode == 0:
                output = result.stdout
                if "Direct access" not in output:
                    import re
                    server_match = re.search(r"Proxy Server\(?s?\)?\s*:\s*(.+)", output)
                    if server_match:
                        server = server_match.group(1).strip()
                        if server and ":" in server:
                            return f"http://{server}" if "://" not in server else server
        except Exception:
            pass

        # 2b. 注册表 Internet Settings
        try:
            import winreg
            with winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\CurrentVersion\Internet Settings",
            ) as key:
                proxy_enable, _ = winreg.QueryValueEx(key, "ProxyEnable")
                if proxy_enable == 1:
                    proxy_server, _ = winreg.QueryValueEx(key, "ProxyServer")
                    if proxy_server and ":" in proxy_server:
                        return f"http://{proxy_server}" if "://" not in proxy_server else proxy_server
        except Exception:
            pass

    return None