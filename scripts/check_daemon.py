#!/usr/bin/env python3
"""ZeroSearch Session Start Hook — check Daemon status on Claude Code session start."""

import json
import os
import sys
from pathlib import Path

DAEMON_STATE = Path.home() / ".cache" / "zerosearch" / "daemon.json"

def check_pid_alive(pid: int) -> bool:
    """Check if a process with given PID is alive."""
    try:
        os.kill(pid, 0)
        return True
    except (OSError, ProcessLookupError):
        return False

def main():
    if not DAEMON_STATE.exists():
        print("[ZeroSearch] Daemon 状态文件不存在，首次搜索时将冷启动 Chrome (~5s)")
        return 0

    try:
        state = json.loads(DAEMON_STATE.read_text())
    except json.JSONDecodeError:
        print("[ZeroSearch] Daemon 状态文件损坏，下次搜索时将重建")
        DAEMON_STATE.unlink(missing_ok=True)
        return 1

    pid = state.get("pid")
    if not pid or not check_pid_alive(pid):
        print("[ZeroSearch] Daemon PID 不存活，下次搜索时将冷启动 Chrome (~5s)")
        DAEMON_STATE.unlink(missing_ok=True)
        return 1

    print(f"[ZeroSearch] Chrome Daemon 已运行 (PID: {pid})，搜索将使用热连接 (<1s)")
    return 0

if __name__ == "__main__":
    sys.exit(main())
