# ADR-002: Chrome Daemon CDP 连接策略 — connect_over_cdp

## 状态

Accepted

## 背景

ZeroSearch v0.2 每次搜索都冷启动 Chrome 浏览器（Patchright `launch()` → 导航 → `browser.close()`），耗时 ~5s。v0.3 引入 Chrome Daemon，需要实现"热搜索"：首次冷启动后 Chrome 保持存活，后续搜索通过 CDP 连接到已有 Chrome 实例，只创建新标签页完成搜索，目标耗时 <1s。

核心技术挑战：如何在不同 Python CLI 调用之间连接同一个 Chrome 实例？

## 决策

选择 **方案 A: connect_over_cdp + subprocess 冷启动**。

**Spike 验证结果 (2026-05-21)**:
- ✅ `subprocess.Popen` 启动 Chrome（带反检测 flags）→ Chrome 完全独立于 Python 进程
- ✅ `navigator.webdriver = False`（`--disable-blink-features=AutomationControlled` 有效）
- ✅ `connect_over_cdp` 跨进程连接成功 → 导航 Google 无 CAPTCHA
- ❌ Patchright `launch()` 无法使 Chrome 脱离进程（os._exit 也不行，driver 必然杀 Chrome）

**修正后的工作流程**:
1. **冷启动**: `subprocess.Popen([chrome, "--remote-debugging-port=<port>", "--disable-blink-features=AutomationControlled", ...])` → 等待 CDP 就绪 → 写入 `daemon.json`
2. **热搜索 (冷启动+热搜索统一)**: 读取 `daemon.json` → 检测 PID 存活 + CDP 响应 → `patchright.chromium.connect_over_cdp("http://127.0.0.1:<port>")` → `browser.new_page()` → 导航 → 提取 → `page.close()` → `browser.close()` (释放连接，不杀 Chrome)
3. **停止**: `/zerosearch-stop` → 向 Chrome PID 发送 SIGTERM → 删除 `daemon.json`

**核心理由**: 0 新依赖，冷启动用 subprocess（标准库），热连接用 Patchright connect_over_cdp（复用 Page API + 反检测上下文）。Chrome flags 提供基础反检测（已验证 `navigator.webdriver=false`），connect_over_cdp 提供 Patchright 的 stealth context 注入。

## 候选方案对比

| 候选 | 总分 | 反检测 | 跨CLI | 实现复杂度 | 性能 | 结论 |
|------|:------:|:--:|:--:|:--:|:--:|------|
| **A: connect_over_cdp** | **233/240** | 首次 launch 已打补丁 | daemon.json | 仅新增 BrowserEngine 双路径 | 连接 <100ms | ✅ 选定 |
| B: Python Daemon 进程 | 165/240 | 同 A | IPC 协议 | 全新 Daemon 模块 + IPC | IPC 增加延迟 | ❌ 过度设计 |
| C: 纯 CDP WebSocket | 125/240 | 需手动维护 | daemon.json | 完全重写 Extractor | 最快但丧失 API | ❌ 维护成本高 |

### 关键维度对比

| 维度 | A (connect_over_cdp) | B (Python Daemon) | C (纯 CDP WS) |
|------|:--:|:--:|:--:|
| Patchright API 复用 | ✅ 完全复用 | ✅ 复用 | ❌ 需手写 CDP 命令 |
| 跨 CLI 调用 | daemon.json | IPC (Unix Socket/gRPC) | daemon.json + WebSocket |
| 反检测保持 | ✅ 首次 launch 补丁持续生效 | ✅ 同 A | ⚠️ 需手动注入 |
| ContentExtractor 兼容 | ✅ Page 对象不变 | ✅ 同 A | ❌ 需重写为 CDP |
| 新依赖 | 0 | IPC 库 (≥1) | websockets 库 |
| 实现改动量 | BrowserEngine + cli.py 参数 | BrowserEngine + 全新 Daemon 模块 + IPC | 几乎全部系统 |

## 权衡点

| 权衡 | 分析 |
|------|------|
| **connect_over_cdp 的反检测** | 反检测补丁在 Chrome 进程启动时通过 CDP 注入（Runtime.enable / Console.enable 补丁）。connect_over_cdp 只建立新连接，不重置已注入的 CDP 域。如发现覆盖情况，可在重连后调用补丁重新注入。 |
| **CDP 端口管理** | 固定端口 9222 简单但可能与本地其他工具冲突。方案：启动时扫描 9222-9232 找空闲端口，将实际端口写入 daemon.json。 |
| **Browser 对象生命周期** | `browser.close()` 必须仅在 `/zerosearch-stop` 或用户关窗时调用。热搜索路径中 `browser` 通过 connect_over_cdp 获取，搜索完成后**不调用** `browser.close()`，仅 `page.close()`。 |
| **跨 CLI 并发** | 两个 CLI 同时搜索时，各自通过 connect_over_cdp 获取独立的 Browser 对象引用，各自创建 Page。Chrome 内核天然隔离标签页，无竞态问题。 |
| **daemon.json 竞态** | 文件级竞态：写 daemon.json（冷启动）与读 daemon.json（热搜索检测）之间可能并发。方案：冷启动时使用临时文件 + 原子 rename；读取时容忍短暂不一致（存活检测已兜底）。 |

## 后果

**正面**:
- 0 新依赖（pip install 不变）
- ContentExtractor / MarkdownConverter 完全不变（仍使用 Playwright Page 对象）
- 实现范围明确：BrowserEngine 新增 ~100 行（daemon_state.py + factory 双路径）+ SearchEngine 编排层 ~20 行适配
- v0.2 冷启动路径完整保留，向后兼容
- 热搜索 <1s（连接 ~100ms + 导航 + 提取）
- 首次 launch 注入的反检测补丁持续生效

**负面**:
- connect_over_cdp 依赖固定的 CDP 端口号（需端口冲突检测）
- Chrome 进程分离意味着 Python 进程无法直接感知 Chrome 崩溃（依赖下次搜索时的存活检测）
- 用户可能忘记停止 Chrome（内存占用 ~200MB 持续存在），但可通过手动 `/zerosearch-stop` 或关窗解决
- CDP 端口固定在同一台机器的 127.0.0.1 上，不支持远程 Daemon [ASSUMPTION: 无需远程 Daemon]

**需要的后续行动**:
- BrowserEngine: 新增 `daemon_state.py`（daemon.json 读写 + PID 存活检测 + CDP 端口响应检测）
- BrowserEngine: `browser_factory.py` 新增 `connect_to_daemon()` 和 `launch_daemon()` 两个方法
- BrowserEngine: `context_manager.py` 状态机扩展 COLD → HOT → DEAD（HOT 为新增状态）
- SearchEngine: `cli.py` 新增 `--start` / `--stop` 参数
- SearchEngine: `engine.py` 编排层新增 Daemon 状态检测分支（`check_daemon()` → 冷启动 或 热连接）

## 影响范围

| 系统 | 影响 |
|------|------|
| **BrowserEngine** | 🔴 重大变更 — 新增 daemon_state.py + 冷启动/热连接双路径 + 状态机扩展 |
| **SearchEngine** | 🟡 微调 — 编排层新增 Daemon 检测分支 + CLI --start/--stop 参数 |
| **SKILL.md** | 🟢 微调 — 新增 /zerosearch-start/stop 触发词 |
| **ContentExtractor** | 🟢 不变 |
| **MarkdownConverter** | 🟢 不变 |
| **setup.sh / requirements.txt** | 🟢 不变 (0 新依赖) |
