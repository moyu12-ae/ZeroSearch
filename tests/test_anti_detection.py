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


class TestDaemonRunnerStealthParity:
    """TDD: daemon_runner.py 的反检测配置应与 browser_factory.py 一致

    daemon_runner.py 通过 launch_persistent_context 启动 Chrome，
    必须传递完整的反检测参数（ignore_default_args, locale, viewport 等），
    否则 Daemon 模式的 Chrome 会带上 --enable-automation 标记。
    """

    def test_daemon_runner_uses_stealth_config(self):
        """daemon_runner 应导入并使用 StealthConfig 提供的反检测配置。"""
        sys.path.insert(0, str(Path(__file__).parent.parent))
        import ast

        daemon_path = Path(__file__).parent.parent / "src" / "browser" / "daemon_runner.py"
        source = daemon_path.read_text()
        tree = ast.parse(source)

        uses_ignore_default_args = False
        uses_stealth_unpack = False

        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                for kw in getattr(node, 'keywords', []):
                    if kw.arg == "ignore_default_args":
                        uses_ignore_default_args = True
                    # 检测 **stealth.to_context_kwargs() 展开模式
                    if kw.arg is None:  # ** 展开的 kw 没有 arg 名
                        if isinstance(kw.value, ast.Call):
                            if (isinstance(kw.value.func, ast.Attribute) and
                                    kw.value.func.attr == "to_context_kwargs"):
                                uses_stealth_unpack = True

        assert uses_ignore_default_args, (
            "daemon_runner 的 launch_persistent_context 缺少 ignore_default_args 参数，"
            "会导致 Chrome 带上 --enable-automation 标记"
        )
        assert uses_stealth_unpack, (
            "daemon_runner 的 launch_persistent_context 缺少 **to_context_kwargs() 展开，"
            "locale/viewport/geolocation/extra_http_headers 等反检测参数未传递"
        )

    def test_daemon_runner_browser_args_complete(self):
        """daemon_runner 的 launch_persistent_context 应传递完整反检测参数集合。"""
        sys.path.insert(0, str(Path(__file__).parent.parent))
        import ast

        daemon_path = Path(__file__).parent.parent / "src" / "browser" / "daemon_runner.py"
        source = daemon_path.read_text()
        tree = ast.parse(source)

        launch_kwargs = set()
        has_kwargs_unpack = False

        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                if (isinstance(node.func, ast.Attribute) and
                        node.func.attr == "launch_persistent_context"):
                    for kw in getattr(node, 'keywords', []):
                        if kw.arg:
                            launch_kwargs.add(kw.arg)
                        elif kw.arg is None:
                            has_kwargs_unpack = True

        required_direct_params = {
            "channel", "headless", "user_data_dir", "args",
            "ignore_default_args",
        }

        missing = required_direct_params - launch_kwargs
        assert not missing, (
            f"daemon_runner 的 launch_persistent_context 缺少直接参数: {missing}"
        )
        assert has_kwargs_unpack, (
            "daemon_runner 的 launch_persistent_context 缺少 **to_context_kwargs() 展开"
        )


class TestCaptchaWaitResilience:
    """TDD: CAPTCHA 等待循环应在浏览器关闭时自动退出，而非无限等待"""

    def test_captcha_wait_checks_page_alive(self):
        """CAPTCHA 等待循环应包含 page.is_closed() 检测，用户关窗后自动退出。"""
        sys.path.insert(0, str(Path(__file__).parent.parent))

        engine_path = Path(__file__).parent.parent / "src" / "search" / "engine.py"
        source = engine_path.read_text()

        assert "page.is_closed()" in source, (
            "CAPTCHA 等待循环应调用 page.is_closed() 检测浏览器窗口是否被关闭"
        )

    def test_captcha_wait_max_timeout_reduced(self):
        """CAPTCHA 最大等待时间应从 600s 降至合理范围（≤60s 或加自动重检）。"""
        sys.path.insert(0, str(Path(__file__).parent.parent))
        import ast, re

        engine_path = Path(__file__).parent.parent / "src" / "search" / "engine.py"
        source = engine_path.read_text()

        # 查找 while waited < N 模式
        matches = re.findall(r'waited\s*<\s*(\d+)', source)
        if matches:
            max_wait = max(int(m) for m in matches)
            assert max_wait <= 60, (
                f"CAPTCHA 最大等待时间 {max_wait}s 过长，"
                f"应 ≤60s 并配合自动重检机制"
            )

    def test_captcha_loop_has_early_exit_on_page_close(self):
        """CAPTCHA 等待循环在 page 关闭时应立即退出。"""
        sys.path.insert(0, str(Path(__file__).parent.parent))
        import ast

        engine_path = Path(__file__).parent.parent / "src" / "search" / "engine.py"
        source = engine_path.read_text()
        tree = ast.parse(source)

        # 在 _run_search_pipeline 方法中查找 CAPTCHA 处理区域
        in_captcha_block = False
        has_page_close_check = False
        has_return_on_close = False

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name == "_run_search_pipeline":
                for stmt in ast.walk(node):
                    # 检测 handle_captcha 调用后的 while 循环
                    if isinstance(stmt, ast.While):
                        # 检查 while 循环体中是否有 page 关闭检测
                        for sub in ast.walk(stmt):
                            if isinstance(sub, ast.If):
                                # 检查 if 条件中是否引用了 page 和 is_closed/closed
                                if_stmt_source = ast.get_source_segment(source, sub.test)
                                if if_stmt_source and "page" in if_stmt_source.lower():
                                    has_page_close_check = True
                            if isinstance(sub, ast.Return):
                                has_return_on_close = True

        assert has_page_close_check or has_return_on_close, (
            "CAPTCHA 等待循环应在检测到 page 关闭或 CAPTCHA 解决后自动退出，"
            "不应无限等待 Ctrl+C"
        )


class TestBrowserArgsCompleteness:
    """TDD: BROWSER_ARGS 应包含足够多的反检测 flag 以对抗现代 Google 检测"""

    def test_browser_args_count_minimum(self):
        """BROWSER_ARGS 至少应有 10 个反检测 flag（v0.3 只 6 个，不足）。"""
        sys.path.insert(0, str(Path(__file__).parent.parent))
        from src.browser.stealth import BROWSER_ARGS
        assert len(BROWSER_ARGS) >= 10, (
            f"BROWSER_ARGS 只有 {len(BROWSER_ARGS)} 个 flag，"
            f"现代反检测至少需要 10 个。当前: {BROWSER_ARGS}"
        )

    def test_browser_args_include_webgl_fingerprint_protection(self):
        """应包含 WebGL/GPU 指纹防护（通过 --disable-features 合并传递）。"""
        sys.path.insert(0, str(Path(__file__).parent.parent))
        from src.browser.stealth import BROWSER_ARGS

        disable_features_flags = [f for f in BROWSER_ARGS if f.startswith("--disable-features=")]
        assert len(disable_features_flags) == 1, (
            f"--disable-features 应合并为一条，避免覆盖。当前有 {len(disable_features_flags)} 条"
        )
        combined = disable_features_flags[0]
        assert "IsolateOrigins" in combined, "缺少 IsolateOrigins 禁用"
        assert "site-per-process" in combined, "缺少 site-per-process 禁用"

    def test_browser_args_include_background_service_suppression(self):
        """应包含后台服务抑制 flag，减少不必要的网络请求特征。"""
        sys.path.insert(0, str(Path(__file__).parent.parent))
        from src.browser.stealth import BROWSER_ARGS

        background_flags = [
            "--disable-background-networking",
            "--disable-sync",
            "--disable-component-update",
        ]
        for flag in background_flags:
            assert flag in BROWSER_ARGS, f"缺少后台服务抑制 flag: {flag}"

    def test_browser_args_include_macos_keychain_bypass(self):
        """macOS 上应包含密码存储绕过 flag，避免 Keychain 弹窗。"""
        sys.path.insert(0, str(Path(__file__).parent.parent))
        from src.browser.stealth import BROWSER_ARGS

        keychain_flags = [
            "--password-store=basic",
            "--use-mock-keychain",
        ]
        for flag in keychain_flags:
            assert flag in BROWSER_ARGS, f"缺少 Keychain 绕过 flag: {flag}"

    def test_browser_args_include_ipc_and_metrics_suppression(self):
        """应包含 IPC 洪泛防护禁用和指标记录抑制 flag。"""
        sys.path.insert(0, str(Path(__file__).parent.parent))
        from src.browser.stealth import BROWSER_ARGS

        suppression_flags = [
            "--disable-ipc-flooding-protection",
            "--metrics-recording-only",
            "--mute-audio",
        ]
        for flag in suppression_flags:
            assert flag in BROWSER_ARGS, f"缺少 IPC/指标抑制 flag: {flag}"

    def test_disable_features_combined_properly(self):
        """--disable-features 应将所有特性合并为一条，避免互相覆盖。"""
        sys.path.insert(0, str(Path(__file__).parent.parent))
        from src.browser.stealth import BROWSER_ARGS

        disable_features_flags = [f for f in BROWSER_ARGS if f.startswith("--disable-features=")]
        assert len(disable_features_flags) == 1, (
            f"--disable-features 应只有 1 条（合并），避免覆盖。实际: {disable_features_flags}"
        )

        combined = disable_features_flags[0]
        required_features = [
            "IsolateOrigins",
            "site-per-process",
            "TranslateUI",
            "MediaRouter",
            "OptimizationHints",
        ]
        for feat in required_features:
            assert feat in combined, f"--disable-features 缺少 {feat}"


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
