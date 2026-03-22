"""
Fingerprint Generator - Phase 5 反爬虫规避系统

随机生成浏览器指纹参数，用于绕过 Google 反爬虫检测。

Author: Phase 5 Implementation
Version: 5.0.0
"""

import random
import hashlib
from dataclasses import dataclass, asdict
from typing import Optional, List
from datetime import datetime


class SeededRandom:
    """线程安全的随机数生成器，使用种子确保确定性"""

    def __init__(self, seed: Optional[int] = None):
        self._random = random.Random(seed)

    def choice(self, seq: List) -> any:
        return self._random.choice(seq)

    def sample(self, seq: List, k: int) -> List:
        return self._random.sample(seq, k)


@dataclass
class Fingerprint:
    """浏览器指纹数据结构"""
    user_agent: str
    viewport_width: int
    viewport_height: int
    timezone: str
    language: str
    platform: str
    vendor: str
    hardware_concurrency: int
    device_memory: int
    hash: Optional[str] = None

    def to_dict(self) -> dict:
        """转换为字典格式"""
        result = asdict(self)
        return result

    def __str__(self) -> str:
        return (
            f"Fingerprint("
            f"UA={self.user_agent[:50]}..., "
            f"Viewport={self.viewport_width}x{self.viewport_height}, "
            f"TZ={self.timezone}, "
            f"Lang={self.language}"
            f")"
        )


class FingerprintGenerator:
    """
    随机指纹生成器

    每次调用 generate() 生成一个随机的浏览器指纹配置，
    用于模拟不同用户的浏览器特征，降低被反爬虫检测的概率。

    使用方法:
        generator = FingerprintGenerator()
        fp = generator.generate()
        print(fp.user_agent, fp.viewport_width, fp.viewport_height)
    """

    UA_POOL: List[str] = [
        # macOS Chrome
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15",

        # Windows Chrome
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:123.0) Gecko/20100101 Firefox/123.0",

        # Linux Chrome
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
        "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:123.0) Gecko/20100101 Firefox/123.0",
    ]

    VIEWPORT_POOL: List[tuple] = [
        # 常见桌面分辨率
        (1920, 1080),
        (1920, 1200),
        (2560, 1440),
        (2560, 1600),
        (1366, 768),
        (1440, 900),
        (1280, 720),
        (1280, 800),
        (1600, 900),
        (1680, 1050),
        (1536, 864),
        (1024, 768),
    ]

    TIMEZONE_POOL: List[str] = [
        # 北美
        "America/New_York",
        "America/Chicago",
        "America/Denver",
        "America/Los_Angeles",
        "America/Toronto",
        "America/Vancouver",
        # 欧洲
        "Europe/London",
        "Europe/Paris",
        "Europe/Berlin",
        "Europe/Madrid",
        "Europe/Rome",
        "Europe/Amsterdam",
        "Europe/Stockholm",
        "Europe/Moscow",
        # 亚太
        "Asia/Tokyo",
        "Asia/Shanghai",
        "Asia/Hong_Kong",
        "Asia/Singapore",
        "Asia/Seoul",
        "Asia/Taipei",
        "Asia/Bangkok",
        "Australia/Sydney",
        "Australia/Melbourne",
        # 南美
        "America/Sao_Paulo",
        "America/Buenos_Aires",
        # 其他
        "Pacific/Auckland",
        "Asia/Dubai",
    ]

    LANGUAGE_POOL: List[str] = [
        # 常用语言组合
        "en-US",
        "en-GB",
        "en-CA",
        "en-AU",
        "de-DE",
        "de-AT",
        "de-CH",
        "fr-FR",
        "fr-CA",
        "es-ES",
        "es-MX",
        "es-AR",
        "pt-BR",
        "pt-PT",
        "it-IT",
        "ja-JP",
        "zh-CN",
        "zh-TW",
        "ko-KR",
        "ru-RU",
        "nl-NL",
        "pl-PL",
        "sv-SE",
        "tr-TR",
        "th-TH",
        "id-ID",
        "vi-VN",
    ]

    PLATFORM_POOL: List[str] = [
        "MacIntel",
        "Macintosh",
        "Win32",
        "Linux x86_64",
        "Linux armv8l",
    ]

    VENDOR_POOL: List[str] = [
        "Google Inc.",
        "Apple Computer, Inc.",
        "",
    ]

    HARDWARE_CONCURRENCY_POOL: List[int] = [2, 4, 6, 8, 12, 16]

    DEVICE_MEMORY_POOL: List[int] = [2, 4, 8, 16]

    def __init__(self, seed: Optional[int] = None):
        """
        初始化指纹生成器

        Args:
            seed: 可选的随机种子，用于测试目的
        """
        self._random = SeededRandom(seed)
        self._call_count = 0

    def generate(self) -> Fingerprint:
        """
        生成随机浏览器指纹

        Returns:
            Fingerprint: 包含所有指纹参数的 dataclass 对象

        示例:
            generator = FingerprintGenerator()
            fp = generator.generate()
            print(fp.user_agent)  # e.g., "Mozilla/5.0 (Macintosh; Intel Mac OS X..."
            print(fp.viewport_width, fp.viewport_height)  # e.g., "1920 1080"
        """
        self._call_count += 1

        user_agent = self._random.choice(self.UA_POOL)
        viewport = self._random.choice(self.VIEWPORT_POOL)
        timezone = self._random.choice(self.TIMEZONE_POOL)
        language = self._random.choice(self.LANGUAGE_POOL)
        platform = self._random.choice(self.PLATFORM_POOL)
        vendor = self._random.choice(self.VENDOR_POOL)
        hardware_concurrency = self._random.choice(self.HARDWARE_CONCURRENCY_POOL)
        device_memory = self._random.choice(self.DEVICE_MEMORY_POOL)

        fp = Fingerprint(
            user_agent=user_agent,
            viewport_width=viewport[0],
            viewport_height=viewport[1],
            timezone=timezone,
            language=language,
            platform=platform,
            vendor=vendor,
            hardware_concurrency=hardware_concurrency,
            device_memory=device_memory,
        )

        fp.hash = self._compute_hash(fp)

        return fp

    def _compute_hash(self, fp: Fingerprint) -> str:
        """计算指纹的哈希值，用于唯一标识"""
        content = (
            f"{fp.user_agent}|"
            f"{fp.viewport_width}x{fp.viewport_height}|"
            f"{fp.timezone}|"
            f"{fp.language}|"
            f"{datetime.now().isoformat()}"
        )
        return hashlib.md5(content.encode()).hexdigest()[:16]

    def generate_multiple(self, count: int) -> List[Fingerprint]:
        """
        批量生成多个不同的指纹

        Args:
            count: 需要生成的指纹数量

        Returns:
            List[Fingerprint]: 指纹列表
        """
        return [self.generate() for _ in range(count)]

    def get_call_count(self) -> int:
        """获取 generate() 被调用的次数"""
        return self._call_count

    def reset(self):
        """重置调用计数器"""
        self._call_count = 0


def demo():
    """演示指纹生成器的使用"""
    print("=" * 60)
    print("FingerprintGenerator 演示")
    print("=" * 60)

    generator = FingerprintGenerator()

    print("\n生成 3 个随机指纹:\n")

    for i in range(3):
        fp = generator.generate()
        print(f"指纹 {i + 1}:")
        print(f"  User-Agent: {fp.user_agent[:80]}...")
        print(f"  Viewport: {fp.viewport_width}x{fp.viewport_height}")
        print(f"  Timezone: {fp.timezone}")
        print(f"  Language: {fp.language}")
        print(f"  Platform: {fp.platform}")
        print(f"  Hardware: {fp.hardware_concurrency} cores, {fp.device_memory} GB")
        print(f"  Hash: {fp.hash}")
        print()

    print(f"总调用次数: {generator.get_call_count()}")


if __name__ == "__main__":
    demo()
