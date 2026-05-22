<div align="center">

# ZeroSearch v0.4

### Claude Code 的 AI 增强搜索能力

Powered by **Patchright** + **Chrome Daemon** (subprocess CDP — session-persistent browser)

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/)
[![Claude Code Skill](https://img.shields.io/badge/Claude%20Code-Skill-purple.svg)](https://www.anthropic.com/news/skills)
[![Patchright](https://img.shields.io/badge/Patchright-v1.58-green.svg)](https://github.com/Kaliiiiiiiiii-Vinyzu/patchright)

</div>

---

## 这是什么

一个 Claude Code Skill，将 Google AI Mode（`udm=50`）搜索能力直接集成到 Claude Code 中。不同于普通搜索返回 10 个蓝色链接，Google AI Mode 自动综合 100+ 个网站内容，生成带来源引用的结构化回答。

**v0.3 亮点**：Chrome Daemon 常驻（首次 ~5s，后续 <1s）、subprocess + CDP 分离架构、幽灵连接自动恢复、Patchright 反检测、独立 Profile、LRU 缓存、分级错误降级。

---

## 相比原版的优势

| 维度 | 原版 google-ai-mode-skill | ZeroSearch v0.3 |
|------|--------------------------|-----------------|
| **浏览器引擎** | Patchright + Chrome | Patchright + Chrome (守护进程模式) |
| **Daemon** | 无，每次冷启动 | **Chrome Daemon 常驻**，首次 ~5s，后续 <1s |
| **默认模式** | 无头 (headless) | **始终有头** (可见窗口，CAPTCHA 更少) |
| **反检测** | `--disable-blink-features` | CDP 协议级 (Patchright launch) + 守护进程 + StealthUtils |
| **缓存** | 无 | **LRU 50条 + TTL 5分钟**，重复查询 <1ms |
| **错误处理** | 无结构化降级 | **6 级退出码** + CAPTCHA/超时/AI不可用分级降级 + 幽灵连接自动恢复 |
| **输出** | 基础 Markdown + 引用 | **AI 原生精简**：90+ 模式去噪（中/英/日文）+ 紧凑脚注 |
| **首次体验** | 无引导 | **AskUserQuestion** 三选项引导（用户级/项目级/否） |
| **工作区集成** | 手动配置 | AskUserQuestion 引导注册 CLAUDE.md 搜索策略 |
| **测试** | 未知 | **45 自动化测试**，回归安全 |
| **架构文档** | 无 | 完整 PRD + ADR + 系统设计（.anws/v3/） |
| **CAPTCHA** | 手动切 `--show-browser` | 默认有头，`Ctrl+C` 继续，不切模式 |

> 原版 google-ai-mode-skill 是"能用"的 MVP，ZeroSearch v0.3 是**工程化的完整产品**——性能相当（~5s 冷启动，热搜索 <1s），可靠性、可维护性、AI 消费效率全面领先。

---

## 快速开始

### 方式一：Plugin 模式（推荐）

```bash
# 1. 安装依赖
cd zerosearch
bash setup.sh

# 2. 在 Claude Code 中加载 Plugin
claude --plugin-dir ./zerosearch

# 3. 首次运行配置
# 在 Claude Code 中输入
/zerosearch:zerosearch-config

# 4. 开始搜索
/zerosearch:zerosearch React hooks 2026 best practices
```

### 方式二：Standalone 模式

```bash
# 1. 克隆
git clone https://github.com/moyu12-ae/ZeroSearch.git ~/.claude/skills/zerosearch

# 2. 安装
cd ~/.claude/skills/zerosearch && bash setup.sh

# 3. 在 Claude Code 中触发
# "/zerosearch React hooks 2026 best practices"
```

首次运行时会通过 `AskUserQuestion` 询问是否设为默认搜索工具。搜索使用独立 Chrome Profile (`~/.cache/zerosearch/chrome_profile/`)，与日常 Chrome 隔离。

**系统要求**: Python ≥3.10, macOS（Chrome 自动继承系统代理）。

---

## 使用方式

### 在 Claude Code 中

直接说 "搜索 xxx" 即可触发。Plugin 模式下使用命名空间前缀：

| 命令 | 说明 |
|------|------|
| `/zerosearch:zerosearch <query>` | 香农策略优化查询 → Google AI Mode 搜索 |
| `/zerosearch:zerosearch-config` | 配置 Chrome Profile + 默认搜索工具注册 |
| `/zerosearch:zerosearch-start` | 手动启动 Chrome Daemon（预热） |
| `/zerosearch:zerosearch-stop` | 手动停止 Chrome Daemon（释放资源） |

### CLI 模式

```bash
# 基本搜索
python src/search/run.py --query "React hooks 2026"

# 保存结果 + 性能日志
python src/search/run.py --query "React hooks 2026" --save --debug

# Daemon 管理
python src/search/run.py --start    # 启动 Chrome Daemon
python src/search/run.py --stop     # 停止 Chrome Daemon
```

| 参数 | 说明 |
|------|------|
| `--query`, `-q` | 搜索查询字符串（必填） |
| `--start` | 启动 Chrome Daemon（不搜索） |
| `--stop` | 停止 Chrome Daemon |
| `--save` | 保存结果到 `results/` 目录 |
| `--debug` | 输出每环节性能日志 |

> Profile 管理通过 `/zerosearch:zerosearch-config` 或首次运行自动引导。

---

## 技术架构

```
v0.4 Plugin:
  /zerosearch:zerosearch → Shannon Strategy → Search Execution → Chrome Daemon → Google AI Mode
  /zerosearch:zerosearch-config → Profile + 默认搜索工具注册
  /zerosearch:zerosearch-start/stop → Daemon 手动启停
```

| 系统 | 职责 | 层 |
|------|------|:--:|
| **S0: Plugin Framework** | plugin.json + 4 命令 + hooks, AI 按需读取文件 | Markdown/JSON |
| **S1: Shannon Strategy** | 香农信息论搜索策略 (I(x) = -log₂P(x)), 纯提示词 | Markdown |
| **S2: Search Execution** | 搜索编排, 调用引擎, LRU 缓存, 错误降级 | Markdown + Python |
| **S3: Engine Runtime** | BrowserEngine + ContentExtractor + MarkdownConverter (v0.3 复用) | Python |

### 关键设计决策

- **Plugin 化**: 从单 SKILL.md → `.claude-plugin/plugin.json` + `commands/` + `skills/` + `hooks/`
- **香农提示词工程**: I(x) = -log₂P(x) 指导搜索查询构造，高信息量关键词替代通用词
- **统一搜索模式**: 单一 `/zerosearch:zerosearch` 入口，不做 Quick/Deep 分离
- **Chrome Daemon**: 首次冷启动 ~5s，热搜索 <1s。手动 `/zerosearch:zerosearch-stop` 或关窗停止
- **幽灵连接恢复**: Chrome 崩溃后下次搜索自动冷启动重建
- **零新依赖**: Python 引擎从 v0.3 完整复用

---

## 项目结构

```
zerosearch/
├── .claude-plugin/
│   └── plugin.json             # Plugin 声明
├── commands/                   # 命令定义 (AI 按需读取)
│   ├── zerosearch.md           # /zerosearch:zerosearch
│   ├── zerosearch-config.md    # /zerosearch:zerosearch-config
│   ├── zerosearch-start.md     # /zerosearch:zerosearch-start
│   └── zerosearch-stop.md      # /zerosearch:zerosearch-stop
├── skills/                     # Skill 定义
│   ├── shannon-strategy/
│   │   └── SKILL.md            # 香农搜索策略
│   └── search-execution/
│       └── SKILL.md            # 搜索执行引擎
├── hooks/
│   ├── hooks.json              # Hook 配置
│   └── scripts/                # Hook 脚本
├── src/                        # Python 引擎 (v0.3 复用)
│   ├── browser/                # BrowserEngine
│   ├── search/                 # SearchEngine
│   ├── extractor/              # ContentExtractor
│   └── converter/              # MarkdownConverter
├── tests/                      # pytest (45 tests)
├── setup.sh                    # 安装脚本
├── requirements.txt            # Python 依赖
└── .anws/v4/                   # 架构文档 (当前版本)
```

---

## 性能

| 指标 | 目标 | 实测 |
|------|:--:|:--:|
| 端到端搜索 (冷启动) | ≤5s | ~5s |
| 缓存命中 | <1ms | <0.001ms |
| CAPTCHA 触发率 (未登录) | <10% | 独立 Profile |
| CAPTCHA 触发率 (已登录 Google) | <1% | 登录后几乎零触发 |

---

## CAPTCHA 处理

ZeroSearch 使用独立 Chrome Profile（`~/.cache/zerosearch/chrome_profile/`）。首次搜索可能触发 CAPTCHA——浏览器窗口保持打开，手动验证后 Profile 记住登录状态，后续搜索 CAPTCHA 几乎零触发。

---

## 故障排查

| 问题 | 解决方案 |
|------|---------|
| Patchright 未找到 | 重新运行 `bash setup.sh` |
| Chrome 未安装 | `source .venv/bin/activate && python -m patchright install chrome` |
| Chrome Profile 锁定 | 关闭所有 Chrome 窗口重试；或用 `/zerosearch:zerosearch-config` 切换 Profile |
| AI Mode 不可用 | 当前地区不支持，VPN 到美国/英国；或回退到 WebFetch |
| Profile 损坏 | 删除 `~/.cache/zerosearch/chrome_profile/` |
| 依赖安装失败 | 运行 `bash setup.sh` 重新创建 venv |
| 每次搜索都 CAPTCHA | 在 Chrome 窗口中登录 Google 账号一次，Profile 记住登录后几乎零触发 |
| Plugin 命令无响应 | 检查 `.claude-plugin/plugin.json` 是否存在；运行 `/reload-plugins` |

**退出码**:

| 码 | 含义 |
|:--:|------|
| 0 | 成功 |
| 1 | 通用错误 |
| 2 | CAPTCHA 触发 |
| 3 | 浏览器关闭 |
| 4 | AI Mode 不可用 |
| 5 | Chrome Profile 锁定 |
| 130 | 用户中断 |

---

## v0.4 已完成

### 1. Plugin 化 ✅

从单 SKILL.md 升级为标准 Claude Code Plugin：

| 维度 | v0.3 | v0.4 |
|------|------|------|
| 架构入口 | 单 SKILL.md | .claude-plugin/plugin.json + 4 commands + 2 skills |
| AI 文件读取 | 读全部 SKILL.md (~136行) | 按需读取 (~110行/次) |
| 搜索策略 | 无（原样转发查询） | 香农信息论提示词工程 |
| 命令 | 1 个 (/zerosearch) | 4 个 (search/config/start/stop) |
| 模块化 | 追加式增长 | 独立文件，修改策略不改引擎 |

---

## 测试

```bash
python -m pytest tests/ -v             # 29 tests
python -m pytest tests/ --cov=src --cov-report=term
```

---

## 维护

```bash
# 更新 Patchright
source .venv/bin/activate && pip install --upgrade patchright

# 验证兼容性
python -m pytest tests/
```

---

## 许可证

MIT License — 见 [LICENSE](LICENSE) 文件

---

## 致谢

- 灵感来源: [google-ai-mode-skill](https://github.com/PleasePrompto/google-ai-mode-skill) — 原版 Google AI Mode 搜索 Skill
- 浏览器引擎: [Patchright](https://github.com/Kaliiiiiiiiii-Vinyzu/patchright) — Playwright undetected fork
- 架构管理: [Anws](https://github.com/anthropics/anws) — AI IDE 工作流投影管理
