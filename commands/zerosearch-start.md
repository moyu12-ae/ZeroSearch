---
name: zerosearch-start
description: 手动启动 Chrome Daemon（不搜索）
allowed-tools: Bash
---

# /zerosearch-start — 启动 Chrome Daemon

手动启动 Chrome 常驻进程，用于预热浏览器。后续搜索将使用热连接（<1s）。

## 执行步骤

### Step 1: 检测 Daemon 状态

检查 `~/.cache/zerosearch/daemon.json` 是否存在且 PID 存活。

### Step 2: 启动或跳过

- **Daemon 已运行**: 输出 `[Daemon] Chrome 已在运行`，退出码 0
- **Daemon 未运行**: 执行冷启动：

```bash
python ${CLAUDE_PLUGIN_ROOT}/src/search/run.py --start
```

Chrome 窗口出现后保持打开。后续 `/zerosearch` 将复用该实例。
