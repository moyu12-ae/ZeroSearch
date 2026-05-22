# ZeroSearch v0.4 质疑报告 (Challenge Report)

> **审查日期**: 2026-05-22
> **审查范围**: `.anws/v4/` 全部设计文档 + 全部 Python 源代码审计
> **累计轮次**: 3
> **验证手段**: 设计文档审查 + v0.3/v0.4 逐条对照 + CLI/engine/daemon 源码逐段审计

---

## 问题总览

### 第1轮（当前活跃）

| 严重度 | 数量 | 摘要 | 状态 |
|--------|------|------|------|
| Critical | 3 | Plugin 命令命名空间冲突、udm=50 无官方文档支持、hooks.json 格式错误 | ✅ 已决策 (CH-01:接受; CH-02:不加降级; CH-03:已修复) |
| High | 2 | 架构文档格式错误（S1 header 丢失）、scripts/ 层不存在导致命令不可执行 | ✅ 已修复 |
| Medium | 4 | 05_TASKS 缺失、04_SYSTEM_DESIGN 空白、"零修改"承诺矛盾、ContentExtractor DOM 脆弱性 | ⏳ 待处理 |
| Low | 1 | Google AI Mode 商业可用性风险（订阅墙） | ⏳ 待处理 |

### 第2轮 — v0.3/v0.4 内容覆盖度审查（当前活跃）

| 严重度 | 数量 | 摘要 | 状态 |
|--------|------|------|------|
| Critical | 6 | v0.3 操作知识 6 项遗漏：Rate Limiting、CAPTCHA Handling、Output Format、Troubleshooting、First-Time Setup、自动首次运行检测 | ✅ 已修复 |
| High | 1 | "How It Works" 叙述碎片化 — v0.3 一段话讲清，v0.4 分散在 4 个文件 | ✅ 已修复 |
| Medium | 1 | 总 token 开销增加 2.6x (136→361行)，6 个文件维护面 | ✅ 可接受 |

### 第3轮 — 代码实现审计（当前活跃）

| 严重度 | 数量 | 摘要 | 状态 |
|--------|------|------|------|
| Critical | 1 | Plugin 命令中 Bash 引用使用相对路径 — 依赖 CWD=Plugin 根，实际运行时 CWD 是用户项目目录 | ⏳ 待修复 |
| High | 1 | README CLI 模式文档与 cli.py 实现不一致 — 记录 `--profile`/`--fresh-profile` 等不存在参数 | ⏳ 待修复 |
| Medium | 1 | SKILL.md.deprecated 仍含有效 YAML frontmatter — 误改名可触发冲突 | ⏳ 待清理 |

---

## 审查摘要

**审查模式**: `DESIGN`
**整体判断**: 需要先修复 Critical 和 High 问题
**高信号结论**: 
1. **Plugin 命名空间是最危险的忽视**——如果用户从 `/zerosearch` 变为 `/zerosearch:zerosearch`，v0.3→v0.4 就是重大的 UX 退步
2. **udm=50 是整个系统的命脉依赖**——它不被 Google 官方文档承认，是一个通过社区逆向发现的参数
3. **hooks.json 格式与官方规范不符**——缺少外层 `"hooks"` 包装键

| 指标 | 数值 |
|------|------|
| Critical | 3 |
| High | 2 |
| Medium | 2 |
| Low | 1 |
| Total Findings | 8 |

| 证据来源 | 结论 |
|----------|------|
| design-reviewer | 未独立执行（直接审查设计文档） |
| task-reviewer | 跳过（05_TASKS.md 不存在） |
| Pre-Mortem | 失败原因集中在：命名空间 UX 退化、udm=50 参数失效、命令不可执行 |
| 承诺闭合检查 | Partial — 多项运行承诺无法验证 |
| 官方文档对比 | Claude Code Plugin 官方文档 (code.claude.com/docs/en/plugins) — 发现命名空间问题 |
| Web 资料验证 | Wikipedia Google AI Mode 词条 + Google CAPTCHA 实测 — 确证 udm=50 无官方来源 |

---

## 核心发现清单

| ID | 类别 | 严重度 | 契约/维度 | 位置 | 发现 | 影响 | 建议 |
|----|------|--------|-----------|------|------|------|------|
| CH-01 | 承诺失真 | Critical | 业务契约 | PRD §6 (用户流程)、ADR-003 §方案对比 | Plugin 命令默认被命名空间化 → `/zerosearch` 变成 `/zerosearch:zerosearch`，与 PRD 承诺的用户体验矛盾 | 用户必须输入更长命令，v0.3 UX 承诺（"统一搜索入口"）被击穿 | 方案A: 保留 standalone `.claude/commands/` 模式；方案B: 将 plugin name 设极短 + 显式文档说明 |
| CH-02 | 架构契约 | Critical | 外部依赖 | PRD §7.1、架构 §1.3 | `udm=50` 是未被 Google 官方文档记录的 URL 参数。Wikipedia 词条未提及此参数，Google 搜索结果返回 CAPTCHA 而非文档。社区逆向发现，随时可能失效 | udm=50 失效 = 整个搜索引擎报废，无法导航到 Google AI Mode 页面 | 增加 udm=50 失效的检测 + Fallback 路径（如直接搜索 Google 首页并提取 AI Overviews，或回退到 WebFetch） |
| CH-03 | 运行契约 | Critical | 格式规范 | `hooks/hooks.json` | hooks.json 缺少外层 `"hooks"` 包装键。官方规范格式为 `{"hooks": {"PostToolUse": [...]}}`，当前为 `{"PostToolUse": [...]}` | Hook 无法被 Claude Code 加载和触发 | 修正 hooks.json 格式，增加 `"hooks"` 外层键 |
| CH-04 | 架构契约 | High | 文档完整性 | 02_ARCHITECTURE_OVERVIEW.md:L72 | System 1 (Shannon Strategy Skill) 的 header `### System 1:` 丢失，被 System 0 的物理结构代码块吞没。导致架构文档中 S1 的标题行缺失，阅读时 S1 被错误嵌套在 S0 的物理结构描述中 | 实现者阅读架构文档时困惑 S1 的边界定义 | 修复 markdown 结构，在 S0 物理结构代码块后正确插入 `### System 1:` header |
| CH-05 | 运行契约 | High | 技术实现 | commands/*.md + skills/search-execution/SKILL.md | 所有命令引用 `python scripts/run_search.py`，但 `scripts/` 目录下不存在这些文件。实际 Python 引擎在 `src/` 中。命令执行时将直接报 `FileNotFoundError` | 所有搜索命令无法运行 | 方案A: 创建 scripts/ 下薄包装脚本调用 src/；方案B: 命令直接引用 src/search/run.py |
| CH-06 | 承诺失真 | Medium | 任务契约 | 整个 `.anws/v4/` | `05_TASKS.md` 不存在。PRD 的 7 个 User Story (REQ-020 至 REQ-027) 无任何实现任务承接。无法验证设计承诺是否会被代码实现覆盖 | 关键设计决策可能遗漏实现；架构意图与代码之间存在断层 | 执行 `/blueprint` 生成 05_TASKS.md |
| CH-07 | 架构契约 | Medium | 设计完整性 | `.anws/v4/04_SYSTEM_DESIGN/` (空目录) | 4 个系统（Plugin Framework、Shannon Strategy、Search Execution、Engine Runtime）均无详细设计文档。接口定义、数据流、状态机、错误路径全部缺失。ADR-003/004/005 的决策无法被系统设计引用 | 实现阶段缺乏技术细节指导，可能导致实现偏离架构意图 | 执行 `/design-system` 为每个系统创建详细设计 |
| CH-08 | 外部依赖 | Low | 业务持续性 | PRD §1、§2.2 | Google AI Mode 于 2025 年 3 月推出，最初仅限 Google One AI Premium 订阅用户（美国）。AI Overviews 是更广泛可用的公开版本（2024 年 5 月起在 100+ 国家/地区可用）。udm=50 对应的究竟是 AI Mode（付费）还是 AI Overviews（免费），文档未说明 | 如果 udm=50 需要 Google One 订阅，ZeroSearch 对未订阅用户不可用 | 在文档中明确 udm=50 实际触发的是 AI Overviews 还是 AI Mode，并验证在非美国地区的可用性 |
| CH-09 | 承诺失真 | Medium | 架构契约 (Pre-Mortem #4) | PRD §4.4 US-027 验收标准 | "零逻辑修改" 与 "import 路径更新" 构成**逻辑矛盾**。迁移到 Plugin 目录后，`sys.path` 根目录变化，`cli.py` 中 `parent.parent` 的硬编码回溯深度可能在 Plugin 安装后失效。`run.py` 通过 `setup.sh` 存在性定位项目根的逻辑更脆弱——Plugin 安装后 `setup.sh` 不在同一层级 | import 路径变更本身可能引入 bug；45 个测试在迁移后是否全部通过取决于路径修复的完整性 | US-027 应明确承认 "import 路径变更属于修改"，将验收标准从 "零修改" 调整为 "逻辑不变、import 路径有限变更、45 个测试全部通过" |
| CH-10 | 外部依赖 | Medium | 运行契约 (Pre-Mortem #7) | 02_ARCHITECTURE_OVERVIEW.md §3 ContentExtractor、01_PRD.md §5 | ContentExtractor 的 90+ 去噪模式 + 17 选择器是 v0.3 对 Google AI Mode DOM 结构的**快照适配**。Google 的 DOM 结构无 API 稳定性保证。一次不兼容的 DOM 更新 → 搜索输出全部失效 | v0.4 声称 ContentExtractor "完整复用" 但从未讨论其最大风险：Google 页面结构是第三方非公开实现细节 | 在 search-execution Skill 中增加 DOM 结构变化检测 + 降级输出（原始 HTML fallback）；或增加 CI 定期冒烟测试验证提取器有效性 |

---

## 第2轮详细审查: v0.3/v0.4 内容覆盖度对照

> **审查方法**: 将 v0.3 SKILL.md（136行）的每段内容逐一映射到 v0.4 的 6 个文件，标记覆盖/缺失/碎片化。

### v0.3 → v0.4 逐条对照表

| # | v0.3 内容 (行号) | v0.4 映射 | 状态 | 说明 |
|:--:|-------------------|----------|:----:|------|
| 1 | Frontmatter + trigger words (L1-4) | `commands/zerosearch.md` L1-4 | ✅ | 触发词移到 Skill description |
| 2 | How It Works (L37-47) | 分散在 4 个文件 | ⚠️ 碎片化 | 见 CH-11 |
| 3 | First Run: Default Search (L10-34) | `commands/zerosearch-config.md` | ⚠️ 退化 | 见 CH-16 |
| 4 | Usage / Search CLI (L53-57) | `commands/zerosearch.md` Step 3 | ✅ | |
| 5 | Daemon Management (L60-67) | `zerosearch-start.md`, `zerosearch-stop.md` | ✅ | |
| 6 | **Rate Limiting** (L70-72) | — | ❌ | 见 CH-12 |
| 7 | Query Optimization (L73-82) | `skills/shannon-strategy/SKILL.md` | ✅ 增强 | |
| 8 | **First-Time Setup** (L85-93) | — | ❌ | 见 CH-13 |
| 9 | **CAPTCHA Handling** (L95-99) | — | ❌ | 见 CH-14 |
| 10 | **Output Format** (L101-113) | — | ❌ | 见 CH-15 |
| 11 | Exit Codes (L115-125) | `skills/search-execution/SKILL.md` L39-49 | ✅ | |
| 12 | **Troubleshooting** (L127-135) | — | ❌ | 见 CH-17 |

### 第2轮核心发现

| ID | 类别 | 严重度 | v0.3 来源 | 发现 | 影响 | 建议 |
|----|------|--------|----------|------|------|------|
| CH-12 | 内容遗漏 | Critical | SKILL.md L70-72 | **Rate Limiting 完全缺失**。v0.3 明确警告"Space successive searches at least 3 seconds apart"并解释 LRU 缓存 (50条/5min) 自动去重。v0.4 的任何文件中找不到此内容 | AI 快速连续搜索 → Google 触发更严格的 rate limit → CAPTCHA → 搜索全部失败 | 在 `skills/search-execution/SKILL.md` 执行流程前增加 Rate Limiting 节 |
| CH-13 | 内容遗漏 | Critical | SKILL.md L85-93 | **First-Time Setup 完全缺失**。v0.3 有 git clone + bash setup.sh + 系统要求。v0.4 的 6 个文件均不含安装指南 | 新用户拿到 Plugin 不知道如何安装依赖（Python venv, pip install, Chrome） | 在 Plugin 根目录增加 `README.md` 或在 `hooks/post-install.md` 中增加安装引导 |
| CH-14 | 内容遗漏 | Critical | SKILL.md L95-99 | **CAPTCHA Handling 完全缺失**。v0.3 详细说明"browser window stays open — solve CAPTCHA, press Ctrl+C to continue"。这是使用 ZeroSearch 最重要的操作知识 | 用户触发 CAPTCHA 后完全不知道如何操作 → 认为插件坏了 → 放弃使用 | 在 `skills/search-execution/SKILL.md` 错误处理表中为退出码 2 增加详细操作指引 |
| CH-15 | 内容遗漏 | Critical | SKILL.md L101-113 | **Output Format 完全缺失**。v0.3 有完整的 Markdown 输出示例（AI 回答 + Sources 脚注）。v0.4 没有任何输出格式说明 | Claude 不知道结果应该长什么样，输出格式不一致 | 在 `skills/search-execution/SKILL.md` 返回结果节增加输出格式示例 |
| CH-16 | 内容退化 | Critical | SKILL.md L10-34 | **自动首次运行检测退化**。v0.3 通过 `grep -rq "ZeroSearch"` 自动检测首次运行并触发 AskUserQuestion。v0.4 改为手动 `/zerosearch:zerosearch-config`，但没有任何机制自动检测首次运行 | 新用户不知道需要先运行 config，直接搜索 → 可能失败或体验差 | 在 `commands/zerosearch.md` 增加首次运行检测逻辑，如果 `~/.cache/zerosearch/config.json` 不存在则先引导 config |
| CH-17 | 内容遗漏 | Critical | SKILL.md L127-135 | **Troubleshooting 完全缺失**。v0.3 有 5 行问题/解决方案表（Patchright not found, Chrome not installed, AI Mode unavailable, Profile corrupted, CAPTCHA every search）。v0.4 无任何 troubleshooting | 用户遇到问题只能放弃，无法自助修复 | 增加 `skills/troubleshooting/SKILL.md` 或在 README.md 中补充 |
| CH-11 | 叙述完整度 | High | SKILL.md L37-47 | **"How It Works" 叙述碎片化**。v0.3 一段话讲清 Chrome Daemon 概念（"First search ~5s, later <1s"）。v0.4 中此信息分散在：`commands/zerosearch.md` Step 3（一句话提及）、`skills/search-execution/SKILL.md` Step 2（状态检测）、`zerosearch-start.md`（启动说明）。无一处完整讲清整体概念 | 新用户/新 AI 会话难以建立 Daemon 心智模型，可能困惑"为什么有个 Chrome 窗口" | 在 `commands/zerosearch.md` 开头增加 3-4 行的 "How It Works" 速览 |
| CH-18 | 模块化效率 | Medium | 整体 | **Token 开销增加 2.6x**。v0.3 单文件 136 行, v0.4 合计 361 行。但 AI 每次搜索只加载 ~110 行（zerosearch.md 60 + strategy 150+ 部分），净收益为正 | 维护面从 1 个文件变 6 个，但每次只读 2 个 | 可接受。合并非关键内容（troubleshooting 放 README 而非 Skill）以减少 AI 加载量 |

---

## 第3轮详细审查: 代码实现审计

> **审查方法**: 逐段审计 `cli.py`、`run.py`、`engine.py`、`daemon_runner.py`、所有 `commands/*.md`、`skills/*/SKILL.md`，对照 PRD + ADR 契约逐条验证。

### 审查范围

| 文件 | 审计内容 |
|------|---------|
| `src/search/cli.py` | CLI 参数解析、退出码路由、import 路径 |
| `src/search/run.py` | venv 包装、项目根定位 |
| `src/search/engine.py` | 搜索编排、Daemon 双路径、LRU 缓存、错误降级 |
| `src/browser/daemon_runner.py` | Daemon 子进程、状态文件写入 |
| `commands/*.md` | Bash 引用路径正确性 |
| `skills/search-execution/SKILL.md` | Bash 调用引用路径 |

### 第3轮核心发现

| ID | 类别 | 严重度 | 契约 | 位置 | 发现 | 影响 | 建议 |
|----|------|--------|------|------|------|------|------|
| CH-19 | 运行契约 | Critical | 运行承诺 | `commands/zerosearch.md:52`, `commands/zerosearch-start.md:23`, `commands/zerosearch-stop.md:27`, `skills/search-execution/SKILL.md:35` | **所有命令和 Skill 中的 Bash 引用使用相对路径 `python src/search/run.py`**。当 Claude Code 通过 Plugin 执行 `/zerosearch:zerosearch <query>` 时，Claude 从用户项目 CWD 执行 Bash，而 `src/search/run.py` 在 Plugin 目录下。除非 CWD 恰好等于 Plugin 根目录，否则报 `FileNotFoundError` | Plugin 安装后命令无法运行 — 用户输入 `/zerosearch:zerosearch test` 后 Python 找不到脚本 | 所有 Bash 引用改用 `${CLAUDE_PLUGIN_ROOT}/src/search/run.py`，或使用 `cd ${CLAUDE_PLUGIN_ROOT} && python src/search/run.py ...` |
| CH-20 | 文档契约 | High | 文档契约 | `README.md:74-81` CLI 模式 | README 的 "CLI 模式" 章节仍记录 v0.3 参数 `--profile <path>`、`--fresh-profile`。当前 `cli.py` 的 `build_parser()` 仅支持 `--query/--start/--stop --save --debug`，不支持 `--profile`/`--fresh-profile`。用户按 README 执行 `python src/search/run.py --query "test" --profile <path>` 会得到 `unrecognized arguments: --profile` 错误 | 用户按文档操作失败，对项目可信度造成损害；PRD 已将 profile 管理移至 `/zerosearch:zerosearch-config`，但 README 未同步 | 删除 README CLI 模式中 `--profile`/`--fresh-profile` 的示例，替换为实际支持的参数；增加说明 profile 管理通过 `/zerosearch:zerosearch-config` 进行 |
| CH-21 | 遗留风险 | Medium | 无特定契约 | `SKILL.md.deprecated:1-4` | 废弃文件仍保留完整 YAML frontmatter (`name: zerosearch`, `description: Use this skill...`)。如果文件被意外改名回 `SKILL.md`（例如 git 操作误恢复），会与 Plugin 的命名空间 `/zerosearch:xxx` 产生冲突，导致双入口并存 | 低概率但高影响 — 如果发生，Claude Code 会同时加载 Plugin 和独立 Skill，产生不可预测行为 | 删除 `SKILL.md.deprecated` 的 YAML frontmatter，仅保留正文作为历史参考；或直接删除该文件（内容已完整迁移到 commands + skills 中） |

### 架构合规性检查

| 检查项 | 状态 | 证据 |
|--------|:--:|------|
| `cli.py` import 路径机制 (`_setup_import_path`) | ✅ | `parent.parent` 正确解析 Plugin 根目录；lazy import 在 path setup 后执行 |
| `daemon_runner.py` import 路径 | ✅ | 自行执行 `sys.path.insert(0, parent.parent.parent)` |
| `engine.py` 相对导入 | ✅ | `from ..browser.browser_factory` — 正确使用包内相对导入 |
| `run.py` 项目根定位 (`parents[2]` + `setup.sh` 验证) | ✅ | fallback 到 `Path.cwd()` 健壮 |
| 6 级退出码完整 | ✅ | `cli.py` 定义 0/1/2/3/4/5/130 + `_extract_exit_code()` 关键字匹配 |
| LRU 缓存 (50条/5min) | ✅ | `engine.py` CACHE_SIZE=50, CACHE_TTL=300 |
| Daemon 冷启动/热连接双路径 | ✅ | `engine.py._resolve_browser()` 完整实现状态检测分支 |
| 幽灵连接恢复 (CDP 断连自动重试) | ✅ | `engine.py.search()` 捕获 CDPDisconnectError → cleanup → 冷启动重试 |
| 反检测 flag (`BROWSER_ARGS`) | ✅ | `daemon_runner.py` 正确引用 `stealth.py` |
| CAPTCHA 等待逻辑 | ⚠️ | `engine.py:210` `time.sleep(600)` — 10 分钟硬等待，无超时反馈 |
| **Bash 路径引用** | ❌ | 见 CH-19 |
| **README CLI 同步** | ❌ | 见 CH-20 |

### 未发现问题的部分

以下审计点经过逐行检查，确认无暗病：

- **Import 链闭环**: `cli.py` → `engine.py` → `browser_factory.py` + `extractor.py` + `converter.py` + `cache.py` + `error_handler.py` — 所有 import 链可通过 `python3 -m pytest tests/ -q` 的 45 passed 验证
- **Daemon 状态文件原子性**: `daemon_state.py` 使用 `os.replace()` 原子写入
- **退出码向后兼容**: 退出码表 0/1/2/3/4/5/130 与 v0.3 SKILL.md 完全一致
- **CDP 错误检测**: `_is_cdp_error()` 覆盖 9 种断连关键字
- **atexit 资源释放**: `engine.py:44` 注册 `shutdown()` 确保异常退出时释放资源

---

## 关联契约验证

### 业务契约 (PRD) 验证

| 承诺 | 状态 | 证据 |
|------|:--:|------|
| "统一搜索入口 `/zerosearch`" (PRD §6) | ⚠️ 失真风险 | CH-01: Plugin 命名空间可能使入口变为 `/zerosearch:zerosearch` |
| "AI 只读取当前命令相关文件" (PRD §4.1 REQ-020) | ⚠️ 未验证 | CH-06: 无任务验证此承诺 |
| "v0.3 底层引擎完整复用，零回归" (PRD §3.1 G4) | ⚠️ 未验证 | CH-07: 无系统设计文档定义迁移接口 |
| "搜索性能与 v0.3 持平" (PRD §8) | ⚠️ 未验证 | CH-05: 命令不可执行，性能无法测量 |

### 架构契约 (Architecture + ADR) 验证

| 承诺 | 状态 | 证据 |
|------|:--:|------|
| "Plugin 架构标准合规" (ADR-003) | ✅ 通过 | 官方文档验证 `.claude-plugin/plugin.json` + `skills/` + `commands/` + `hooks/` 结构正确 |
| "香农策略独立于引擎" (ADR-004) | ✅ 通过 | S1 纯 Markdown，S3 Python — 依赖方向单向且正确 |
| "不依赖自动多轮" (ADR-005) | ✅ 通过 | 无多轮编排逻辑，一次搜索一次结果 |

### 运行契约验证

| 承诺 | 状态 | 证据 |
|------|:--:|------|
| "命令可执行" | ❌ 失败 | CH-05: 引用的脚本文件不存在 |
| "Hook 可触发" | ❌ 失败 | CH-03: hooks.json 格式不符合官方规范 |
| "冷启动 ≤5s / 热搜索 <1s" | ⚠️ 未验证 | 引擎未就位，引用的脚本不存在 |

---

## Pre-Mortem 失败分析

> 场景：6 个月后，ZeroSearch v0.4 项目失败。以下是推演的失败原因。

| 失败原因 | 失真契约 | Root Cause | 证据 | 概率 |
|---------|---------|-----------|------|:----:|
| 用户抵制命名空间化命令 | 业务契约 (统一搜索入口) | Plugin 命名空间机制使 `/zerosearch` 变为 `/zerosearch:zerosearch`，用户体验退步 | 官方文档明确 Plugin 技能/命令需 namespace 前缀 | 高 |
| udm=50 被 Google 移除或重定向 | 架构契约 (外部依赖) | 依赖未被官方文档记录的 URL 参数，社区逆向发现的参数无 SLA 保障 | Wikipedia 词条无 udm=50 提及；Google 搜索返回 CAPTCHA 无文档 | 中 |
| 命令无法执行导致无人使用 | 运行契约 (命令可执行) | scripts/ 目录为空，命令引用不存在的 Python 文件，部署后立即报错 | CH-05 直接验证：scripts/ 空目录，命令引用 `python scripts/run_search.py` | 高 |
| hooks.json 格式错误导致 Hook 静默失败 | 运行契约 (Hook 可触发) | 缺少外层 "hooks" 键，与官方规范不符 | 官方迁移文档明确格式为 `{"hooks": {"PostToolUse": [...]}}` | 中 |
| AI Mode 需要 Google One 订阅 | 外部依赖 (业务持续性) | Google AI Mode 在 2025 年 3 月发布时仅限付费订阅用户 | Wikipedia: "initially available only to Google One AI Premium subscribers" | 低 |

---

## 建议行动清单

### P0 — 立即处理 (阻塞 /blueprint)

1. **[CH-01]** — **Plugin 命名空间冲突**
   - **方案A (推荐)**: 保留 standalone 配置模式（`.claude/commands/` + `.claude/skills/`），不打包为 Plugin。ZeroSearch 的 UX 承诺（`/zerosearch` 直接触发）与 Plugin 命名空间机制根本冲突
   - **方案B**: 将 plugin name 设为 `z`（极短），命令变为 `/z:zerosearch`。但仍有前缀，不符合 PRD 承诺
   - **方案C**: 推翻 Plugin 化决策，回归 standalone SKILL.md 模式。但保留 `skills/shannon-strategy/` 和 `skills/search-execution/` 作为独立 Skill 文件由 SKILL.md 引用

2. **[CH-02]** — **udm=50 失效降级路径**
   - 在 search-execution Skill 中增加：udm=50 页面检测失败 → 自动退化为普通 Google 搜索 + 提取 AI Overviews（页面顶部的 AI 摘要）
   - 或在 setup.sh 中增加 udm=50 可用性检测

3. **[CH-03]** — **修正 hooks.json 格式**
   - 将所有事件处理器包装在 `"hooks"` 键内

### P1 — 近期处理 (重要)

4. **[CH-04]** — **修复架构文档 markdown 结构**
   - 在 02_ARCHITECTURE_OVERVIEW.md 中 S0 物理结构代码块后插入丢失的 `### System 1: Shannon Search Strategy Skill` header

5. **[CH-05]** — **解决命令不可执行问题**
   - 创建 `scripts/run_search.py`、`scripts/daemon_start.py`、`scripts/daemon_stop.py` 薄包装脚本，调用 `src/` 下的引擎
   - 或更新所有 command/skill 文件的 Bash 调用引用 `src/search/run.py` 直接路径

### P2 — 持续改进

6. **[CH-06]** — 执行 `/blueprint` 生成 `05_TASKS.md`
7. **[CH-07]** — 执行 `/design-system` 为 4 个系统生成详细设计文档
8. **[CH-08]** — 在 README 中说明 Google AI Mode 的可用性前提（地区、是否需要 Google 账号/订阅）

### 第2轮 P0 — 必须补充的内容遗漏

9. **[CH-12]** — 在 `skills/search-execution/SKILL.md` 增加 **Rate Limiting** 节（3秒间隔 + LRU 去重说明）
10. **[CH-13]** — 增加 **First-Time Setup** 文档（可在 README.md 或独立 setup Skill）
11. **[CH-14]** — 在 `skills/search-execution/SKILL.md` 退出码 2 处增加 **CAPTCHA 操作指引**（"浏览器窗口保持打开 → 手动验证 → Ctrl+C 继续"）
12. **[CH-15]** — 在 `skills/search-execution/SKILL.md` Step 5 增加 **Output Format 示例**
13. **[CH-16]** — 在 `commands/zerosearch.md` 增加 **自动首次运行检测**（检查 config.json，不存在则引导 config）
14. **[CH-17]** — 增加 **Troubleshooting 文档**（放 README.md 以不影响 AI 上下文）
15. **[CH-11]** — 在 `commands/zerosearch.md` 开头增加 **"How It Works" 速览**（3-4 行讲清 Daemon 概念）

---

## 最终判断

- [ ] 绿 项目可继续，风险可控
- [x] 黄 项目可继续，但需先解决 P0 问题 (CH-12~CH-17)
- [ ] 红 项目需要重新评估

**判断依据**: 第1轮 Critical（命名空间、udm=50、hooks）已全部决策/修复。第2轮发现 v0.4 的 Plugin 架构在**模块化分工上是正确的**（4系统、6文件、单向依赖），但**遗漏了 v0.3 SKILL.md 中 6 段关键操作知识**（Rate Limiting / CAPTCHA / Setup / Output / Troubleshooting / 自动首检）。这不是架构问题，是**内容迁移不完整的工程问题**——每个遗漏都有明确的补充位置。修复后 v0.4 可达到"模块化优于 v0.3 + 内容完全覆盖"的目标。

---

## 附录

### A. 承诺闭合与假设验证摘要

| 项目 | 结论 | 证据 | 对应问题 |
|------|------|------|----------|
| 重复态 (命令幂等) | Pass | Daemon idempotency 从 v0.3 继承 | — |
| 失败态 (CAPTCHA/超时/地区) | Partial | 6 级退出码已定义，但 udm=50 失效的 Fallback 未定义 | CH-02 |
| 默认态 (框架默认行为) | Fail | 命令默认不可执行 (scripts/ 空)、Hook 默认不触发 (格式错误) | CH-03, CH-05 |
| 运行态 (可部署、可触发) | Fail | 插件可安装但命令无法运行 | CH-05 |
| 并发态 | N/A | 单用户单 Chrome 实例，无并发需求 | — |
| 观测态 (日志/审计) | Partial | v0.3 继承 `--debug` 日志，但 Hook 观测点缺失 | CH-03 |

### B. ADR 影响追踪

| ADR 文件 | 受影响系统 | 影响说明 |
|---------|-----------|---------|
| ADR-003 Plugin 架构 | CH-01 所有命令入口 | Plugin 命名空间可能推翻本 ADR 的 UX 假设 |
| ADR-004 香农提示词 | — | 无影响（纯策略层，不依赖基础设施） |
| ADR-005 统一搜索模式 | — | 无影响（设计决策正确） |
| ADR-001 技术栈 (v2) | S3 Engine Runtime | udm=50 失效会影响浏览器导航目标 |
| ADR-002 Daemon CDP (v3) | S3 Engine Runtime | 无影响 |

### C. 官方文档验证记录

**来源**: [Claude Code Plugin 官方文档](https://code.claude.com/docs/en/plugins) (2026-05-22 访问)

关键验证点:
- ✅ `.claude-plugin/plugin.json` 位置正确
- ✅ `skills/<name>/SKILL.md` 结构正确
- ✅ `commands/` 目录存在且有效（官方注: "Use `skills/` for new plugins" 但 `commands/` 仍可用）
- ✅ `hooks/hooks.json` 存在
- ❌ Skills/Commands 默认带 Plugin 命名空间前缀 (`/plugin-name:skill-name`)
- ❌ hooks.json 格式需外层 `"hooks"` 键: `{"hooks": {"PostToolUse": [...]}}`
- ⚠️ Plugin 技能不支持 `/zerosearch` 这样的无前缀调用方式

**来源**: [Wikipedia - Google AI Overviews](https://en.wikipedia.org/wiki/Google_Search#AI_Overviews) (2026-05-22 访问)

关键验证点:
- ⚠️ "udm=50" 在 Wikipedia 条文中未提及
- ⚠️ Google AI Mode (2025.03) 最初仅限 Google One AI Premium 订阅用户
- ✅ AI Overviews (2024.05) 在 100+ 国家广泛可用
- ❓ udm=50 实际访问的是 AI Mode 还是 AI Overviews — 文档中未澄清
