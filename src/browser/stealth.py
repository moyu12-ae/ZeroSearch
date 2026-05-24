"""
反检测配置 (Stealth Configuration)

对齐 Architecture v2 §2.1 BrowserEngine。
Chromium 自动继承系统代理，无需手动配置。
BROWSER_ARGS 借鉴原版 google-ai-mode-skill config.py。
"""

import random
import time
from dataclasses import dataclass, field


# 反检测 Chrome 启动参数 (模块级常量，StealthConfig 与 Daemon 共享)
BROWSER_ARGS = [
    "--disable-blink-features=AutomationControlled",
    "--disable-dev-shm-usage",
    "--no-first-run",
    "--no-default-browser-check",
    "--lang=en",
    "--disable-translate",
    # ── 扩展反检测 flag (v0.3.1) ──
    "--disable-background-networking",
    "--disable-sync",
    "--disable-component-update",
    "--password-store=basic",
    "--use-mock-keychain",
    "--disable-ipc-flooding-protection",
    "--metrics-recording-only",
    "--mute-audio",
    # 合并所有 --disable-features 为一条（避免互相覆盖）
    "--disable-features=IsolateOrigins,site-per-process,TranslateUI,MediaRouter,"
    "OptimizationHints,InterestFeedContentSuggestions,AudioServiceOutOfProcess",
]


@dataclass
class StealthConfig:
    """反检测配置 — 浏览器指纹伪装

    Patchright CDP 级反检测 (自动):
    - Runtime.enable 泄露修复
    - Console.enable 泄露修复
    - navigator.webdriver 移除

    显式配置:
    - Chromium 启动参数 (BROWSER_ARGS)
    - 语言强制英文 (Local State / Preferences — 由 BrowserFactory 处理)
    - 视口与地理位置
    """

    locale: str = "en-US"
    timezone_id: str = "America/New_York"

    viewport: dict = field(default_factory=lambda: {
        "width": 1280,
        "height": 800,
    })

    extra_http_headers: dict = field(default_factory=lambda: {
        "Accept-Language": "en-US,en;q=0.9",
        "Accept": (
            "text/html,application/xhtml+xml,"
            "application/xml;q=0.9,*/*;q=0.8"
        ),
    })

    geolocation: dict = field(default_factory=lambda: {
        "latitude": 40.7128,
        "longitude": -74.0060,
    })

    # Chromium 启动参数 (引用模块级常量)
    browser_args: list[str] = field(default_factory=lambda: list(BROWSER_ARGS))

    # 忽略的默认参数 (移除自动化标记)
    ignore_default_args: list = field(default_factory=lambda: [
        "--enable-automation",
        "--no-sandbox",  # macOS 不需要，Patchright 默认添加
    ])

    def to_context_kwargs(self) -> dict:
        """转换为传给 launch_persistent_context 的参数"""
        return {
            "locale": self.locale,
            "viewport": self.viewport,
            "geolocation": self.geolocation,
            "extra_http_headers": self.extra_http_headers,
        }


class StealthUtils:
    """人类行为模拟工具

    借鉴原版 google-ai-mode-skill browser_utils.py。
    提供随机延迟、字符级输入、拟人点击等辅助方法。
    """

    @staticmethod
    def random_delay(min_ms: int = 100, max_ms: int = 500) -> None:
        """随机延迟，模拟人类操作间隔"""
        time.sleep(random.uniform(min_ms, max_ms) / 1000)

    @staticmethod
    def human_type(page, selector: str, text: str) -> None:
        """拟人化键盘输入 — 字符间 25-75ms 延迟，5% 概率额外停顿

        Args:
            page: Playwright Page 对象
            selector: 目标元素 CSS 选择器
            text: 要输入的文本
        """
        element = page.query_selector(selector)
        if element:
            element.click()
        else:
            page.wait_for_selector(selector, timeout=2000)
            page.click(selector)

        for char in text:
            page.keyboard.type(char, delay=random.randint(25, 75))
            if random.random() < 0.05:
                time.sleep(random.uniform(0.15, 0.4))

    @staticmethod
    def realistic_click(page, selector: str) -> None:
        """拟人化点击 — 鼠标移动到元素中心 + 前后延迟

        Args:
            page: Playwright Page 对象
            selector: 目标元素 CSS 选择器
        """
        element = page.wait_for_selector(selector, timeout=5000)
        if element:
            box = element.bounding_box()
            if box:
                steps = 5
                for i in range(1, steps + 1):
                    px = box["x"] + (box["width"] * i / steps)
                    py = box["y"] + (box["height"] * i / steps)
                    page.mouse.move(px, py)
                    time.sleep(random.uniform(0.01, 0.03))

            time.sleep(random.uniform(0.1, 0.3))  # 点击前延迟
            element.click()
            time.sleep(random.uniform(0.1, 0.3))  # 点击后延迟
