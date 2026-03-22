# ZeroSearch - API 参考文档

**版本**: 6.4.0
**更新日期**: 2026-03-22
**状态**: ✅ 已验证与实现一致

---

## 目录

1. [快速开始](#快速开始)
2. [SearchEngine](#searchengine)
3. [SearchResult](#searchresult)
4. [Citation](#citation)
5. [RateLimiter](#ratelimiter)
6. [RateLimitConfig](#ratelimitconfig)
7. [RateLimitMode](#ratelimitmode)
8. [FingerprintGenerator](#fingerprintgenerator)
9. [AntiBotDetector](#antibotdetector)
10. [CoolingManager](#coolingmanager)
11. [BrowserManager](#browsermanager)
12. [SessionManager](#sessionmanager)
13. [异常类](#异常类)
14. [常量和枚举](#常量和枚举)
15. [使用示例](#使用示例)

---

## 快速开始

### 基本用法

```python
from scripts import SearchEngine

# 连接真实 Chrome 浏览器
engine = SearchEngine(connect_port=9222)

# 执行搜索
result = engine.search("your query")

# 访问结果
print(result.summary)           # 页面摘要
print(result.url)              # 搜索结果 URL (注意: 不是 page_url)
for citation in result.citations:
    print(f"{citation.title}: {citation.url}")
```

### 导入方式

**推荐导入** (使用 `scripts/__init__.py`):
```python
from scripts import (
    SearchEngine,
    SearchResult,
    Citation,
    RateLimiter,
    RateLimitConfig,
    RateLimitMode,
    FingerprintGenerator,
    AntiBotDetector,
    CoolingManager,
    BrowserManager,
)
```

**直接导入** (不推荐):
```python
from scripts.search import SearchEngine
from scripts.rate_limiter import RateLimiter, RateLimitConfig, RateLimitMode
```

---

## SearchEngine

Google AI Mode 搜索引擎。

### 导入

```python
from scripts import SearchEngine
# 或
from scripts.search import SearchEngine
```

### 构造函数

```python
SearchEngine(
    connect_port: int = 9222,      # CDP 端口
    headless: bool = False,         # 是否无头模式
    state_path: Optional[Path] = None,  # 状态文件路径
    cdp_port: Optional[int] = None,      # CDP 端口 (同 connect_port)
    auto_connect: bool = True,            # 自动连接
    max_retries: int = 3                 # 最大重试次数
)
```

### 主要方法

#### `search(query: str, ...) -> SearchResult`

执行搜索并返回结果。

```python
result = engine.search(
    query="your search query",
    timeout: int = 40,              # AI Mode 超时 (秒)
    wait_time: int = 5,            # 页面加载等待时间
    headers: Optional[Dict] = None  # 自定义 HTTP 头
)
```

**参数**:
- `query` (str): 搜索查询字符串
- `timeout` (int, 默认 40): AI Mode 完成超时时间（秒）
- `wait_time` (int, 默认 5): 等待页面加载时间（秒）
- `headers` (Optional[Dict], 默认 None): 自定义 HTTP 请求头

**返回**:
- `SearchResult`: 搜索结果对象

**异常**:
- `SearchError`: 搜索失败
- `CAPTCHAError`: 检测到 CAPTCHA
- `AIModeNotAvailableError`: AI Mode 不可用

#### `search_batch(queries: List[str]) -> List[SearchResult]`

批量搜索（实验性功能）。

```python
results = engine.search_batch([
    "query 1",
    "query 2",
    "query 3"
])
```

### 示例

```python
from scripts import SearchEngine

engine = SearchEngine(connect_port=9222)

# 单次搜索
result = engine.search("Python best practices 2026")
print(f"摘要: {result.summary}")
print(f"引用数: {len(result.citations)}")

# 批量搜索
results = engine.search_batch([
    "React hooks tutorial",
    "Vue 3 composition API",
    "Angular signals"
])
for r in results:
    print(f"查询: {r.query}, 引用: {len(r.citations)}")
```

---

## SearchResult

表示完整搜索结果的数据类。

### 导入

```python
from scripts import SearchResult
# 或
from scripts.search import SearchResult
```

### 属性

| 属性 | 类型 | 描述 |
|------|------|------|
| `query` | `str` | 搜索查询 |
| `url` | `str` | 搜索结果页面 URL (**注意: 不是 page_url**) |
| `summary` | `str` | 页面摘要文本 |
| `citations` | `List[Citation]` | 引用列表 |
| `markdown_output` | `str` | 格式化的 Markdown 输出 |
| `ai_mode_available` | `bool` | AI Mode 是否可用 |
| `error_message` | `str` | 错误信息（如有） |
| `captcha_detected` | `bool` | 是否检测到 CAPTCHA |
| `rate_limit_wait` | `float` | 速率限制等待时间（秒） |

### ❌ 常见错误

```python
# ❌ 错误: 使用 page_url
print(result.page_url)  # AttributeError!

# ✅ 正确: 使用 url
print(result.url)
```

### 示例

```python
result = engine.search("machine learning basics")

# 访问属性
print(result.query)              # "machine learning basics"
print(result.url)               # "https://www.google.com/search?q=..."
print(result.summary)           # 页面摘要
print(result.ai_mode_available) # True/False

# 遍历引用
for citation in result.citations:
    print(f"[{citation.index}] {citation.title}")
    print(f"    URL: {citation.url}")
    print(f"    Context: {citation.context}")
```

---

## Citation

表示引用的数据类。

### 导入

```python
from scripts import Citation
# 或
from scripts.search import Citation
```

### 属性

| 属性 | 类型 | 描述 |
|------|------|------|
| `index` | `int` | 引用索引 |
| `url` | `str` | 引用来源 URL |
| `title` | `str` | 引用来源标题 |
| `context` | `str` | 引用上下文 |
| `source` | `str` | 来源站点名称 |

### ❌ 常见错误

```python
# ❌ 错误: 使用 ExtractedCitation
from scripts import ExtractedCitation  # ImportError!

# ✅ 正确: 使用 Citation
from scripts import Citation
```

### 示例

```python
result = engine.search("web development trends")

for citation in result.citations:
    print(f"引用 {citation.index}:")
    print(f"  标题: {citation.title}")
    print(f"  URL: {citation.url}")
    print(f"  上下文: {citation.context}")
```

---

## RateLimiter

搜索速率控制器，防止触发反爬虫机制。

### 导入

```python
from scripts import RateLimiter
# 或
from scripts.rate_limiter import RateLimiter
```

### 构造函数

```python
RateLimiter(config: Optional[RateLimitConfig] = None)
```

**注意**: 构造函数接受 `config` 参数，不是 `mode` 参数！

### 主要方法

#### `wait_if_needed() -> float`

如果需要，等待以维持最小间隔。

```python
# 在搜索前调用
wait_time = limiter.wait_if_needed()
# ... 执行搜索 ...
limiter.record_search()
```

**返回**: 等待时间（秒）

#### `record_search() -> None`

记录已执行搜索。

```python
limiter.record_search()
```

#### `get_next_wait_time() -> float`

获取下一个建议等待时间（不实际等待）。

```python
wait_time = limiter.get_next_wait_time()
```

**返回**: 建议等待时间（秒）

#### `get_status() -> dict`

获取当前速率限制器状态。

```python
status = limiter.get_status()
print(status)
# {
#     'mode': 'balanced',
#     'min_interval': 15.0,
#     'max_interval': 30.0,
#     'last_search_elapsed': 5.2,
#     'consecutive_rapid': 0,
#     'current_backoff': 10.0,
#     'needs_wait': True
# }
```

#### `reset() -> None`

重置速率限制器状态。

```python
limiter.reset()
```

### ❌ 常见错误

```python
# ❌ 错误: 使用 mode 参数
limiter = RateLimiter(mode=RateLimitMode.BALANCED)  # TypeError!

# ✅ 正确: 使用 config 参数
config = RateLimitConfig.from_mode(RateLimitMode.BALANCED)
limiter = RateLimiter(config=config)
```

```python
# ❌ 错误: 调用不存在的方法
limiter.wait_random()  # AttributeError!
limiter.get_next_interval()  # AttributeError!

# ✅ 正确: 使用正确的方法名
limiter.record_search()
limiter.get_next_wait_time()
```

### 便捷工厂函数

```python
from scripts.rate_limiter import create_rate_limiter, RateLimitMode

# 创建平衡模式限制器 (15-30秒)
limiter = create_rate_limiter()

# 创建保守模式限制器 (30-60秒)
limiter = create_rate_limiter(mode=RateLimitMode.CONSERVATIVE)

# 创建快速模式限制器 (5-15秒)
limiter = create_rate_limiter(mode=RateLimitMode.FAST)
```

### 示例

```python
from scripts import RateLimiter, RateLimitConfig, RateLimitMode

# 方式 1: 使用默认配置 (平衡模式)
limiter = RateLimiter()

# 方式 2: 使用配置对象
config = RateLimitConfig.from_mode(RateLimitMode.CONSERVATIVE)
limiter = RateLimiter(config=config)

# 方式 3: 使用工厂函数
limiter = create_rate_limiter(mode=RateLimitMode.BALANCED)

# 使用限制器
while True:
    wait_time = limiter.wait_if_needed()
    if wait_time > 0:
        print(f"等待 {wait_time:.1f} 秒...")

    # 执行搜索
    result = engine.search("query")

    # 记录搜索
    limiter.record_search()

    # 检查状态
    status = limiter.get_status()
    print(f"连续快速搜索: {status['consecutive_rapid']}")
```

---

## RateLimitConfig

速率限制配置数据类。

### 导入

```python
from scripts import RateLimitConfig
# 或
from scripts.rate_limiter import RateLimitConfig
```

### 属性

| 属性 | 类型 | 默认值 | 描述 |
|------|------|--------|------|
| `min_interval` | `float` | 15.0 | 最小间隔（秒） |
| `max_interval` | `float` | 30.0 | 最大间隔（秒） |
| `max_backoff` | `float` | 120.0 | 最大退避时间（秒） |
| `initial_backoff` | `float` | 10.0 | 初始退避时间（秒） |
| `backoff_multiplier` | `float` | 2.0 | 退避倍数 |
| `mode` | `RateLimitMode` | BALANCED | 限制模式 |

### 工厂方法

#### `from_mode(mode: RateLimitMode) -> RateLimitConfig`

从预定义模式创建配置。

```python
config = RateLimitConfig.from_mode(RateLimitMode.BALANCED)
```

**预定义模式**:
- `CONSERVATIVE`: 30-60 秒
- `BALANCED`: 15-30 秒 (默认)
- `FAST`: 5-15 秒

### 示例

```python
from scripts import RateLimitConfig, RateLimitMode

# 使用预定义模式
config = RateLimitConfig.from_mode(RateLimitMode.BALANCED)

# 自定义配置
config = RateLimitConfig(
    min_interval=10.0,
    max_interval=20.0,
    mode=RateLimitMode.FAST
)

limiter = RateLimiter(config=config)
```

---

## RateLimitMode

速率限制模式枚举。

### 导入

```python
from scripts import RateLimitMode
# 或
from scripts.rate_limiter import RateLimitMode
```

### 值

| 枚举值 | 描述 | 间隔范围 |
|--------|------|---------|
| `CONSERVATIVE` | 保守模式 | 30-60 秒 |
| `BALANCED` | 平衡模式 (默认) | 15-30 秒 |
| `FAST` | 快速模式 | 5-15 秒 |

### 示例

```python
from scripts import RateLimitMode

mode = RateLimitMode.BALANCED
print(mode.value)  # "balanced"
```

---

## FingerprintGenerator

随机浏览器指纹生成器。

### 导入

```python
from scripts import FingerprintGenerator
# 或
from scripts.fingerprint import FingerprintGenerator
```

### 构造函数

```python
FingerprintGenerator()
```

### 主要方法

#### `generate() -> Dict[str, Any]`

生成随机浏览器指纹。

```python
fingerprint = generator.generate()
# {
#     'user_agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)...',
#     'viewport': (1920, 1080),
#     'timezone': 'America/New_York',
#     'language': 'en-US',
#     'platform': 'MacIntel',
#     'vendor': 'Google Inc.',
#     'webgl_renderer': '...',
#     'canvas_fingerprint': '...'
# }
```

#### `get_random_user_agent() -> str`

获取随机 User-Agent。

```python
ua = generator.get_random_user_agent()
```

### 预定义池

```python
# User-Agent 池 (12个)
UA_POOL = [
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36...",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36...",
    # ... 共12个
]

# 视口池 (12个)
VIEWPORT_POOL = [
    (1920, 1080),
    (1366, 768),
    # ... 共12个
]

# 时区池 (26个)
TIMEZONE_POOL = [
    "America/New_York",
    "Europe/London",
    # ... 共26个
]

# 语言池 (25个)
LANGUAGE_POOL = [
    "en-US",
    "en-GB",
    # ... 共25个
]
```

### 示例

```python
from scripts import FingerprintGenerator

generator = FingerprintGenerator()

# 生成完整指纹
fingerprint = generator.generate()
print(f"User-Agent: {fingerprint['user_agent']}")
print(f"视口: {fingerprint['viewport']}")
print(f"时区: {fingerprint['timezone']}")
print(f"语言: {fingerprint['language']}")
```

---

## AntiBotDetector

反爬虫检测器（3层检测）。

### 导入

```python
from scripts import AntiBotDetector
# 或
from scripts.captcha_handler import AntiBotDetector
```

### 构造函数

```python
AntiBotDetector()
```

### 主要方法

#### `detect_static(url: str = "", body_text: str = "") -> CaptchaResult`

静态 CAPTCHA 检测（不需要浏览器）。

```python
result = detector.detect_static(
    url="https://www.google.com/search?q=...",
    body_text="页面文本内容"
)

if result.is_captcha:
    print(f"检测到 CAPTCHA: {result.message}")
    print(f"建议等待: {result.suggested_wait} 秒")
```

#### `detect_dynamic(page_html: str) -> CaptchaResult`

动态 CAPTCHA 检测（基于页面 HTML）。

```python
result = detector.detect_dynamic(page_html)
```

### 返回类型

```python
@dataclass
class CaptchaResult:
    is_captcha: bool      # 是否检测到 CAPTCHA
    message: str           # 检测消息
    captcha_type: str      # CAPTCHA 类型
    suggested_wait: float  # 建议等待时间（秒）
```

### 示例

```python
from scripts import AntiBotDetector

detector = AntiBotDetector()

# 检测搜索结果
result = detector.detect_static(
    url=search_result.url,
    body_text=search_result.summary
)

if result.is_captcha:
    print(f"⚠️ {result.message}")
    print(f"⏱️ 建议等待: {result.suggested_wait} 秒")
else:
    print("✅ 无 CAPTCHA")
```

---

## CoolingManager

渐进式冷却管理器。

### 导入

```python
from scripts import CoolingManager
# 或
from scripts.cooling_manager import CoolingManager
```

### 构造函数

```python
CoolingManager(
    cooldown_levels: List[float] = [1, 5, 15, 30, 60],  # 冷却级别（分钟）
    max_level: int = 5                                          # 最大冷却级别
)
```

### 主要方法

#### `notify_captcha() -> CoolingResult`

通知 CAPTCHA 被检测，增加冷却级别。

```python
result = manager.notify_captcha()
print(f"当前级别: {result.level}")
print(f"等待时间: {result.wait_minutes} 分钟")
```

#### `reset() -> None`

重置冷却级别。

```python
manager.reset()
```

### 返回类型

```python
@dataclass
class CoolingResult:
    level: int           # 当前冷却级别
    wait_minutes: float  # 等待时间（分钟）
    is_max_level: bool   # 是否达到最大级别
```

### 示例

```python
from scripts import CoolingManager

manager = CoolingManager()

# 检测到 CAPTCHA
result = manager.notify_captcha()
if result.is_max_level:
    print(f"⚠️ 已达到最大冷却级别!")
print(f"等待 {result.wait_minutes} 分钟后重试...")

# 重置
manager.reset()
```

---

## BrowserManager

浏览器管理器（agent-browser CLI 封装）。

### 导入

```python
from scripts import BrowserManager
# 或
from scripts.browser import BrowserManager
```

### 构造函数

```python
BrowserManager(
    headless: bool = False,
    cdp_port: Optional[int] = None,
    state_path: Optional[Path] = None,
    auto_connect: bool = True,
    timeout: int = 30
)
```

### 主要方法

#### `connect(port: int) -> bool`

连接到 Chrome 调试实例。

```python
success = browser.connect(9222)
```

#### `execute_command(command: str, timeout: int = 30) -> Dict[str, Any]`

执行 agent-browser 命令。

```python
result = browser.execute_command("goto https://example.com")
```

#### `take_snapshot(url: str) -> PageSnapshot`

获取页面快照。

```python
snapshot = browser.take_snapshot("https://example.com")
```

### 示例

```python
from scripts import BrowserManager

browser = BrowserManager(headless=False)

# 连接
if browser.connect(9222):
    print("✅ 已连接到 Chrome")

    # 执行命令
    result = browser.execute_command("goto https://google.com")
    print(f"页面标题: {result.get('title', 'N/A')}")

    # 关闭
    browser.close()
```

---

## SessionManager

会话管理器（状态持久化）。

### 导入

```python
from scripts import SessionManager
# 或
from scripts.session_manager import SessionManager
```

### 构造函数

```python
SessionManager(state_path: Optional[Path] = None)
```

### 主要方法

#### `save_state() -> None`

保存会话状态。

```python
manager.save_state()
```

#### `load_state() -> SessionState`

加载会话状态。

```python
state = manager.load_state()
```

### 示例

```python
from scripts import SessionManager

manager = SessionManager(state_path=Path("session.json"))

# 加载状态
state = manager.load_state()

# 修改状态
state.search_count += 1

# 保存状态
manager.save_state()
```

---

## 异常类

### SearchError

搜索基类异常。

```python
from scripts import SearchError

try:
    result = engine.search("query")
except SearchError as e:
    print(f"搜索错误: {e}")
```

### AIOverviewNotFoundError

AI Overview 未找到异常。

```python
from scripts import AIOverviewNotFoundError

try:
    result = engine.search("query")
except AIOverviewNotFoundError:
    print("AI Overview 未找到")
```

### AIModeNotAvailableError

AI Mode 不可用异常。

```python
from scripts import AIModeNotAvailableError

try:
    result = engine.search("query")
except AIModeNotAvailableError as e:
    print(f"AI Mode 不可用: {e.message}")
```

### CAPTCHAError

CAPTCHA 检测异常。

```python
from scripts import CAPTCHAError

try:
    result = engine.search("query")
except CAPTCHAError as e:
    print(f"CAPTCHA 检测: {e.message}")
    if e.captcha_result:
        print(f"建议等待: {e.captcha_result.suggested_wait} 秒")
```

### BrowserError

浏览器相关错误。

```python
from scripts import BrowserError

try:
    browser.connect(9222)
except BrowserError as e:
    print(f"浏览器错误: {e}")
```

### BrowserNotRunningError

浏览器未运行错误。

```python
from scripts import BrowserNotRunningError

try:
    browser.connect(9222)
except BrowserNotRunningError:
    print("请先启动 Chrome 并启用调试端口")
```

---

## 常量和枚举

### DEFAULT_PROFILE_DIR

默认 Profile 目录。

```python
from scripts import DEFAULT_PROFILE_DIR

print(DEFAULT_PROFILE_DIR)  # Path to ~/.cache/zero-search/chrome_profile
```

### DEFAULT_HEADERS

默认 HTTP 请求头。

```python
from scripts import DEFAULT_HEADERS

print(DEFAULT_HEADERS)
# {
#     'Accept-Language': 'en-US,en;q=0.9'
# }
```

### RateLimitMode (枚举)

见 [RateLimitMode](#ratelimitmode) 章节。

### 搜索相关常量

```python
from scripts.search import (
    CITATION_SELECTORS,        # 引用选择器列表
    AI_COMPLETION_TEXT_INDICATORS,  # AI 完成文本指示器
    AI_MODE_NOT_AVAILABLE,     # AI Mode 不可用文本
    CUTOFF_MARKERS             # 内容截断标记
)
```

---

## 使用示例

### 示例 1: 基本搜索

```python
from scripts import SearchEngine

engine = SearchEngine(connect_port=9222)
result = engine.search("Python programming")

print(f"摘要: {result.summary}")
print(f"引用数: {len(result.citations)}")
```

### 示例 2: 带速率限制的搜索

```python
from scripts import SearchEngine, RateLimiter, RateLimitConfig, RateLimitMode

engine = SearchEngine(connect_port=9222)
limiter = RateLimiter(config=RateLimitConfig.from_mode(RateLimitMode.BALANCED))

queries = ["Python", "JavaScript", "Rust", "Go"]

for query in queries:
    # 等待（如需要）
    limiter.wait_if_needed()

    # 搜索
    result = engine.search(query)
    print(f"{query}: {len(result.citations)} 引用")

    # 记录
    limiter.record_search()
```

### 示例 3: 批量搜索带冷却

```python
from scripts import SearchEngine, AntiBotDetector, CoolingManager

engine = SearchEngine(connect_port=9222)
detector = AntiBotDetector()
cooler = CoolingManager()

results = []
for query in queries:
    result = engine.search(query)

    # 检查 CAPTCHA
    captcha_check = detector.detect_static(result.url, result.summary)
    if captcha_check.is_captcha:
        cooler.notify_captcha()
        print(f"⚠️ 冷却 {cooler.current_wait()} 分钟")
        time.sleep(cooler.current_wait() * 60)
        continue

    results.append(result)
```

### 示例 4: 完整错误处理

```python
from scripts import (
    SearchEngine,
    SearchError,
    CAPTCHAError,
    AIModeNotAvailableError
)

engine = SearchEngine(connect_port=9222)

try:
    result = engine.search("query")

except CAPTCHAError as e:
    print(f"CAPTCHA 检测: {e.message}")
    print(f"建议等待: {e.captcha_result.suggested_wait} 秒")

except AIModeNotAvailableError as e:
    print(f"AI Mode 不可用: {e.message}")
    print("请使用 VPN 或更换地区")

except SearchError as e:
    print(f"搜索错误: {e}")

else:
    print(f"成功! 获得 {len(result.citations)} 个引用")
```

---

## 版本历史

| 版本 | 日期 | 变更 |
|------|------|------|
| 6.2.0 | 2026-03-22 | ✅ API 参考文档创建，与实现100%一致 |
| 6.1.0 | 2026-03-20 | 添加 Stealth Utils, Citation Enhanced, Html Converter |
| 5.1.0 | 2026-03-18 | 添加 AntiBot, RateLimiter, CoolingManager |
| 5.0.0 | 2026-03-15 | 初始 Phase 5 发布 |
| 2.0.0 | 2026-03-10 | Connect Mode 支持 |
| 1.0.0 | 2026-01-15 | 初始版本 |

---

## 已知问题

暂无。

## 常见问题

### Q: 为什么我的导入失败了？

**A**: 确保使用正确的模块名称：
- ❌ `ExtractedCitation` → ✅ `Citation`
- ❌ `result.page_url` → ✅ `result.url`

### Q: RateLimiter 如何选择模式？

**A**: 使用 `RateLimitConfig.from_mode()`:
```python
config = RateLimitConfig.from_mode(RateLimitMode.BALANCED)
limiter = RateLimiter(config=config)
```

### Q: 如何处理 CAPTCHA？

**A**: 使用 `AntiBotDetector` 和 `CoolingManager`:
```python
detector = AntiBotDetector()
cooler = CoolingManager()

# 检测
result = detector.detect_static(url, text)
if result.is_captcha:
    cooler.notify_captcha()
    time.sleep(result.suggested_wait)
```

---

**文档状态**: ✅ 已验证与实现一致
**最后更新**: 2026-03-22
**维护者**: Google AI Mode Skill Team
