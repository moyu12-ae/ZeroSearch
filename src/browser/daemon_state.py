"""
Daemon 状态文件管理

对齐 Architecture v3 §2.1 BrowserEngine。
提供 daemon.json 的原子读写、PID 存活检测、CDP 端口响应检测。
"""

import json
import os
import tempfile
import urllib.request
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

DAEMON_STATE_PATH = Path.home() / ".cache" / "zerosearch" / "daemon.json"


@dataclass
class DaemonState:
    """Daemon 状态快照"""

    pid: int
    cdp_port: int
    profile_path: str
    started_at: str  # ISO8601


def _ensure_dir() -> None:
    DAEMON_STATE_PATH.parent.mkdir(parents=True, exist_ok=True)


def write_state(pid: int, cdp_port: int, profile_path: str) -> None:
    """原子写入 Daemon 状态文件（临时文件 + rename，防竞态）"""
    _ensure_dir()
    state = DaemonState(
        pid=pid,
        cdp_port=cdp_port,
        profile_path=profile_path,
        started_at=datetime.now(timezone.utc).isoformat(),
    )
    # 写入临时文件，然后原子 rename
    tmp_fd, tmp_path = tempfile.mkstemp(
        dir=str(DAEMON_STATE_PATH.parent),
        prefix=".daemon_",
        suffix=".tmp",
    )
    try:
        with os.fdopen(tmp_fd, "w") as f:
            json.dump(asdict(state), f, indent=2)
        os.replace(tmp_path, str(DAEMON_STATE_PATH))
    except Exception:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
        raise


def read_state() -> Optional[DaemonState]:
    """读取 Daemon 状态文件。不存在或损坏则返回 None"""
    try:
        if not DAEMON_STATE_PATH.exists():
            return None
        with open(DAEMON_STATE_PATH, "r") as f:
            data = json.load(f)
        return DaemonState(
            pid=data["pid"],
            cdp_port=data["cdp_port"],
            profile_path=data["profile_path"],
            started_at=data.get("started_at", ""),
        )
    except (json.JSONDecodeError, KeyError, IOError):
        return None


def is_pid_alive(pid: int) -> bool:
    """检测 PID 是否存活（os.kill(pid, 0)）"""
    try:
        os.kill(pid, 0)
        return True
    except (OSError, ProcessLookupError):
        return False


def is_cdp_responsive(port: int, timeout: float = 2.0) -> bool:
    """检测 CDP 端口是否响应（HTTP GET /json/version）"""
    try:
        url = f"http://127.0.0.1:{port}/json/version"
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status == 200
    except Exception:
        return False


def cleanup_stale() -> None:
    """删除过期状态文件（PID 不存在或 CDP 无响应时调用）"""
    if not DAEMON_STATE_PATH.exists():
        return
    state = read_state()
    if state is not None and is_pid_alive(state.pid):
        return  # 文件有效，不清理
    # PID 不存活，清理状态文件
    try:
        DAEMON_STATE_PATH.unlink()
    except OSError:
        pass


def remove_state() -> None:
    """强制删除状态文件（stop 命令调用）"""
    try:
        if DAEMON_STATE_PATH.exists():
            DAEMON_STATE_PATH.unlink()
    except OSError:
        pass
