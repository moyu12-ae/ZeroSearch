#!/usr/bin/env python3
"""ZeroSearch Session Start Hook — check Daemon status on Claude Code session start."""

import json
import sys

# 确保项目根在 sys.path（与 daemon_runner 一致）
from pathlib import Path
_project_root = Path(__file__).resolve().parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

from src.utils.platform import get_cache_dir, is_pid_alive as check_pid_alive

DAEMON_STATE = get_cache_dir() / "daemon.json"

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
