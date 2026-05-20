# ZeroSearch v0.2 质疑报告 (Challenge Report)

> **审查日期**: 2026-05-20
> **审查范围**: 全量设计文档 + 全量源代码 + README + SKILL.md
> **累计轮次**: R4（终审 — 层间一致性审查）

---

## 📋 问题总览

### R1 ✅ 已归档 | R3 ✅ 已修复

### R4 轮（当前活跃 — 层间协调一致）

| ID | 严重度 | 摘要 | 状态 |
|----|:------:|------|:--:|
| R4-C1 | 🔴 Critical | PRD/Architecture/ADR 仍描述已删除的双 Profile 模式 | ⏳ |
| R4-H1 | 🟠 High | README "快速开始" 仍说 AskUserQuestion 选 Profile | ⏳ |
| R4-H2 | 🟠 High | PRD REQ-008 验收标准描述不存在的 AskUserQuestion | ⏳ |
| R4-M1 | 🟡 Medium | CAPTCHA 率目标引用已删除的 Option A/B | ⏳ |
| R4-M2 | 🟡 Medium | 测试计划仍引用 `resolve_profile_path` | ⏳ |

---

## 📊 审查摘要

**审查模式**: `FULL`（设计+代码+文档交叉验证）
**整体判断**: 🟡 需先修复层间不一致
**高信号结论**: 代码是正确的（单 Profile），但 PRD/Architecture/ADR 仍描述已删除的双 Profile 模式（Option A/B）。这是简化后未同步设计文档导致的层间漂移——代码向后兼容，但文档向前说了假话。

| 证据来源 | 结论 |
|----------|------|
| 基线测试 | ✅ 29/29 passed |
| 模块编译 | ✅ 15/15 OK |
| Camoufox 扫描 | ✅ Zero functional refs |
| PRD↔代码 交叉验证 | ❌ Profile 模式不一致 |
| Architecture↔代码 | ❌ System 0/1 描述已过期 |
| README↔SKILL.md | ⚠️ README 描述已删除的 AskUserQuestion |

---

## 🔍 核心发现

### R4-C1 🔴 — PRD/Architecture/ADR 仍描述双 Profile 模式

**位置**: 
- `.anws/v2/01_PRD.md` REQ-008（Option A/B + AskUserQuestion Profile 选择）
- `.anws/v2/02_ARCHITECTURE_OVERVIEW.md` System 0（两个 AskUserQuestion）+ System 1（两个 Profile 路径）
- `.anws/v2/03_ADR/ADR_001_TECH_STACK.md` §"正面"（"复用用户真实 Chrome Profile"）

**证据**: 代码已移除双 Profile 支持（commit `9bbb477`），SKILL.md 已简化为单个 AskUserQuestion。但设计文档仍描述：
- AskUserQuestion Q1: Profile 选择（代码中不存在）
- Option A: 复用真实 Chrome（代码中不存在）
- Option B: 独立空白 Profile（现在这是唯一模式）

**影响**: 新开发者按照 PRD/Architecture 理解系统时，会误以为有 Profile 选择功能，而实际上没有。

**建议**: 更新 PRD REQ-008、Architecture §2.0/§2.1、ADR §"正面"——移除 Option A/B 描述，统一为单 Profile。

---

### R4-H1 🟠 — README "快速开始" 仍说 AskUserQuestion 选 Profile

**位置**: `README.md` 快速开始章节

README 写 "首次运行时会通过 AskUserQuestion 让你选择 Profile 模式：Option A (推荐) 复用真实 Chrome Profile / Option B 独立空白 Profile"。

实际代码只有一个 AskUserQuestion："是否将 ZeroSearch 设为默认搜索工具？"，没有 Profile 选择。

**建议**: 更新快速开始段落，改为描述"默认搜索工具"的 AskUserQuestion。

---

### R4-H2 🟠 — PRD REQ-008 验收标准描述已删除的 AskUserQuestion

**位置**: `PRD REQ-008`

验收标准包含 "SKILL.md 检测到 Profile 配置文件不存在 → Claude 调用 AskUserQuestion"。这个 AskUserQuestion 已被简化掉。现在的 SKILL.md 只调用 AskUserQuestion 询问"默认搜索工具"。

**建议**: REQ-008 应描述当前的单 Profile 逻辑（无需用户选择，统一使用独立 Profile），或将 REQ-008 与 REQ-009 合并为"首次运行初始化"。

---

### R4-M1 🟡 — CAPTCHA 率目标引用已删除的 Option A/B

**位置**: `PRD §5 非功能需求`

仍写 "CAPTCHA 触发率 — Option A (真实 Chrome, 已登录) <1%" / "Option B (独立 Profile, 未登录) <10%"。Option A 已删除。

**建议**: 统一为 "CAPTCHA 触发率（独立 Profile）<10%，登录 Google 后 <1%"。

---

### R4-M2 🟡 — 05_TASKS.md 测试任务仍引用 `resolve_profile_path`

**位置**: `05_TASKS.md` T2.2.1, T3.3.1

任务描述引用 `profile_config.json` 解析和双路径选择，但实际代码已无此逻辑。

**建议**: 标记这些任务为已完成（已简化），或更新描述。

---

## 🚦 最终判断

- [ ] 🟢 项目可继续
- [x] 🟡 可继续，但需先同步设计文档
- [ ] 🔴 需要重新评估

**判断依据**: 1 Critical（设计文档与代码不一致）+ 2 High（README/PRD 细节过期）。代码质量和测试覆盖良好（29 tests, 15 modules, zero Camoufox）。问题是文档层间漂移——代码已演进但设计文档未同步。修复后即可发布。

---

## 📚 附录

### A. 层间一致性验证矩阵

| 文档 → 代码 | 结果 |
|-------------|:--:|
| PRD REQ-001 (冷启动+可见) → engine.py + context_manager | ✅ |
| PRD REQ-002 (CDP反检测) → stealth.py + browser_factory | ✅ |
| PRD REQ-003 (AI原生输出) → dom_cleaner + footnote | ✅ |
| PRD REQ-004 (代理继承) → 代码无proxy配置 | ✅ |
| PRD REQ-005 (pip安装) → setup.sh + requirements.txt | ✅ |
| PRD REQ-008 (Profile选择) → 已删除 | ❌ |
| PRD REQ-009 (CLAUDE注册) → setup.sh | ✅ |
| Architecture §2.0 (SKILL.md System 0) → SKILL.md | ❌ |
| Architecture §2.1 (BrowserEngine双路径) → profile_manager | ❌ |
| ADR "复用真实Chrome Profile" → 已删除 | ❌ |
| README 快速开始 → SKILL.md | ❌ |
| SKILL.md → cli.py flags | ✅ |
| 05_TASKS.md test descriptions → test_browser_factory.py | ⚠️ |

### B. 基线证据

| 检查 | 结果 |
|------|:--:|
| pytest (29 tests) | ✅ |
| Import chain (15 modules) | ✅ |
| Camoufox functional refs | ✅ 0 |
| `--no-sandbox` in args | ✅ removed |
| Proxy code in browser engine | ✅ 0 |
| SKILL↔CLI flag parity | ✅ |
