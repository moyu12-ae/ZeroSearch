<div align="center">

# ZeroSearch v0.2

### Claude Code 的 AI 增强搜索能力

Powered by **Patchright** (undetected Chromium — CDP-level anti-detection)

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/)
[![Claude Code Skill](https://img.shields.io/badge/Claude%20Code-Skill-purple.svg)](https://www.anthropic.com/news/skills)
[![Patchright](https://img.shields.io/badge/Patchright-v1.58-green.svg)](https://github.com/Kaliiiiiiiiii-Vinyzu/patchright)

</div>

---

## 这是什么

一个 Claude Code Skill，将 Google AI Mode（`udm=50`）搜索能力直接集成到 Claude Code 中。不同于普通搜索返回 10 个蓝色链接，Google AI Mode 自动综合 100+ 个网站内容，生成带来源引用的结构化回答。

**v0.2 亮点**：Patchright Chromium 引擎（CDP 协议级反检测）、真 Chrome Profile 复用（Google 登录继承）、系统代理自动继承、AI 原生精简输出。

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
AskUserQuestion → Chrome (Patchright) → Google AI Mode (udm=50) → AI 提取 → 精简 Markdown
```

| 系统 | 职责 | 性能预算 |
|------|------|:--:|
| **System 0: SKILL.md** | AskUserQuestion 交互、Profile 选择 | — |
| **BrowserEngine** | Patchright Chrome 生命周期、双 Profile 管理、反检测 | <5s 冷启动 |
| **SearchEngine** | 全流程编排、LRU 缓存 (50条/5min)、分级错误降级 | 编排层 |
| **ContentExtractor** | AI 完成检测、17 选择器引用提取、DOM + UI 噪音清洗 | <300ms |
| **MarkdownConverter** | HTML→Markdown 三库 Fallback、[1] 脚注、紧凑输出 | <200ms |

### 关键设计决策

- **Patchright Chromium**: CDP 协议级反检测（Runtime.enable / Console.enable 补丁），通过 Cloudflare/DataDome 验证
- **真 Chrome Profile**: 默认复用系统 Chrome（`channel="chrome"`），Google 登录继承，CAPTCHA 率 <1%
- **系统代理自动继承**: Chromium 原生读取 macOS 代理设置，零配置
- **pip 安装**: 无 Git Submodule，`pip install patchright` 一键升级
- **冷启动 + 有头模式**: 每次搜索启动可见 Chrome 窗口，搜索完自动关闭

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
├── tests/                # pytest (29 tests)
├── results/              # 搜索结果 (--save)
└── .anws/v2/             # 架构文档 (当前版本)
```

---

## 性能

| 指标 | 目标 | 实测 |
|------|:--:|:--:|
| 端到端搜索 (冷启动) | ≤5s | ~5s |
| 缓存命中 | <1ms | <0.001ms |
| CAPTCHA 触发率 (Option A) | <1% | Google 已登录用户 |
| CAPTCHA 触发率 (Option B) | <10% | 未登录 |

---

## CAPTCHA 处理

- **Option A (推荐)**: 复用真实 Chrome Profile，已登录 Google → CAPTCHA 几乎零触发
- **Option B**: 首次可能触发 CAPTCHA，浏览器窗口保持打开，手动验证后 Profile 记住

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
