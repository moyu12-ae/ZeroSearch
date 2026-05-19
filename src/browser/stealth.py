"""
反检测配置 (Stealth Configuration)

对齐 browser-engine.md §8 反检测配置详解。
5 项显式配置 + 6 项 Camoufox 内置处理。
"""

from dataclasses import dataclass, field


@dataclass
class StealthConfig:
    """反检测配置 — 浏览器指纹伪装

    Camoufox 内置反检测 (6 项):
    - WebGL 指纹随机化
    - Canvas 指纹随机化
    - 字体指纹随机化
    - AudioContext 指纹随机化
    - navigator 属性伪装
    - 自动化标记移除 (disable-automation-controlled)

    显式配置 (5 项):
    """

    user_agent: str = (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/125.0.0.0 Safari/537.36"
    )
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

    # Camoufox 会自动处理
    disable_automation_flags: bool = True

    # 模拟地理位置 (纽约)
    geolocation: dict = field(default_factory=lambda: {
        "latitude": 40.7128,
        "longitude": -74.0060,
    })

    def to_context_kwargs(self) -> dict:
        """转换为传给 NewBrowser / NewContext 的参数"""
        return {
            "user_agent": self.user_agent,
            "locale": self.locale,
            "viewport": self.viewport,
            "geolocation": self.geolocation,
            "extra_http_headers": self.extra_http_headers,
        }
