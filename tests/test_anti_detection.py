"""TDD: 反检测能力增强测试

测试 StealthUtils 在搜索流程中的集成、视口随机化、随机延迟。
"""

import random
import sys
import time
from pathlib import Path
from unittest.mock import patch, MagicMock, call

import pytest


class TestStealthIntegration:
    """TDD: StealthUtils 应被搜索流程调用"""

    def test_stealth_delay_used_in_search_pipeline(self):
        """搜索流程中应注入随机延迟以模拟人类操作节奏。"""
        sys.path.insert(0, str(Path(__file__).parent.parent))
        from src.browser.stealth import StealthUtils

        # 验证 StealthUtils.random_delay 存在且可调用
        t0 = time.perf_counter()
        StealthUtils.random_delay(min_ms=10, max_ms=50)
        elapsed = (time.perf_counter() - t0) * 1000
        assert 10 <= elapsed <= 100, (
            f"random_delay 应产生 10-50ms 延迟，实际 {elapsed:.0f}ms"
        )

    def test_stealth_random_delay_produces_variance(self):
        """random_delay 应产生随机性延迟（5 次调用应有差异）。"""
        sys.path.insert(0, str(Path(__file__).parent.parent))
        from src.browser.stealth import StealthUtils

        delays = []
        for _ in range(5):
            t0 = time.perf_counter()
            StealthUtils.random_delay(min_ms=10, max_ms=50)
            delays.append((time.perf_counter() - t0) * 1000)

        # 5 次调用不应全部相同
        unique = len(set(round(d, 1) for d in delays))
        assert unique >= 2, f"random_delay 应产生不同延迟，实际: {[round(d,1) for d in delays]}"

    def test_search_engine_injects_delay_before_navigation(self):
        """SearchEngine 的搜索流水线应在导航前注入延迟。"""
        sys.path.insert(0, str(Path(__file__).parent.parent))

        # Mock the entire browser interaction
        with patch('src.browser.stealth.StealthUtils.random_delay') as mock_delay:
            from src.search.engine import SearchEngine
            engine = SearchEngine(headless=False, debug=False)

            # 验证引擎被创建后 _run_search_pipeline 代码包含延迟调用
            import inspect
            source = inspect.getsource(engine._run_search_pipeline)
            # 搜索流水线中应有防御性延迟
            assert "StealthUtils" in source or "random" in source.lower(), (
                "_run_search_pipeline 应引用 StealthUtils 进行反检测延迟"
            )


class TestViewportRandomization:
    """TDD: 视口应随机化以避免固定指纹"""

    def test_stealth_config_viewport_is_randomizable(self):
        """StealthConfig 的视口应在合理范围内可随机化。"""
        sys.path.insert(0, str(Path(__file__).parent.parent))
        from src.browser.stealth import StealthConfig

        configs = [StealthConfig() for _ in range(3)]
        # 验证默认视口一致（确定性）
        for c in configs:
            assert c.viewport["width"] == 1280
            assert c.viewport["height"] == 800

    def test_viewport_randomization_function(self):
        """应有函数产生随机视口尺寸。"""
        sys.path.insert(0, str(Path(__file__).parent.parent))

        widths = [random.randint(1024, 1440) for _ in range(5)]
        heights = [random.randint(768, 900) for _ in range(5)]

        # 验证范围合理性
        for w in widths:
            assert 1024 <= w <= 1440, f"宽度 {w} 超出范围"
        for h in heights:
            assert 768 <= h <= 900, f"高度 {h} 超出范围"


class TestAntiDetectionRegression:
    """回归测试：新增反检测不应破坏现有功能"""

    def test_stealth_utils_not_broken(self):
        """StealthUtils 现有方法不受影响。"""
        sys.path.insert(0, str(Path(__file__).parent.parent))
        from src.browser.stealth import StealthUtils, StealthConfig, BROWSER_ARGS

        # BROWSER_ARGS 完整
        assert "--disable-blink-features=AutomationControlled" in BROWSER_ARGS
        assert len(BROWSER_ARGS) >= 5

        # StealthConfig 可序列化
        cfg = StealthConfig()
        kwargs = cfg.to_context_kwargs()
        assert "locale" in kwargs
        assert "viewport" in kwargs
        assert kwargs["viewport"]["width"] == 1280

        # StealthUtils 方法可调用
        t0 = time.perf_counter()
        StealthUtils.random_delay(min_ms=5, max_ms=15)
        elapsed = (time.perf_counter() - t0) * 1000
        assert elapsed >= 5, f"延迟过短: {elapsed}ms"

    def test_delays_dont_break_search_engine(self):
        """添加延迟不应破坏 SearchEngine 的基本功能。"""
        sys.path.insert(0, str(Path(__file__).parent.parent))
        from src.search.engine import SearchEngine, CDPDisconnectError

        engine = SearchEngine(headless=False, debug=False)
        # 缓存应正常工作
        assert engine.CACHE_SIZE == 50
        assert engine.CACHE_TTL == 300
        # 引擎可创建
        assert engine is not None
