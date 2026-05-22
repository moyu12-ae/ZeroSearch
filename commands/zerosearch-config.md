---
name: zerosearch-config
description: 配置 ZeroSearch — 设为默认搜索工具
allowed-tools: Read, Bash, AskUserQuestion
---

# /zerosearch-config — 搜索配置

ZeroSearch 配置入口。Chrome 使用独立 Profile（`~/.cache/zerosearch/chrome_profile/`），与日常 Chrome 隔离，无需额外配置。

## 执行步骤

### Step 1: 默认搜索工具注册

使用 `AskUserQuestion` 询问是否将 ZeroSearch 设为默认搜索工具：

| 选项 | 描述 |
|------|------|
| A | 用户级默认（写入 ~/.claude/CLAUDE.md，所有项目生效） |
| B | 项目级默认（写入当前工作区 CLAUDE.md，仅本项目生效） |
| C | 不设为默认 |

### Step 2: 写入配置

根据用户选择：

- **A 用户级**: 将搜索策略追加到 `~/.claude/CLAUDE.md`
- **B 项目级**: 将搜索策略追加到当前项目 `CLAUDE.md`
- **C 不注册**: 不做任何操作

同时更新 `~/.cache/zerosearch/config.json` 记录本次选择。
