# ZeroSearch - Trae 零成本网页搜索

<div align="center">

### 使用真实 Chrome 的零 Token 网页研究

将你的 Trae AI 助手变成研究利器——零 Token 开销、真实 Chrome 浏览、带可点击引用来源。

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![GitHub Workflow Status](https://img.shields.io/github/actions/workflow/status/moyu12-ae/ZeroSearch/ci.svg)](https://github.com/moyu12-ae/ZeroSearch/actions)
[![Version](https://img.shields.io/badge/Version-6.4.0-blue.svg)](https://github.com/moyu12-ae/ZeroSearch/releases)
[![GitHub stars](https://img.shields.io/github/stars/moyu12-ae/ZeroSearch.svg)](https://github.com/moyu12-ae/ZeroSearch/stargazers)
[![GitHub forks](https://img.shields.io/github/forks/moyu12-ae/ZeroSearch.svg)](https://github.com/moyu12-ae/ZeroSearch/network)
[![English version](https://img.shields.io/badge/English-English%20Version-blue.svg)](README_en.md)

**适用系统**: macOS、Linux 或 Windows (WSL) 的 Trae IDE 用户

</div>

---

## 为什么选择 ZeroSearch？

内置的网页研究功能通常会消耗大量 Token。ZeroSearch 通过连接你的真实 Chrome 浏览器，为 Trae 提供**专业级研究能力**——零 Token 开销、无验证码、完全复用登录会话。

### 示例结果

```
"Next.js 15 App Router 最佳实践 2026"
→ [Next.js 官方文档](https://nextjs.org) - 服务端组件完整指南
→ [Vercel 博客](https://vercel.com/blog) - 生产环境部署模式

"PostgreSQL vs MySQL JSON 性能对比 2026"
→ [PostgreSQL Wiki](https://wiki.postgresql.org) - JSONB 基准测试
→ [MySQL 博客](https://dev.mysql.com/blog) - JSON 函数对比

"欧盟 AI 法规 2026 对创业公司的影响"
→ [欧盟委员会](https://commission.europa.eu) - 官方文档
→ [TechCrunch](https://techcrunch.com) - 行业分析
```

**结果**: **任何主题**的研究——编程、技术对比、法律、产品、健康、金融。带引用的答案，高 Token 效率。

---

## 功能特性

| 功能 | 说明 |
|------|------|
| **零 Token 开销** | 使用真实 Chrome + CDP，Token 消耗极低 |
| **无验证码** | 使用你现有的 Google 登录状态 |
| **可点击引用** | 每个声明都带有 `[上下文](URL)` 格式的来源链接 |
| **多语言支持** | 自动检测 EN/DE/ZH/ES/FR/IT/NL 浏览器语言 |
| **会话持久化** | 持久化浏览器配置，减少验证码触发 |
| **错误恢复** | 自动重试，指数退避策略 |

---

## 安装

### 前置要求

- macOS、Linux 或 Windows (WSL)
- Python 3.8+
- Git

### 快速安装

```bash
# 克隆仓库
git clone <仓库-url>
cd ZeroSearch

# 运行安装脚本（安装 agent-browser CLI 和依赖）
./setup.sh
```

安装脚本自动完成：
- 安装 `agent-browser` CLI（Vercel 的 AI 原生浏览器自动化工具）
- 创建 Python 虚拟环境
- 安装依赖（beautifulsoup4）
- 设置持久化浏览器配置

### 手动安装

```bash
# 安装 agent-browser CLI
npm install -g agent-browser
agent-browser install

# 安装 Python 依赖
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

---

## 快速开始

### Python API

```python
from scripts import SearchEngine

# 初始化搜索引擎
engine = SearchEngine(profile="research")

# 执行搜索
result = engine.search("你的搜索查询")

# 获取带引用的 Markdown 输出
print(result.markdown_output)
```

### 输出示例

```markdown
## Next.js 15 App Router 最佳实践 2026

Next.js 15 引入了改进的服务端组件和流式渲染模式。主要改进包括：

- **服务端 Action** 现在支持[乐观更新](https://nextjs.org/docs/app/building-your-application/data-fetching/forms-and-mutations)，提升用户体验
- **流式渲染** 通过 Suspense 边界实现[渐进式渲染](https://react.dev/reference/react/Suspense)
- **缓存** 进行了[重新设计](https://nextjs.org/docs/app/building-your-application/caching)，提供更细粒度的 fetch 级别控制

**来源:**

- [Next.js 官方文档](https://nextjs.org)
- [React 官方文档](https://react.dev)
- [Vercel 博客](https://vercel.com/blog)
```

---

## 连接真实 Chrome（推荐）

连接到你的真实 Chrome 浏览器，使用现有的 Google 登录状态，避免验证码：

```python
from scripts import SearchEngine

# 使用保存的认证状态（最快）
engine = SearchEngine(state_path="~/.agent-browser/states/google.json")

# 或通过 CDP 端口连接
engine = SearchEngine(cdp_port=9222)

# 无需验证码搜索
result = engine.search("EVA 终 日本评价")
print(result.markdown_output)
```

### 设置认证状态

```bash
# 1. 启动带调试功能的 Chrome 并登录
python scripts/state_manager.py setup --name google

# 2. 保存认证状态
python scripts/state_manager.py save --name google

# 3. 测试搜索
python scripts/state_manager.py test --name google --query "你的搜索"
```

### 为什么使用真实 Chrome？

| 特性 | 无头浏览器 | 真实 Chrome |
|------|-----------|------------|
| 验证码 | 频繁触发 | 无（已登录） |
| 设置 | 即时 | 一次性设置 |
| 速度 | 快 | 快 |
| 隐私 | 好 | 使用你的浏览器数据 |

---

## 使用示例

### 查找库文档

```python
from scripts import SearchEngine

engine = SearchEngine(profile="docs")
result = engine.search(
    "Prisma ORM 2026（schema 定义、迁移、客户端 API、关系）。"
    "包含 TypeScript 示例。"
)
print(result.markdown_output)
```

### 获取代码示例

```python
result = engine.search(
    "WebSocket 实现 Node.js 2026（服务端设置、客户端连接、"
    "认证、重连逻辑）。生产级代码示例。"
)
```

### 技术对比

```python
result = engine.search(
    "GraphQL vs REST API 2026（性能、缓存、工具链、类型安全）。"
    "带基准测试数据的对比表。"
)
```

### 最佳实践研究

```python
result = engine.search(
    "微服务安全模式 2026（API 网关、mTLS、密钥管理、"
    "可观测性）。架构图。"
)
```

---

## 配置

### 配置管理

```python
from scripts import ProfileManager

# 创建持久化配置
profile_mgr = ProfileManager()
profile_path = profile_mgr.create(exist_ok=True)

# 搜索时使用
engine = SearchEngine(profile=str(profile_path))

# 如果损坏则重置
profile_mgr.reset()
```

### 语言选择

```python
from scripts import LanguageSelector, Language

# 自动检测（默认）
selector = LanguageSelector()

# 强制指定语言
selector = LanguageSelector(Language.GERMAN)

# 获取当前语言的引用选择器
citations = selector.get_citation_selectors()
```

### 错误处理

```python
from scripts import ErrorHandler, RetryConfig

# 配置重试行为
handler = ErrorHandler(
    RetryConfig(max_retries=2, base_delay=1.0, exponential_backoff=True)
)

# 检测 HTML 中的错误
error = handler.detect_error(html_content)
if error:
    print(handler.format_error_message(error))
```

---

## 故障排除

### 常见问题

| 问题 | 解决方案 |
|------|----------|
| `ModuleNotFoundError` | 运行 `./setup.sh` 或 `pip install -r requirements.txt` |
| 每次都验证码 | 首次手动完成验证，配置会持久化 |
| 找不到 AI 概述 | 用更具体的表述重新提问 |
| 浏览器启动失败 | 检查网络连接和 Chrome 安装 |
| AI Mode 不可用 | 地区不支持，使用 US/UK/DE 的 VPN |
| 配置损坏 | 运行 `ProfileManager().reset()` 重新创建 |

### 验证码处理

如果检测到验证码：

1. 使用 `--show-browser` 参数查看浏览器
2. 手动完成验证码
3. 配置会为后续搜索持久化

### 网络问题

```python
from scripts import ErrorHandler, RetryConfig

# 为不稳定连接增加重试次数
handler = ErrorHandler(RetryConfig(max_retries=5, base_delay=2.0))
```

---

## 架构

```
┌─────────────────────────────────────────────────────────┐
│                     Trae IDE                             │
└─────────────────────────────────────────────────────────┘
                            │
┌─────────────────────────────────────────────────────────┐
│                    SKILL 层                              │
│  (SKILL.md - 用户界面、查询模板)                        │
└─────────────────────────────────────────────────────────┘
                            │
┌─────────────────────────────────────────────────────────┐
│                  搜索逻辑层                              │
│  ┌─────────────────┐  ┌─────────────────┐              │
│  │ CitationExtractor│  │ LanguageSelector │              │
│  └─────────────────┘  └─────────────────┘              │
│  ┌─────────────────┐                                    │
│  │  ErrorHandler  │                                    │
│  └─────────────────┘                                    │
└─────────────────────────────────────────────────────────┘
                            │
┌─────────────────────────────────────────────────────────┐
│                 Agent Browser 层                         │
│  ┌─────────────────┐  ┌─────────────────┐              │
│  │ BrowserManager │  │ ProfileManager  │              │
│  └─────────────────┘  └─────────────────┘              │
└─────────────────────────────────────────────────────────┘
                            │
                    agent-browser CLI
                            │
                    Google Chrome
```

---

## API 参考

### SearchEngine

```python
class SearchEngine:
    def __init__(
        self,
        browser: Optional[BrowserManager] = None,
        profile: Optional[str] = None,
        wait_time: int = 2,
        max_retries: int = 2,
    )

    def search(self, query: str) -> SearchResult
```

### CitationExtractor

```python
class CitationExtractor:
    def __init__(self, max_citations: int = 20)
    def extract_from_html(self, html: str) -> List[ExtractedCitation]
    def to_markdown_list(self, citations: List[ExtractedCitation]) -> str
```

### LanguageSelector

```python
class LanguageSelector:
    def __init__(self, language: Optional[Language] = None)
    def detect_language() -> Language
    def get_citation_selectors() -> List[str]
```

### ErrorHandler

```python
class ErrorHandler:
    def __init__(self, retry_config: Optional[RetryConfig] = None)
    def detect_error(html: str) -> Optional[ErrorReport]
    def should_retry(error: ErrorReport) -> bool
```

---

## 退出码

| 代码 | 含义 |
|------|------|
| `0` | 成功 |
| `1` | 一般错误 |
| `2` | 需要验证码 |
| `3` | AI Mode 不可用 |
| `4` | 网络超时 |

---

## 贡献

欢迎贡献！请阅读 [AGENTS.md](AGENTS.md) 了解 AI 协作协议。

## 许可证

MIT 许可证 - 详见 [LICENSE](LICENSE) 文件。

---

## 相关项目

- [agent-browser](https://github.com/vercel/agent-browser) - AI 原生浏览器自动化 CLI
- [Google AI Mode MCP](https://github.com/PleasePrompto/google-ai-mode-mcp) - Claude Code MCP 替代方案

---

<div align="center">

**❤️ 为 Trae 社区构建**

</div>
