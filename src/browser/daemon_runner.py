"""
Chrome Daemon 守护进程

由 BrowserFactory.launch_daemon() 通过 subprocess 启动。
使用 Patchright launch_persistent_context() 获取完整 CDP 级反检测补丁。
Chrome 存活期间，守护进程保持运行；守护进程退出时 Chrome 随 driver 关闭。

调用方式:
    python daemon_runner.py --port 9222 --profile /path --state /path/daemon.json
"""

import argparse
import json
import os
import signal
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

# 确保项目根在 path 中
_project_root = Path(__file__).resolve().parent.parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

from src.browser.stealth import BROWSER_ARGS


def _write_language_prefs(profile_path: str) -> None:
    """写入英文语言偏好"""
    pp = Path(profile_path)
    # Local State
    ls_path = pp / "Local State"
    ls = {}
    if ls_path.exists():
        try:
            ls = json.loads(ls_path.read_text())
        except (json.JSONDecodeError, IOError):
            pass
    ls.setdefault("app_locale", "en")
    ls.setdefault("accept_languages", "en-US,en")
    try:
        ls_path.write_text(json.dumps(ls, indent=2))
    except (IOError, OSError):
        pass
    # Preferences
    prefs_dir = pp / "Default"
    prefs_dir.mkdir(parents=True, exist_ok=True)
    prefs_path = prefs_dir / "Preferences"
    prefs = {}
    if prefs_path.exists():
        try:
            prefs = json.loads(prefs_path.read_text())
        except (json.JSONDecodeError, IOError):
            pass
    prefs.setdefault("accept_languages", "en-US,en")
    prefs.setdefault("selected_languages", "en-US,en")
    prefs.setdefault("intl", {}).setdefault("accept_languages", "en-US,en")
    prefs.setdefault("intl", {}).setdefault("selected_languages", "en-US,en")
    prefs.setdefault("translate", {}).setdefault("enabled", False)
    try:
        prefs_path.write_text(json.dumps(prefs, indent=2))
    except (IOError, OSError):
        pass


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, required=True)
    parser.add_argument("--profile", type=str, required=True)
    parser.add_argument("--state", type=str, required=True)
    args = parser.parse_args()

    port: int = args.port
    profile_path: str = args.profile
    state_file: str = args.state

    # 确保 profile 目录存在
    Path(profile_path).mkdir(parents=True, exist_ok=True)
    _write_language_prefs(profile_path)

    # 启动 Patchright + Chrome (完整 CDP 反检测)
    from patchright.sync_api import sync_playwright
    p = sync_playwright().start()

    ctx = p.chromium.launch_persistent_context(
        channel="chrome",
        headless=False,
        user_data_dir=profile_path,
        args=[
            f"--remote-debugging-port={port}",
            *BROWSER_ARGS,
        ],
        handle_sigint=False,
        handle_sigterm=False,
        handle_sighup=False,
        no_viewport=False,
    )

    # 写入状态文件
    state = {
        "pid": os.getpid(),
        "cdp_port": port,
        "profile_path": profile_path,
        "started_at": datetime.now(timezone.utc).isoformat(),
    }
    Path(state_file).parent.mkdir(parents=True, exist_ok=True)
    with open(state_file, "w") as f:
        json.dump(state, f, indent=2)

    # 优雅退出标志
    _shutdown = False

    def _handle_signal(signum, frame):
        nonlocal _shutdown
        _shutdown = True

    signal.signal(signal.SIGTERM, _handle_signal)
    signal.signal(signal.SIGINT, _handle_signal)

    print(f"[Daemon] Chrome 已启动, PID={os.getpid()}, 端口={port}", flush=True)

    # 保持运行，直到收到 SIGTERM/SIGINT 或被外部 kill
    try:
        while not _shutdown:
            time.sleep(1)
    finally:
        try:
            ctx.close()
        except Exception:
            pass
        try:
            p.stop()
        except Exception:
            pass
        try:
            Path(state_file).unlink(missing_ok=True)
        except OSError:
            pass


if __name__ == "__main__":
    main()
