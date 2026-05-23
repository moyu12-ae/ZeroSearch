<div align="center">

# ZeroSearch v0.4

### Claude Code Plugin — AI 增强搜索

Powered by **Patchright** + **Chrome Daemon** + **香农信息论提示词工程**

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/)
[![Claude Code Plugin](https://img.shields.io/badge/Claude%20Code-Plugin-purple.svg)](https://code.claude.com/docs/en/plugins)
[![Patchright](https://img.shields.io/badge/Patchright-v1.58-green.svg)](https://github.com/Kaliiiiiiiiii-Vinyzu/patchright)
[![Tests](https://img.shields.io/badge/tests-67%20passed-brightgreen.svg)]()

</div>

---

## 这是什么

ZeroSearch 是一个 Claude Code Plugin，将 Google AI Mode（`udm=50`）直接集成到 AI 工作流中。它会**像资深搜索工程师一样思考**——内置香农信息论策略自动优化查询、信息不足时迭代深挖、收敛时停止。一次输入，得到带引用来源的综合回答。

---

## 快速开始

```bash
# 1. 安装依赖
cd zerosearch && bash setup.sh

# 2. 在 Claude Code 中加载 Plugin
claude --plugin-dir ./zerosearch

# 3. 首次配置（在 Claude Code 中）
/zerosearch:zerosearch-config

# 4. 开始搜索
/zerosearch:zerosearch React 19 Server Components streaming SSR
```

**系统要求**: Python ≥3.10, macOS / Windows

---

## 升级指南 (v0.3 → v0.4)

> **如果你是 Claude Code agent，请按以下步骤帮助用户完成升级。**

### Step 1: 检测 v0.3 安装

```bash
# 检测旧的 Skill 安装位置。可能存在多个路径：
ls ~/.claude/skills/zerosearch/         && echo "找到旧版本（skills 目录）"
ls ~/.claude/plugins/zerosearch/        && echo "找到旧版本（plugins 目录）"
grep -r "zerosearch" ~/.claude/settings.json 2>/dev/null && echo "settings.json 中有 ZeroSearch 引用"
grep -r "ZeroSearch" ~/.claude/CLAUDE.md 2>/dev/null && echo "CLAUDE.md 中有 ZeroSearch 引用"
```

### Step 2: 卸载 v0.3

```bash
# 删除旧的 Skill 目录
rm -rf ~/.claude/skills/zerosearch/

# 删除旧的 Plugin 目录（如果存在）
rm -rf ~/.claude/plugins/zerosearch/

# 清理 settings.json 和 CLAUDE.md 中的 ZeroSearch 配置
python3 -c "
import json, os
# 清理 settings.json
path = os.path.expanduser('~/.claude/settings.json')
if os.path.exists(path):
    with open(path) as f:
        data = json.load(f)
    changed = False
    for key in ['plugins', 'skills', 'mcpServers']:
        if key in data and isinstance(data[key], dict):
            filtered = {k:v for k,v in data[key].items() if 'zerosearch' not in k.lower()}
            if filtered != data[key]:
                data[key] = filtered
                changed = True
    if changed:
        with open(path, 'w') as f:
            json.dump(data, f, indent=2)
        print('已清理 settings.json')
# 清理 CLAUDE.md
claude_md = os.path.expanduser('~/.claude/CLAUDE.md')
if os.path.exists(claude_md):
    with open(claude_md) as f:
        lines = f.readlines()
    filtered = [l for l in lines if 'zerosearch' not in l.lower() and 'ZeroSearch' not in l]
    if filtered != lines:
        with open(claude_md, 'w') as f:
            f.writelines(filtered)
        print('已清理 CLAUDE.md')
"
```

### Step 3: 安装 v0.4 (Claude Code Plugin)

```bash
# 克隆仓库
cd /tmp && git clone https://github.com/moyu12-ae/ZeroSearch.git zerosearch-v4
cd zerosearch-v4

# 安装依赖
bash setup.sh

# 安装为 Claude Code Plugin
mkdir -p ~/.claude/plugins/
cp -r . ~/.claude/plugins/zerosearch/

echo "v0.4 安装完成。重新启动 Claude Code 即可使用 /zerosearch:zerosearch"
```

### Step 4: 验证安装

```bash
# 在 Claude Code 中运行
/plugin list                    # 确认 zerosearch 插件已加载
/zerosearch:zerosearch-config   # 配置为默认搜索工具
/zerosearch:zerosearch 测试搜索   # 测试搜索功能
```

> **提示**: 旧版 v0.3 Profile 和缓存会自动迁移，无需手动处理。

---

## 特性

- **香农信息论驱动** — I(x) = -log₂P(x)，高信息量关键词替代通用词，搜索精准度显著提升
- **贝叶斯收敛迭代** — 信息不足时自动追加搜索（最多 3 轮），收敛即停，无需手动追问
- **Chrome Daemon** — 首次冷启动 ~5s，后续热搜索 <1s，Chrome 保持常驻
- **孤儿 Chrome 恢复** — 冷启动前主动扫端口，发现孤儿 Chrome 直接热连接，根治幽灵连接
- **反检测增强** — CDP 协议级反检测 + StealthUtils 随机延迟注入搜索流水线
- **排他配置** — 用户级/项目级互斥，一键切换自动清除旧注册
- **Plugin 模块化** — 4 个命令 + 2 个技能独立文件，AI 按需读取不浪费 Token

---

## v0.4 更新

| 维度 | v0.3 | v0.4 |
|------|------|------|
| **架构** | 单 SKILL.md | Claude Code Plugin（4 commands + 2 skills + hooks） |
| **搜索策略** | 原样转发查询 | 香农信息论 + 自动收敛迭代 |
| **幽灵连接** | 被动检测 → 冷启动重试 | 主动扫端口 → 孤儿 Chrome 恢复 |
| **反检测** | StealthUtils 未集成 | 搜索流水线随机延迟注入 |
| **配置** | 手动 grep | 排他性一键互斥 |
| **测试** | 45 tests | 67 tests（含 TDD 验证） |
| **审计** | — | 4 轮 challenge，67 问题闭环 |

---

## 使用方式

| 命令 | 说明 |
|------|------|
| `/zerosearch:zerosearch <query>` | 香农策略优化 → 自动迭代 → 综合回答 + 引用 |
| `/zerosearch:zerosearch-config` | 排他性配置默认搜索工具 |
| `/zerosearch:zerosearch-start` | 手动启动 Chrome Daemon |
| `/zerosearch:zerosearch-stop` | 手动停止 Chrome Daemon |

直接说 "搜索 xxx" 或 "查一下 xxx" 即可触发，无需前缀。

### CLI 模式

```bash
python src/search/run.py --query "React 19 Server Components"  # 搜索
python src/search/run.py --query "..." --save --debug           # 搜索 + 保存 + 日志
python src/search/run.py --start                                # 启动 Daemon
python src/search/run.py --stop                                 # 停止 Daemon
```

---

## 技术架构

```
/zerosearch:zerosearch → Shannon Strategy → Search Execution → Chrome Daemon → Google AI Mode
```

| 系统 | 职责 |
|------|------|
| **S0: Plugin Framework** | plugin.json + 4 命令 + hooks |
| **S1: Shannon Strategy** | 香农信息论搜索策略（纯 Markdown Skill） |
| **S2: Search Execution** | 搜索编排 + LRU 缓存 + 反检测延迟 + 错误降级 |
| **S3: Engine Runtime** | Chrome Daemon + 内容提取 + Markdown 转换 |

### 项目结构

```
zerosearch/
├── .claude-plugin/plugin.json    # Plugin 声明
├── commands/                     # 4 个命令 (AI 按需读取)
├── skills/                       # 2 个 Skill (shannon-strategy / search-execution)
├── hooks/hooks.json              # Hook 配置
├── scripts/                      # 配置脚本 + Daemon 检测
├── src/                          # Python 引擎
│   ├── browser/                  # Chrome Daemon + 反检测 + 孤儿恢复
│   ├── search/                   # 搜索编排 + LRU 缓存 + StealthUtils 集成
│   ├── extractor/                # AI 内容提取 + 引用 + 去噪
│   └── converter/                # HTML→Markdown + 脚注格式化
├── tests/                        # pytest (67 tests)
├── docs/                         # 香农策略原文
└── .anws/v4/                     # 架构文档 (4 轮审计)
```

---

## 故障排查

| 问题 | 解决方案 |
|------|---------|
| Patchright 未找到 | `bash setup.sh` |
| Chrome 未安装 | `source .venv/bin/activate && python -m patchright install chrome` |
| Chrome Profile 锁定 | 关闭其他 Chrome 窗口；或 `/zerosearch:zerosearch-config` 切换 |
| AI Mode 不可用 | VPN 到美国/英国；或回退到 WebFetch |
| Profile 损坏 | `rm -rf ~/.cache/zerosearch/chrome_profile/` |
| 每次搜索都 CAPTCHA | 在 Chrome 窗口登录 Google 一次，Profile 记住后几乎零触发 |
| Plugin 命令无响应 | 检查 `.claude-plugin/plugin.json`；运行 `/reload-plugins` |

**退出码**: 0 成功 | 1 通用错误 | 2 CAPTCHA | 3 浏览器关闭 | 4 AI不可用 | 5 Profile锁定 | 130 用户中断

---

## 测试

```bash
python -m pytest tests/ -v          # 67 tests
```

---

## 许可证

MIT License — 见 [LICENSE](LICENSE)

## 致谢

- 灵感来源: [google-ai-mode-skill](https://github.com/PleasePrompto/google-ai-mode-skill)
- 浏览器引擎: [Patchright](https://github.com/Kaliiiiiiiiii-Vinyzu/patchright)
- 架构管理: [Anws](https://github.com/anthropics/anws)
