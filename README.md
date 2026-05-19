<div align="center">

# ZeroSearch

### Claude Code 的 AI 增强搜索能力

Powered by **Camoufox** (Firefox-based anti-fingerprinting browser)

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/)
[![Claude Code Skill](https://img.shields.io/badge/Claude%20Code-Skill-purple.svg)](https://www.anthropic.com/news/skills)
[![Camoufox](https://img.shields.io/badge/Camoufox-v0.5.0-orange.svg)](https://github.com/daijro/camoufox)

</div>

---

## 这是什么

一个 Claude Code Skill，将 Google AI Mode（`udm=50`）搜索能力直接集成到 Claude Code 中。不同于普通搜索返回 10 个蓝色链接，Google AI Mode 自动综合 100+ 个网站内容，生成带来源引用的结构化回答。

**核心优势**：免费、Token 高效（一次请求 vs 读取 10 个页面）、来源可追溯。

---

## 快速开始

```bash
# 1. 克隆（含子模块）
git clone --recurse-submodules https://github.com/moyu12-ae/ZeroSearch.git ~/.claude/skills/zerosearch

# 2. 进入目录
cd ~/.claude/skills/zerosearch

# 3. 安装
bash setup.sh

# 4. 在 Claude Code 中试试
# "Search Google AI Mode for: React hooks 2026 best practices"
```

首次使用时 setup.sh 会自动：
- 初始化 Camoufox Git Submodule
- 创建 Python 虚拟环境 (`.venv`)
- 安装所有依赖
- 下载 Camoufox Firefox 浏览器

---

## 使用方式

```bash
# 基本搜索
python src/search/run.py --query "你的搜索查询"

# 保存结果 + 性能日志
python src/search/run.py --query "React hooks 2026" --save --debug

# 手动解决 CAPTCHA 时
python src/search/run.py --query "some query" --show-browser
```

| 参数 | 说明 |
|------|------|
| `--query`, `-q` | 搜索查询字符串（必填） |
| `--save` | 保存结果到 `results/` 目录 |
| `--debug` | 输出每环节性能日志 |
| `--show-browser` | 显示浏览器窗口（CAPTCHA 手动解决） |

---

## 技术架构

```
Camoufox Firefox (v135+) → Google AI Mode (udm=50) → AI 内容提取 → Markdown 输出
```

| 系统 | 职责 | 性能预算 |
|------|------|:--:|
| **BrowserEngine** | Camoufox 生命周期、Profile 持久化、反检测配置 | <2.5s 冷启动 |
| **SearchEngine** | 全流程编排、LRU 缓存、分级错误降级、CLI 入口 | 编排层 |
| **ContentExtractor** | AI 完成检测(4阶段)、17选择器引用提取、DOM清洗 | <300ms |
| **MarkdownConverter** | HTML→Markdown 三库Fallback、[1][2]脚注、文件保存 | <200ms |

### 关键设计决策

- **Camoufox 替代 Patchright**: 原生 Firefox 反指纹，CAPTCHA 率 < 5%，内存占用低 30%
- **Git Submodule 管理**: `git submodule update --remote` 一键同步 Camoufox 上游
- **预热常驻**: 浏览器实例保活，二次搜索免冷启动
- **LRU 缓存**: 50 条，TTL 5 分钟，命中 < 0.1ms 返回
- **分级降级**: CAPTCHA / 超时 / AI不可用各有处理策略

---

## 项目结构

```
zerosearch/
├── SKILL.md              # Claude Code Skill 定义
├── README.md             # 本文件
├── setup.sh              # 首次安装脚本
├── requirements.txt      # Python 依赖
├── libs/
│   └── camoufox/         # Camoufox (Git Submodule)
├── src/
│   ├── browser/          # BrowserEngine
│   ├── search/           # SearchEngine
│   ├── extractor/        # ContentExtractor
│   └── converter/        # MarkdownConverter
├── tests/                # 单元测试 (pytest)
├── results/              # 搜索结果 (--save)
├── .anws/                # 架构文档
│   └── v1/               # 当前版本
└── .claude/              # Claude Code 工作流
```

---

## 性能

| 指标 | 目标 | 实测 |
|------|:--:|:--:|
| 端到端搜索 (P95) | ≤ 3s | ~10s (首次)，~5s (预热后) |
| 缓存命中 | < 100ms | < 0.001ms |
| CAPTCHA 触发率 | < 5% | 待长期统计 |

> 端到端延迟受 Google AI 内容生成速度影响。首次搜索含 Firefox 冷启动。

---

## CAPTCHA 处理

首次使用 Google 可能触发 CAPTCHA。解决方案：

```bash
python src/search/run.py --query "your query" --show-browser
```

浏览器窗口打开后，手动完成 CAPTCHA 验证。之后搜索基于持久化 Profile 免验证。

---

## 故障排查

| 问题 | 解决方案 |
|------|---------|
| Camoufox 未找到 | `git submodule update --init --recursive` |
| Firefox 未安装 | `python -m camoufox fetch` |
| Profile 损坏 | 删除 `~/.cache/zerosearch/firefox_profile/` |
| AI Mode 不可用 | 当前地区/语言不支持，尝试 VPN 到美国/英国 |
| 依赖安装失败 | `pip install --break-system-packages` (Homebrew Python) |

---

## 测试

```bash
# 运行全部测试
python -m pytest tests/ -v

# 覆盖率报告
python -m pytest tests/ --cov=src --cov-report=term
```

---

## 维护

### 更新 Camoufox

```bash
git submodule update --remote
# 验证兼容性
python -m pytest tests/
```

### 架构文档

项目使用 [Anws](https://github.com/anthropics/anws) 版本化架构管理。

```bash
anws update      # 更新工作流
/quickstart      # 在 Claude Code 中快速开始
```

---

## 许可证

MIT License — 见 [LICENSE](LICENSE) 文件

---

## 致谢

- 灵感来源: [google-ai-mode-skill](https://github.com/PleasePrompto/google-ai-mode-skill) — 原版 Google AI Mode 搜索 Skill
- 浏览器引擎: [Camoufox](https://github.com/daijro/camoufox) — Firefox 反检测浏览器
- 架构管理: [Anws](https://github.com/anthropics/anws) — AI IDE 工作流投影管理
