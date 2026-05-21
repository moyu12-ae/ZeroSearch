"""Spike: 连接已有 Chrome Daemon (脚本 B)

验证 connect_over_cdp 是否能从独立 Python 进程连接到已有 Chrome 实例，
并检查反检测补丁是否持续生效。
"""

import sys
import os
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from patchright.sync_api import sync_playwright

DEBUG_PORT = 9222

p = sync_playwright().start()

try:
    print(f"[Connector] 正在连接 http://127.0.0.1:{DEBUG_PORT} ...")
    browser = p.chromium.connect_over_cdp(
        f"http://127.0.0.1:{DEBUG_PORT}",
        timeout=10000,
    )
    print(f"[Connector] ✅ 连接成功!")
    print(f"[Connector] Browser version: {browser.version}")
    print(f"[Connector] 已有 context 数: {len(browser.contexts)}")

    # 创建新页面
    page = browser.new_page()
    print(f"[Connector] ✅ new_page() 成功")

    # 检查反检测
    webdriver = page.evaluate("() => navigator.webdriver")
    print(f"[Connector] navigator.webdriver = {webdriver}")

    # 检查 Chrome runtime
    chrome = page.evaluate("() => !!(window.chrome && window.chrome.runtime)")
    print(f"[Connector] window.chrome.runtime 可用 = {chrome}")

    # 导航到 Google 测试
    print(f"[Connector] 正在导航到 Google...")
    try:
        page.goto(
            "https://www.google.com",
            wait_until="domcontentloaded",
            timeout=15000,
        )
        print(f"[Connector] ✅ 页面加载成功")
        print(f"[Connector] Page title: {page.title()}")

        # 检查是否有 CAPTCHA
        body_text = page.evaluate("() => document.body.innerText")
        has_captcha = "captcha" in body_text.lower() or "unusual traffic" in body_text.lower()
        if has_captcha:
            print(f"[Connector] ⚠️  可能触发了 CAPTCHA 验证")
        else:
            print(f"[Connector] ✅ 未检测到 CAPTCHA")
    except Exception as e:
        print(f"[Connector] ⚠️  导航失败: {e}")

    # 关闭标签页（不关闭浏览器）
    page.close()
    print(f"[Connector] page.close() 完成。标签页已关闭。")

    # 验证 Chrome 仍在运行
    time.sleep(1)
    connected = browser.is_connected()
    print(f"[Connector] Browser.is_connected() = {connected}")

    print(f"[Connector] --- 验证通过！connect_over_cdp 跨进程方案可行 ---")

except Exception as e:
    print(f"[Connector] ❌ 连接失败: {e}")
    import traceback
    traceback.print_exc()

finally:
    try:
        p.stop()
        print(f"[Connector] Playwright 已停止.")
    except Exception as e:
        print(f"[Connector] Playwright stop: {e}")
