"""
反检测配置 (Stealth Configuration)

对齐 browser-engine.md §8 反检测配置详解。
5 项显式配置 + 6 项 Camoufox 内置处理 + 系统代理自动检测。
"""

import subprocess
from dataclasses import dataclass, field


def detect_system_proxy() -> dict | None:
    """从 macOS 系统代理设置中读取 HTTP/HTTPS 代理。

    读取 scutil --proxy 输出，提取 HTTP/HTTPS 代理地址和端口。
    适用于 Shadowrocket、ClashX、V2Ray 等设置系统代理的工具。

    Returns:
        Playwright proxy dict (如 {"server": "http://127.0.0.1:1082"})，
        若未检测到代理则返回 None。
    """
    try:
        result = subprocess.run(
            ["scutil", "--proxy"],
            capture_output=True, text=True, timeout=5,
        )
        if result.returncode != 0:
            return None

        output = result.stdout.lower()
        proxy_host = None
        proxy_port = None

        # 解析 HTTP/HTTPS 代理 (优先 HTTPS)
        for proto in ("https", "http"):
            if f"{proto}enable : 1" in output:
                # 匹配 "httpsproxy : 127.0.0.1" 和 "httpsport : 1082"
                import re
                host_m = re.search(rf"{proto}proxy\s*:\s*(\S+)", output)
                port_m = re.search(rf"{proto}port\s*:\s*(\d+)", output)
                if host_m and port_m:
                    proxy_host = host_m.group(1)
                    proxy_port = int(port_m.group(1))
                    break

        if proxy_host and proxy_port:
            return {"server": f"http://{proxy_host}:{proxy_port}"}
    except Exception:
        pass
    return None


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
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:135.0) "
        "Gecko/20100101 Firefox/135.0"
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

    # 系统代理 (macOS 自动检测 Shadowrocket / ClashX 等)
    proxy: dict | None = field(default_factory=detect_system_proxy)

    def to_context_kwargs(self) -> dict:
        """转换为传给 NewBrowser / NewContext 的参数"""
        kwargs = {
            "user_agent": self.user_agent,
            "locale": self.locale,
            "viewport": self.viewport,
            "geolocation": self.geolocation,
            "extra_http_headers": self.extra_http_headers,
        }
        if self.proxy:
            kwargs["proxy"] = self.proxy
        return kwargs
