"""Spike v5: subprocess 启动 Chrome + Patchright connect_over_cdp

直接用 subprocess 启动 Chrome（完全独立于 Patchright 生命周期），
传入反检测参数。后续用 Patchright connect_over_cdp 连接。
"""

import subprocess
import os
import time
import json
import sys
from datetime import datetime, timezone

CHROME_PATH = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
DEBUG_PORT = 9222
PROFILE_DIR = os.path.expanduser("~/.cache/zerosearch/chrome_profile/")
STATE_FILE = os.path.expanduser("~/.cache/zerosearch/daemon.json")

os.makedirs(PROFILE_DIR, exist_ok=True)
os.makedirs(os.path.dirname(STATE_FILE), exist_ok=True)

# 反检测参数 (来自 stealth.py StealthConfig.browser_args)
# 注意: CDP 补丁 (Runtime.enable/Console.enable) 无法通过命令行注入，
# 由 Patchright 在 launch 时自动处理。subprocess 方式缺失这些补丁，
# 本次 spike 验证仅靠浏览器 flags 是否足够。
ANTI_DETECT_ARGS = [
    "--disable-blink-features=AutomationControlled",
    "--disable-dev-shm-usage",
    "--no-first-run",
    "--no-default-browser-check",
    "--lang=en",
    "--disable-translate",
    # 用户 profile 中的语言偏好
]

cmd = [
    CHROME_PATH,
    f"--remote-debugging-port={DEBUG_PORT}",
    f"--user-data-dir={PROFILE_DIR}",
    *ANTI_DETECT_ARGS,
]

print(f"[Launcher] 启动 Chrome: {' '.join(cmd[:5])} ...", flush=True)

proc = subprocess.Popen(
    cmd,
    stdout=subprocess.DEVNULL,
    stderr=subprocess.DEVNULL,
    start_new_session=True,  # 脱离父进程
)

print(f"[Launcher] Chrome PID: {proc.pid}", flush=True)

# 等待 CDP 就绪
for i in range(15):
    time.sleep(1)
    try:
        import urllib.request
        resp = urllib.request.urlopen(
            f"http://127.0.0.1:{DEBUG_PORT}/json/version", timeout=2
        )
        data = json.loads(resp.read())
        print(f"[Launcher] ✅ CDP 就绪: {data.get('Browser', 'unknown')}", flush=True)
        break
    except Exception:
        if i == 14:
            print(f"[Launcher] ❌ CDP 超时", flush=True)
            proc.kill()
            sys.exit(1)
        print(f"[Launcher] 等待 CDP... ({i+1}/15)", flush=True)

# 写入状态文件
state = {
    "pid": proc.pid,
    "cdp_port": DEBUG_PORT,
    "profile_path": PROFILE_DIR,
    "started_at": datetime.now(timezone.utc).isoformat(),
}
with open(STATE_FILE, "w") as f:
    json.dump(state, f, indent=2)
print(f"[Launcher] 状态文件已写入: {STATE_FILE}", flush=True)
print(f"[Launcher] Launcher 退出，Chrome 独立运行", flush=True)
