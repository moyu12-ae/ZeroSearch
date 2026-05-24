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
        "width": random.randint(1024, 1920),
        "height": random.randint(768, 1080),
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
    """人类行为模拟工具 + 反指纹脚本注入

    借鉴原版 google-ai-mode-skill browser_utils.py。
    提供随机延迟、字符级输入、拟人点击、浏览器指纹覆盖等辅助方法。
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

    # ── 反指纹脚本注入 ─────────────────────────────────────────────

    @staticmethod
    def get_init_script() -> str:
        """生成反指纹 JavaScript 注入脚本。

        通过 page.add_init_script() 注入，在页面 JS 执行前覆盖浏览器指纹 API。
        每次调用重新随机化 hardwareConcurrency 值。
        覆盖向量:
        - navigator.plugins / mimeTypes → 伪造 PDF Viewer 插件
        - navigator.permissions.query → 对已知检测权限返回 granted
        - navigator.hardwareConcurrency → 4-8 随机值
        - WebGLRenderingContext + WebGL2RenderingContext.getParameter → 噪声 GPU 指纹
        - window.chrome.runtime → 确保存在（防止 Chrome 扩展 API 检测）
        """
        return _FINGERPRINT_SCRIPT_TEMPLATE % random.randint(4, 8)


# ── 反指纹 JavaScript 脚本模板 (%d = hardwareConcurrency, 每次调用时填充) ──

_FINGERPRINT_SCRIPT_TEMPLATE = """
(function() {
    'use strict';

    // 1. navigator.plugins — 伪造标准插件列表并赋值
    const _plugins = [
        {name: 'Chrome PDF Plugin', filename: 'internal-pdf-viewer', description: 'Portable Document Format'},
        {name: 'Chrome PDF Viewer', filename: 'mhjfbmdgcfjbbpaeojofohoefgiehjai', description: ''},
        {name: 'Native Client', filename: 'internal-nacl-plugin', description: ''},
    ];
    const pluginArray = Object.create(PluginArray.prototype);
    _plugins.forEach(function(p, i) {
        const plugin = Object.create(Plugin.prototype);
        Object.defineProperties(plugin, {
            name: {get: function() { return p.name; }},
            filename: {get: function() { return p.filename; }},
            description: {get: function() { return p.description; }},
            length: {value: 1},
        });
        pluginArray[i] = plugin;
    });
    Object.defineProperty(pluginArray, 'length', {value: _plugins.length});
    Object.defineProperty(navigator, 'plugins', {
        get: function() { return pluginArray; },
        configurable: true,
    });
    Object.defineProperty(navigator, 'mimeTypes', {
        get: function() { return pluginArray; },
        configurable: true,
    });

    // 2. navigator.permissions.query — 覆盖权限查询（守卫存在性）
    if (window.Permissions && window.Permissions.prototype) {
        var _origQuery = window.Permissions.prototype.query;
        window.Permissions.prototype.query = function(desc) {
            if (desc && desc.name) {
                var _blocked = ['midi', 'midi-sysex', 'usb', 'bluetooth', 'nfc', 'ambient-light-sensor'];
                if (_blocked.indexOf(desc.name) !== -1) {
                    return Promise.resolve({state: 'denied', onchange: null});
                }
            }
            return Promise.resolve({state: 'prompt', onchange: null});
        };
    }

    // 3. navigator.hardwareConcurrency — 每次调用随机化
    var _hwConcurrency = %d;
    Object.defineProperty(navigator, 'hardwareConcurrency', {
        get: function() { return _hwConcurrency; },
        configurable: true,
    });

    // 4. WebGL getParameter — 噪声 GPU 渲染器字符串 (WebGL 1.0 + 2.0)
    var _patchWebGL = function(ctxProto) {
        if (!ctxProto || !ctxProto.getParameter) return;
        var _origGetParam = ctxProto.getParameter;
        ctxProto.getParameter = function(p) {
            var result = _origGetParam.call(this, p);
            // UNMASKED_VENDOR_WEBGL (37445) / UNMASKED_RENDERER_WEBGL (37446)
            if (p === 37445 && typeof result === 'string') {
                return 'Google Inc. (Apple)';
            }
            if (p === 37446 && typeof result === 'string') {
                return 'ANGLE (Apple, ANGLE Metal Renderer: Apple M3, Unspecified Version)';
            }
            return result;
        };
    };
    _patchWebGL(WebGLRenderingContext.prototype);
    _patchWebGL(WebGL2RenderingContext.prototype);

    // 5. window.chrome.runtime — 确保存在
    if (!window.chrome) {
        window.chrome = {};
    }
    if (!window.chrome.runtime) {
        window.chrome.runtime = {
            id: undefined,
            getURL: function() { return ''; },
            connect: function() { return {onMessage: {addListener: function(){}}, onDisconnect: {addListener: function(){}}, postMessage: function(){}, disconnect: function(){}}; },
            sendMessage: function() {},
            onMessage: {addListener: function(){}},
            onConnect: {addListener: function(){}},
            lastError: undefined,
        };
    }

    // 6. Canvas 指纹 — toDataURL/toBlob 添加轻微噪声
    var _origToDataURL = HTMLCanvasElement.prototype.toDataURL;
    HTMLCanvasElement.prototype.toDataURL = function() {
        var ctx = this.getContext('2d');
        if (ctx) {
            var imageData = ctx.getImageData(0, 0, 1, 1);
            if (imageData && imageData.data) {
                imageData.data[0] = imageData.data[0] ^ 1;
                ctx.putImageData(imageData, 0, 0);
            }
        }
        return _origToDataURL.apply(this, arguments);
    };
    var _origToBlob = HTMLCanvasElement.prototype.toBlob;
    HTMLCanvasElement.prototype.toBlob = function(callback) {
        var ctx = this.getContext('2d');
        if (ctx) {
            var imageData = ctx.getImageData(0, 0, 1, 1);
            if (imageData && imageData.data) {
                imageData.data[0] = imageData.data[0] ^ 1;
                ctx.putImageData(imageData, 0, 0);
            }
        }
        return _origToBlob.apply(this, arguments);
    };

    // 7. AudioContext 指纹 — getChannelData 添加噪声
    var _origGetChannelData = AudioBuffer.prototype.getChannelData;
    AudioBuffer.prototype.getChannelData = function(channel) {
        var data = _origGetChannelData.call(this, channel);
        for (var i = 0; i < Math.min(data.length, 10); i++) {
            data[i] += (Math.random() - 0.5) * 1e-10;
        }
        return data;
    };

    // 8. navigator.deviceMemory — 伪造为常见值
    Object.defineProperty(navigator, 'deviceMemory', {
        get: function() { return 8; },
        configurable: true,
    });

    // 9. screen 属性 — 覆盖 colorDepth/pixelDepth
    Object.defineProperty(screen, 'colorDepth', {
        get: function() { return 24; },
        configurable: true,
    });
    Object.defineProperty(screen, 'pixelDepth', {
        get: function() { return 24; },
        configurable: true,
    });
})();
"""
