# ZeroSearch v0.3 质疑报告 (Challenge Report)

> **审查日期**: 2026-05-21
> **审查范围**: v0.3 全部新增/修改代码 (daemon_state.py, browser_factory.py, engine.py, cli.py, SKILL.md)
> **累计轮次**: R3（代码质量审查）

---

## 📋 问题总览

### R1 ✅ 已归档 | R2 ✅ 已归档

### R3 轮（当前活跃 — 代码暗病审查）

| ID | 严重度 | 摘要 | 状态 |
|----|:------:|------|:--:|
| R3-C1 | 🔴 Critical | connect_to_daemon 失败后孤儿 Chrome 进程泄漏 | ✅ 已修复 |
| R3-M1 | 🟡 Medium | _resolve_browser 误报 "浏览器已关闭" 状态消息 | ✅ 已修复 |
| R3-M2 | 🟡 Medium | launch_daemon 创建无用 context，stealth 参数未生效 | ✅ 已修复 |
| R3-L1 | 🟢 Low | 未使用的 import (contextlib, signal, DaemonState) | ✅ 已修复 |
| R3-L2 | 🟢 Low | connect_to_daemon 异常后 cleanup 对存活 PID 无效 | ✅ 随 R3-C1 修复 |

---

## 📊 审查摘要

**审查模式**: `FULL` (代码审查)
**整体判断**: 🟢 可继续，风险可控
**高信号结论**: 核心问题是 `connect_to_daemon()` 在网络异常等场景失败时，Chrome 进程仍然存活，但代码回退到冷启动却不杀旧进程。孤儿 Chrome 累积消耗内存(每实例~200MB)。其余为消息误导、无用代码和 lint 问题。

| 指标 | 数值 |
|------|:--:|
| Critical | 1 |
| High | 0 |
| Medium | 2 |
| Low | 2 |
| Total Findings | 5 |

---

## 🔍 核心发现清单

| ID | 类别 | 严重度 | 位置 | 发现 | 影响 | 建议 |
|----|------|--------|------|------|------|------|
| R3-C1 | 孤儿进程泄漏 | 🔴 Critical | `engine.py:132` → `browser_factory.py:411` | `connect_to_daemon()` 失败时：Chrome PID 仍存活但代码不回杀旧进程。`cleanup_stale()` 检测到 PID 存活，不作删除。`launch_daemon()` 启动新 Chrome（可能换端口），旧 Chrome 成为孤儿进程。每次重连失败→多一个 200MB Chrome。 | 用户多次搜索后系统出现多个无主 Chrome 窗口，内存泄漏，端口耗尽 | 在 `_resolve_browser()` 中的 connect_to_daemon 异常处理里，先调用 `cleanup_daemon()` 杀掉旧 Chrome，再冷启动 |
| R3-M1 | 状态消息误导 | 🟡 Medium | `engine.py:132-137` | `connect_to_daemon()` 失败后输出三行：①"热连接失败" ②"浏览器已关闭"(错误！Chrome 还活着) ③"冷启动 Chrome"。 | 用户诊断困难——看到"浏览器已关闭"以为 Chrome 自己出问题 | 合并为一条消息："热连接失败，重新启动 Chrome..."；仅在 PID 真死亡时输出"浏览器已关闭" |
| R3-M2 | 无用代码 | 🟡 Medium | `browser_factory.py:337-341` | `launch_daemon()` 末尾创建 `context = browser.contexts[0] if browser.contexts else browser.new_context(**stealth_kwargs)`，但 `context` 变量未使用。`browser.new_page()` 使用 `contexts[0]`（默认 context），stealth 参数注入的 context 在 `contexts[1]` 被忽略。 | stealth 配置(locale/viewport/headers)未生效。实测 Google 仍正常加载（spike 验证无这些配置也能通过），但 PRD 承诺的 stealth 注入未实现 | 删除这段无用代码；或改为先 `new_context(**stealth_kwargs)` 作为 `contexts[0]` |
| R3-L1 | 未使用的 import | 🟢 Low | `browser_factory.py:18` + `daemon_state.py:10` | `from contextlib import contextmanager` 未使用；`import signal` 在 daemon_state.py 未使用；`from .daemon_state import DaemonState` 未使用 | lint 噪音 | 删除 |
| R3-L2 | cleanup 无效调用 | 🟢 Low | `engine.py:137` | `connect_to_daemon()` 异常后代码执行到 `cleanup_stale()`，但此时 Chrome PID 存活→`cleanup_stale()` 发现 PID 存活→不删除文件（正确行为），但成为 NOP。靠下文的 `launch_daemon()` 的 `write_state()` 覆盖旧状态文件。 | 无功能影响，但逻辑不够清晰 | 与 R3-C1 一并修复 |

---

## 承诺闭合验证（代码层面）

| 检查维度 | 结论 | 证据 |
|---------|:--:|------|
| **重复态** | ✅ Pass | `write_state` 原子 rename；`cleanup_daemon` 幂等(PID 不存在→跳过)；`--start` 幂等(已运行→exit 0) |
| **失败态** | ⚠️ Partial | CDP 超时降级正常；但 connect_to_daemon 失败后不杀旧 Chrome→孤儿泄漏 (R3-C1) |
| **默认态** | ✅ Pass | 无 daemon.json→冷启动 |
| **运行态** | ✅ Pass | subprocess start_new_session 分离；SIGTERM→3s→SIGKILL |
| **并发态** | ✅ Pass | atomic write；Chrome 天然隔离标签页 |
| **观测态** | ✅ Pass | stderr 三状态 + --debug 扩展 |
| **幂等性** | ✅ Pass | start/stop/cleanup 全部幂等 |

---

## 建议行动清单

### P0 - 立即修复

1. **[R3-C1]** — `engine.py` `_resolve_browser()` 中，connect_to_daemon 异常分支改为：先 `BrowserFactory.cleanup_daemon()` 杀旧 Chrome，再 `launch_daemon()` 冷启动

### P1 - 近期修复

2. **[R3-M1]** — 合并 _resolve_browser() 的状态消息，消除误导性 "浏览器已关闭"
3. **[R3-M2]** — 删除 `launch_daemon()` 末尾无用的 context 创建代码

### P3 - 持续改进

4. **[R3-L1]** — 清理未使用的 import

---

## 🚦 最终判断

- [ ] 🟢 项目可继续
- [x] 🟢 项目可继续，风险可控

**判断依据**: 1 Critical（孤儿 Chrome 泄漏→每次联结失败多占 ~200MB）。修复代码量 ~5 行。其余为消息误导和无用代码，可在同一 commit 清理。
