---
name: zerosearch-config
description: 配置 ZeroSearch — Chrome Profile 选择、设为默认搜索工具
allowed-tools: Read, Bash, AskUserQuestion
---

# /zerosearch-config — 搜索配置

ZeroSearch 配置入口。

## 执行步骤

### Step 1: Chrome Profile 选择

使用 `AskUserQuestion` 询问用户选择 Profile 模式：

| 选项 | 描述 |
|------|------|
| A | 使用现有 Chrome Profile（已登录 Google，CAPTCHA 极少） |
| B | 创建独立 Profile（~/.cache/zerosearch/chrome_profile/） |
| C | 保持当前配置不变 |

### Step 2: 默认搜索工具注册

使用 `AskUserQuestion` 询问是否将 ZeroSearch 设为默认搜索工具：

| 选项 | 描述 |
|------|------|
| A | 用户级默认（写入 ~/.claude/CLAUDE.md） |
| B | 项目级默认（写入当前项目 CLAUDE.md） |
| C | 不设为默认 |

### Step 3: 写入配置

根据用户选择，更新 `~/.cache/zerosearch/config.json`。
