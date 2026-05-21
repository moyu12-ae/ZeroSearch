<div align="center">

# ZeroSearch v0.3

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

```bash
# 1. 克隆
git clone https://github.com/moyu12-ae/ZeroSearch.git ~/.claude/skills/zerosearch

# 2. 进入目录
cd ~/.claude/skills/zerosearch

# 3. 安装
bash setup.sh

# 4. 在 Claude Code 中试试
# "/zerosearch React hooks 2026 best practices"
```

首次运行时会通过 `AskUserQuestion` 询问是否设为默认搜索工具。搜索使用独立 Chrome Profile，与日常 Chrome 隔离。

---

## 使用方式

### 在 Claude Code 中

直接说 "搜索 xxx" 或触发 `/zerosearch`，Skill 自动执行搜索并返回结构化结果。

### CLI 模式

```bash
# 基本搜索
python src/search/run.py --query "React hooks 2026" --profile ~/Library/Application\ Support/Google/Chrome/

# 保存结果 + 性能日志
python src/search/run.py --query "React hooks 2026" --save --debug --profile <path>

# 使用独立 Profile
python src/search/run.py --query "test" --fresh-profile
```

| 参数 | 说明 |
|------|------|
| `--query`, `-q` | 搜索查询字符串（必填） |
| `--profile <path>` | Chrome Profile 路径 |
| `--fresh-profile` | 使用独立空白 Profile |
| `--save` | 保存结果到 `results/` 目录 |
| `--debug` | 输出每环节性能日志 |
| `--reconfigure` | 重新选择 Profile 模式 |

---

## 技术架构

```
v0.3 Daemon:
  First search → subprocess Chrome → CDP connect → extract → close tab (Chrome stays)
  Later searches → CDP connect → create tab → extract → close tab (<1s)
```

| 系统 | 职责 | 性能预算 |
|------|------|:--:|
| **System 0: SKILL.md** | AskUserQuestion 交互、Daemon 启停触发 | — |
| **BrowserEngine** | subprocess Chrome 生命周期 + Daemon 状态管理、反检测 | <5s 冷启动 |
| **SearchEngine** | 全流程编排、Daemon 检测分支、LRU 缓存 (50条/5min)、分级错误降级 | 编排层 |
| **ContentExtractor** | AI 完成检测、17 选择器引用提取、DOM + UI 噪音清洗 | <300ms |
| **MarkdownConverter** | HTML→Markdown 三库 Fallback、[1] 脚注、紧凑输出 | <200ms |

### 关键设计决策

- **Chrome Daemon**: 首次冷启动后 Chrome 常驻，后续搜索 <1s。手动 `/zerosearch-stop` 或关窗停止
- **subprocess + CDP**: subprocess 启动独立 Chrome 进程，Patchright `connect_over_cdp` 连接
- **反检测**: `--disable-blink-features=AutomationControlled` 等 Chrome flags，独立 Profile
- **系统代理自动继承**: Chromium 原生读取 macOS 代理设置，零配置
- **pip 安装**: 无 Git Submodule，`pip install patchright` 一键升级
- **幽灵连接恢复**: 搜索中途 Chrome 崩溃自动检测 + 冷启动重试

---

## 项目结构

```
zerosearch/
├── SKILL.md              # System 0: Claude Code 技能入口
├── README.md             # 本文件
├── AGENTS.md             # AI 协作协议
├── LICENSE               # MIT 许可证
├── setup.sh              # 一键安装 (pip + chrome + CLAUDE.md 注册)
├── requirements.txt      # Python 依赖 (patchright>=1.55,<2)
├── src/
│   ├── browser/          # BrowserEngine (Patchright + Chrome)
│   ├── search/           # SearchEngine (CLI + 编排 + 缓存)
│   ├── extractor/        # ContentExtractor (AI 检测 + 引用 + 清洗)
│   └── converter/        # MarkdownConverter (HTML→MD + 脚注)
├── tests/                # pytest (45 tests)
├── results/              # 搜索结果 (--save)
└── .anws/v3/             # 架构文档 (当前版本)
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
| Chrome Profile 锁定 | 关闭所有 Chrome 窗口重试；或用 `--fresh-profile` |
| AI Mode 不可用 | 当前地区不支持，VPN 到美国/英国 |
| Profile 损坏 | 删除 `~/.cache/zerosearch/chrome_profile/` |
| 依赖安装失败 | 运行 `bash setup.sh` 重新创建 venv |

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

## v0.3 已完成

### 1. Chrome 持久化 Daemon ✅

首次冷启动后 Chrome 不关闭，后续搜索复用同一浏览器实例（只关标签页）。

| 维度 | v0.2 | v0.3 |
|------|------|------|
| 冷启动 | 每次 ~5s | 首次 ~5s，后续 <1s |
| 浏览器生命周期 | 搜索完关闭 | 只关标签页，Chrome 常驻 |
| 进程管理 | Patchright launch | subprocess 独立进程 + CDP connect |
| 崩溃恢复 | 无 | 幽灵连接检测 + 自动冷启动重试 |

## 后续版本计划

### Plugin 化

从单 Skill 升级为 Claude Code Plugin，功能拆分为独立命令：

```
/zerosearch        → 快速搜索（当前核心功能）
/zerosearch-init   → 初始化配置（Profile + 默认搜索工具注册）
/deepresearch      → 深度研究（多轮自动搜索，见下）
/zerosearch-crawl  → 开启引用爬取模式（见下）
```

### 3. Deep Research — 多轮深度搜索

类似 Google Deep Research，进行多轮自动搜索，逐步深入主题：

```
首轮搜索 → Claude 分析结果 → 生成追问 → 继续搜索 → 整合最终报告
```

- 可设定最大轮次（默认 3 轮）
- 每轮基于前一轮结果自动生成追问
- 最终产出整合报告 + 完整引用链

### 4. 引用网页爬取 + 本地剪藏

开启 `--crawl` 选项后，双 Agent 架构运行：

```
Agent A (搜索)
  Chrome → Google AI Mode → 保存 AI 摘要 + 提取引用链接列表
                              ↓
Agent B (爬取+剪藏)
  逐链打开 → 提取正文 → 保存为 Markdown 到 results/sources/
                              ↓
Final AI (跨文件阅读)
  Claude 同时阅读 AI 摘要 + 所有剪藏原文 → 综合输出
```

- **0 新依赖**：复用 Chrome Daemon + BeautifulSoup
- Agent B 在已有 Chrome 实例中并发多标签页爬取
- 每个链接 ~3-5s，并发后总耗时可控
- 剪藏格式为标准 Markdown，存入本地 `results/sources/`

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
