---
name: zerosearch-config
description: 配置 ZeroSearch — 设为默认搜索工具（排他性：用户级 OR 项目级，二选一）
allowed-tools: Read, Bash, AskUserQuestion
---

# /zerosearch-config — 搜索配置

ZeroSearch 配置入口。Chrome 使用独立 Profile（`~/.cache/zerosearch/chrome_profile/`），无需额外配置。

**排他性规则**: 用户级和项目级只能保留一个。选择新位置会自动从旧位置清除。

## 执行步骤

### Step 1: 检测并选择

先用脚本检测当前注册状态：

```bash
python "${CLAUDE_PLUGIN_ROOT}/scripts/configure_search.py" --detect
```

根据结果，使用 `AskUserQuestion` 询问用户选择：

| 选项 | 描述 |
|------|------|
| A | 用户级默认（写入 ~/.claude/CLAUDE.md，所有项目生效） |
| B | 项目级默认（写入当前项目 CLAUDE.md，仅本项目生效） |
| C | 不注册（清除所有位置的 ZeroSearch 注册） |

### Step 2: 执行排他性注册

根据用户选择运行脚本：

```bash
python "${CLAUDE_PLUGIN_ROOT}/scripts/configure_search.py" --scope user     # A
python "${CLAUDE_PLUGIN_ROOT}/scripts/configure_search.py" --scope project  # B
python "${CLAUDE_PLUGIN_ROOT}/scripts/configure_search.py" --scope none     # C
```

脚本自动处理：
- 在目标位置写入搜索策略
- 从非目标位置清除旧的 ZeroSearch 注册
- 确保任意时刻只有一个位置有 ZeroSearch 配置

### Step 3: 更新配置

写入 `~/.cache/zerosearch/config.json` 记录本次选择。
