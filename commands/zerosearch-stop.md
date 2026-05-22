---
name: zerosearch-stop
description: 手动停止 Chrome Daemon，释放系统资源
allowed-tools: Bash
---

# /zerosearch-stop — 停止 Chrome Daemon

手动关闭 Chrome 常驻进程，释放系统资源。

## 执行步骤

### Step 1: 检测 Daemon 状态

检查 `~/.cache/zerosearch/daemon.json` 是否存在且 PID 存活。

### Step 2: 关闭或跳过

- **Daemon 未运行**: 输出 `[Daemon] Chrome 未在运行`，退出码 0（幂等）
- **Daemon 已运行**: 执行关闭流程：
  1. 向 Chrome PID 发送 SIGTERM
  2. 等待 3s
  3. 若仍未退出，发送 SIGKILL
  4. 清理 `~/.cache/zerosearch/daemon.json`

```bash
python "${CLAUDE_PLUGIN_ROOT}/src/search/run.py" --stop
```

Chrome 窗口关闭，状态文件清理。下次 `/zerosearch` 将自动冷启动。
