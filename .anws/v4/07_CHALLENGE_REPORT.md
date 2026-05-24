# ZeroSearch v0.4 质疑报告 (Challenge Report)

> **审查日期**: 2026-05-24
> **审查范围**: `.anws/v4/` 全部设计文档 + 全部源码 + git diff
> **累计轮次**: 5
> **验证手段**: 设计文档 vs 源码逐段对照 + git diff 分析 + 测试运行验证

---

## 📋 问题总览

### 第1轮

| 严重度 | 数量 | 摘要 | 状态 |
|--------|------|------|------|
| C1-C3 | 🔴 | 命名空间冲突、udm=50 无文档、hooks.json 格式错误 | ✅ 已决策/修复 |
| H1-H2 | 🟠 | 架构文档格式错误、scripts/ 层不存在 | ✅ 已修复 |
| M1-M4 | 🟡 | 05_TASKS 缺失、04_SYSTEM_DESIGN 空白、"零修改"矛盾、DOM 脆弱性 | ✅ 已处理/可接受 |
| L1 | 🟢 | Google AI Mode 订阅墙风险 | ⏳ 持续跟踪 |

### 第2轮

| 严重度 | 数量 | 摘要 | 状态 |
|--------|------|------|------|
| C4-C9 | 🔴 | 6 项操作知识遗漏 (Rate Limit/CAPTCHA/Setup/Output/Troubleshoot/首检) | ✅ 已修复 |
| H3 | 🟠 | "How It Works" 叙述碎片化 | ✅ 已修复 |
| M5 | 🟡 | Token 开销 2.6x | ✅ 可接受 |

### 第3轮

| 严重度 | 数量 | 摘要 | 状态 |
|--------|------|------|------|
| C10 | 🔴 | Bash 相对路径引用 → CWD 依赖 | ⏳ 待修复 |
| H4 | 🟠 | README CLI 模式文档不一致 | ⏳ 待修复 |
| M6 | 🟡 | SKILL.md.deprecated YAML frontmatter 遗留 | ⏳ 待清理 |

### 第4轮

| 严重度 | 数量 | 摘要 | 状态 |
|--------|------|------|------|
| C11-C12 | 🔴 | PRD NG3/NG7 严重过时 | ⏳ 本轮修复 |
| H5-H6 | 🟠 | search-execution 引用错文件、Rate Limiting 不在命令 | ⏳ 待修复 |
| M7-M8 | 🟡 | shannon 双重角色、INT-S3 未闭环 | ⏳ 待修复 |
| L2 | 🟢 | 首次检测脱节 | ⏳ 待修复 |

### 第5轮（当前活跃）— 反检测代码 vs 设计文档同步

| 严重度 | 数量 | 摘要 | 状态 |
|--------|------|------|------|
| Critical | 3 | PRD 测试数/NG7/架构子系统清单与代码严重脱节 | ⏳ 待修复 |
| High | 2 | 反检测架构层未记录、任务清单未覆盖反检测/Bug 修复 | ⏳ 待修复 |
| Medium | 2 | CAPTCHA 目标未更新、架构物理结构不完整 | ⏳ 待修复 |

---

## 📊 审查摘要

**审查模式**: `FULL`
**整体判断**: 🟡 需先修复文档与代码脱节问题
**高信号结论**: 
1. **PRD NG7 声称"不修改引擎代码"**，实际 `git diff main -- src/` 显示 4 文件 +656/-33 行已修改。这不是小修小补，是系统性的反检测增强。PRD 必须诚实反映变更。
2. **反检测已提升到 9 类 JS API 覆盖 + 14 Chrome flags + 视口随机化 + CAPTCHA 智能等待**，但架构文档对反检测的描述仅有一行 "BrowserEngine: 反检测"。整个 StealthUtils 体系、init_script 注入、搜索间 jitter 在设计中不可见。
3. **PRD 声称 45 测试**，实际运行 `pytest tests/ -q` 返回 **126 passed**。差距 2.8x，设计文档的完成标准完全过时。

| 指标 | 数值 |
|------|------|
| Critical | 3 |
| High | 2 |
| Medium | 2 |
| Total Findings | 7 |

| 证据来源 | 结论 |
|----------|------|
| design-reviewer | 跳过（直接代码-文档对照） |
| task-reviewer | 跳过（05_TASKS.md 未覆盖本轮变更） |
| Pre-Mortem | 文档-代码脱节是最大的长期风险——新贡献者看 PRD 以为引擎代码未改动，实际大量反检测逻辑不可见 |
| 承诺闭合检查 | Partial — 反检测增强全部实现但文档未承认为承诺 |
| git diff | `4 files changed, 656 insertions(+), 33 deletions(-)` |

---

## 🔍 第5轮核心发现

| ID | 类别 | 严重度 | 契约 | 位置 | 发现 | 影响 | 建议 |
|----|------|--------|------|------|------|------|------|
| CH-32 | 承诺失真 | **Critical** | PRD NG7 | `01_PRD.md §3.2 NG7` + `01_PRD.md §5` | NG7 声称 "不修改 v0.3 底层引擎代码（纯迁移，不动逻辑）"。PRD §5 "v0.3 保留" 表格宣称引擎层全部 "保留（不动逻辑）"。实际代码 4 文件 +656/-33 行变更，涵盖 daemon_runner 反检测配置补全、stealth BROWSER_ARGS 6→14 扩展、engine CAPTCHA 循环重写、StealthUtils 新增 get_init_script() | 新贡献者读 PRD 以为引擎层代码是 v0.3 原封不动的拷贝，导致：(1) 无法理解反检测架构 (2) 合并冲突时代码变更被误认为 "不需要的修改" (3) 评估 v0.4 工作量时严重低估 | 重写 NG7 为 "引擎代码在 v0.3 基础上做定向增强（反检测加固、Bug 修复），核心搜索流程和公共 API 不变"。更新 PRD §5 表格标注已变更的子系统 |
| CH-33 | 承诺失真 | **Critical** | PRD 完成标准 | `01_PRD.md §9` `01_PRD.md §8` | PRD §9 完成标准写 "全部 45 个 v0.3 测试通过"。PRD §8 非功能需求表写 "测试回归: 全部 45 个测试通过"。实际：`pytest tests/ -q` 返回 **126 passed** (97 original + 11 from round 1 anti-detection + 9 from round 2 fingerprint + 5 from bug fixes + 4 from P0 coverage) | 完成标准严重低估测试规模（2.8x 差距），无法作为真实的验收基准 | 更新为 "全部 126 个测试通过（含 v0.3 原有 97 个 + 反检测增强 24 个 + Bug 修复 5 个）" |
| CH-34 | 架构契约 | **Critical** | 02_ARCHITECTURE §2 System 3 | `02_ARCHITECTURE_OVERVIEW.md §2 System 3` | S3 Engine Runtime 子系统清单仅列 daemon.py/engine.py/cache.py/errors.py/extractor.py/converter.py。**完全缺失** stealth.py（反检测配置 + 9 类 init_script 注入）、browser_factory.py（Patchright 工厂 + Daemon 管理）、daemon_runner.py（独立 Chrome 进程）、profile_manager.py（Profile 隔离）、context_manager.py（浏览器状态机）、error_handler.py（CAPTCHA 检测 + 降级） | 架构文档的子系统清单与实际代码严重脱节。新开发者看文档以为 S3 只有 6 个文件，实际至少 12+ 个核心文件 | 扩充 S3 子系统清单，增加 StealthConfig/StealthUtils 体系、反检测 JS 注入层、Daemon 子系统完整文件列表 |
| CH-35 | 架构契约 | **High** | 02_ARCHITECTURE §2 System 3 + §8 物理结构 | `02_ARCHITECTURE_OVERVIEW.md §2` S3 描述 "BrowserEngine: 反检测"（仅 4 字）`02_ARCHITECTURE_OVERVIEW.md §8` 物理结构 | 反检测是整个 ZeroSearch 最精细的技术层（14 Chrome flags + 4 StealthConfig 参数 + 9 类 JS API 覆盖 + init_script 注入 + CAPTCHA 智能等待 + 视口随机化 + 搜索间 jitter），但在架构文档中被压缩为 "反检测" 两个字。 | 反检测的实现复杂度和设计意图在架构层完全不可见。未来迭代反检测策略时，无法从架构文档理解当前覆盖了哪些检测向量 | 在架构文档中增加 §2.1 反检测层次（独立小节），用表格列出各检测向量、覆盖方式、生效层级 |
| CH-36 | 任务契约 | **High** | 05_TASKS.md | `05_TASKS.md` 整体 | 05_TASKS.md 仅覆盖 Plugin 迁移任务（S1-S3, 18 tasks），**完全不包含**反检测增强和 Bug 修复任务。本轮变更（4 文件 656 行）没有任何任务承接 | 任务清单无法追踪反检测增强的进度和质量。完成标准（INT-S3 发布就绪验证）已过时 | 在 05_TASKS.md 增加 Sprint 4 "反检测加固 + Bug 修复"，列出 6 个子任务 |
| CH-37 | 设计闭合 | **Medium** | PRD §8 非功能需求 | `01_PRD.md §8` | PRD §8 CAPTCHA 率目标 `<10%` (未登录) / `<1%` (已登录) 仍用 v0.3 基线。增强后（14 flags + 9 类 JS 覆盖 + jitter + 视口随机化）CAPTCHA 率显著提升，但目标未更新。 | CAPTCHA 率目标未反映增强后的预期，无法评估反检测投入的 ROI | 更新为增强后的目标（如 <5%/<0.5%），或在注释中说明 "v0.4 增强后预期更低" |
| CH-38 | 设计闭合 | **Medium** | 02_ARCHITECTURE §8 物理结构 | `02_ARCHITECTURE_OVERVIEW.md §8` | 物理结构树中 src/browser/ 仅列 daemon.py 和 daemon_state.py，缺少 stealth.py, browser_factory.py, daemon_runner.py, profile_manager.py, context_manager.py。src/search/ 缺少 error_handler.py | 新开发者无法从文档找到实际代码文件 | 补全物理结构树 |

---

## 🚦 最终判断

- [ ] 🟢 项目可继续，风险可控
- [x] 🟡 项目可继续，但需先解决 P0 文档脱节 (CH-32, CH-33, CH-34)
- [ ] 🔴 项目需要重新评估

**判断依据**: 代码质量良好（126 tests pass, 端到端搜索可用），但设计文档与代码严重脱节。3 个 Critical 问题都集中在文档未反映代码真实状态，修复成本低（纯文档更新），影响高（误导贡献者）。

---

## 📚 附录

### A. 承诺闭合验证（本轮焦点：反检测增强）

| 项目 | 结论 | 证据 |
|------|------|------|
| 反检测 JS API 覆盖 | ✅ 9/9 | init_script 覆盖 plugins/permissions/hwConcurrency/WebGL1+2/chrome.runtime/canvas/AudioContext/deviceMemory/screen |
| Chrome 启动参数 | ✅ 14 flags | 含 disable-features 合并、后台服务抑制、Keychain 绕过 |
| 视口指纹 | ✅ 随机化 | 1024-1920 × 768-1080 每次实例化随机 |
| Daemon 反检测配置 | ✅ 完整 | ignore_default_args + locale + viewport + geolocation + headers |
| CAPTCHA 处理 | ✅ 智能等待 | page.is_closed() 检测 + CAPTCHA 自动重检 + 60s 超时 + 自动重导航 |
| 搜索频率控制 | ✅ jitter | 500-2000ms 随机间隔 |
| 文档同步 | ❌ 严重脱节 | PRD NG7, 测试数, 架构子系统, 物理结构均未同步 |

### B. 代码变更统计 (git diff main)

```
src/browser/daemon_runner.py |   8 +-
src/browser/stealth.py       | 129 ++++++++++-
src/search/engine.py         |  56 ++++-
tests/test_anti_detection.py | 496 +++++++++++++++++++++++++++++++++++++++++--
4 files changed, 656 insertions(+), 33 deletions(-)
```
