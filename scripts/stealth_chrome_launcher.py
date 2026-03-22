#!/usr/bin/env python3
"""
Stealth Chrome Launcher - 带反检测参数的 Chrome 启动器

这个脚本启动带有反检测参数的 Chrome，然后通过 CDP 端口连接。

关键参数:
- --disable-blink-features=AutomationControlled  # 隐藏自动化标志
- --no-first-run                                  # 跳过首次运行向导
- --lang=en-US                                   # 强制英语
"""

import subprocess
import os
import sys
import time
import argparse
from pathlib import Path

STEALTH_ARGS = [
    "--disable-blink-features=AutomationControlled",
    "--disable-dev-shm-usage",
    "--no-sandbox",
    "--no-first-run",
    "--no-default-browser-check",
    "--lang=en-US",
    "--disable-translate",
    "--disable-extensions",
    "--disable-plugins",
    "--disable-background-networking",
    "--disable-default-apps",
    "--disable-sync",
    "--metrics-recording-only",
    "--mute-audio",
    "--disable-background-timer-throttling",
    "--disable-backgrounding-occluded-windows",
    "--disable-renderer-backgrounding",
]

DEFAULT_CHROME_PATHS = {
    "darwin": "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "win32": "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe",
    "linux": "/usr/bin/google-chrome",
}


def find_chrome() -> str:
    """找到 Chrome 可执行文件路径"""
    platform = sys.platform

    if platform in DEFAULT_CHROME_PATHS:
        default_path = Path(DEFAULT_CHROME_PATHS[platform])
        if default_path.exists():
            return str(default_path)

    if platform == "darwin":
        paths = [
            "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
            "/Applications/Chromium.app/Contents/MacOS/Chromium",
            str(Path.home() / "Applications/Google Chrome.app/Contents/MacOS/Google Chrome"),
        ]
        for path in paths:
            if Path(path).exists():
                return path

    elif platform == "linux":
        paths = [
            "/usr/bin/google-chrome",
            "/usr/bin/chromium-browser",
            "/usr/bin/chromium",
            "/snap/bin/chromium",
        ]
        for path in paths:
            if Path(path).exists():
                return path

    raise FileNotFoundError("Chrome not found. Please install Google Chrome or Chromium.")


def launch_stealth_chrome(
    port: int = 9222,
    profile_dir: str = None,
    headless: bool = False,
    user_data_dir: str = None,
) -> subprocess.Popen:
    """
    启动带有反检测参数的 Chrome

    Args:
        port: CDP 端口 (默认 9222)
        profile_dir: Profile 目录路径
        headless: 是否无头模式
        user_data_dir: 用户数据目录

    Returns:
        subprocess.Popen 对象
    """
    chrome_path = find_chrome()

    if profile_dir:
        user_data_dir = profile_dir
    elif user_data_dir is None:
        user_data_dir = f"/tmp/chrome-stealth-{port}"

    user_data_path = Path(user_data_dir)
    user_data_path.mkdir(parents=True, exist_ok=True)

    args = [
        chrome_path,
        f"--remote-debugging-port={port}",
        f"--user-data-dir={user_data_path}",
        "--disable-blink-features=AutomationControlled",
        "--no-sandbox",
        "--no-first-run",
        "--no-default-browser-check",
        "--lang=en-US",
        "--disable-translate",
        "--disable-extensions",
        "--disable-plugins",
        "--disable-background-networking",
        "--disable-sync",
        "--mute-audio",
        "--disable-background-timer-throttling",
        "--disable-renderer-backgrounding",
    ]

    if headless:
        args.append("--headless=new")

    print(f"🚀 Launching stealth Chrome on port {port}...")
    print(f"   Chrome: {chrome_path}")
    print(f"   Profile: {user_data_path}")
    print(f"   Args: {' '.join(args[3:6])}...")

    process = subprocess.Popen(
        args,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    print(f"✅ Chrome launched (PID: {process.pid})")

    print("   Waiting for Chrome to be ready...")
    time.sleep(2)

    return process


def main():
    parser = argparse.ArgumentParser(description="Launch Chrome with stealth parameters")
    parser.add_argument("--port", "-p", type=int, default=9222, help="CDP port (default: 9222)")
    parser.add_argument("--profile", type=str, default=None, help="Profile directory")
    parser.add_argument("--headless", action="store_true", help="Run in headless mode")
    parser.add_argument("--user-data", type=str, default=None, help="User data directory")

    args = parser.parse_args()

    try:
        process = launch_stealth_chrome(
            port=args.port,
            profile_dir=args.profile,
            headless=args.headless,
            user_data_dir=args.user_data,
        )

        print(f"\n🎉 Stealth Chrome is running!")
        print(f"   CDP URL: http://localhost:{args.port}")
        print(f"   Process ID: {process.pid}")
        print(f"\nPress Ctrl+C to stop Chrome")

        process.wait()

    except FileNotFoundError as e:
        print(f"❌ Error: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n👋 Stopping Chrome...")
        process.terminate()
        process.wait()
        print("✅ Chrome stopped")


if __name__ == "__main__":
    main()
