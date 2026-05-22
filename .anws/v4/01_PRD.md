# ZeroSearch v0.4 — 产品需求文档 (PRD)

**功能名称**: Plugin 化 + 香农提示词工程
**文档状态**: 草稿 (Draft)
**创建日期**: 2026-05-22
**关联概念模型**: `.anws/v4/concept_model.json`

---

## 1. 执行摘要 (Executive Summary)

将 ZeroSearch 从单 SKILL.md 升级为 **Claude Code Plugin**，引入基于**香农信息论**的提示词工程——用高信息量关键词明确表达搜索意图，让 Google AI Mode 的语义理解能力充分发挥。底层引擎（BrowserEngine/ContentExtractor/MarkdownConverter）全部复用 v0.3。

核心公式：**I(x) = -log₂P(x)** — 关键词出现概率越低，信息量越高，搜索越精准。

---

## 2. 背景与上下文 (Background & Context)

### 2.1 问题陈述 (Problem Statement)

**问题 1：架构瓶颈** — v0.3 是单 SKILL.md 文件，所有逻辑混在一起。AI 每次读取整个文件，无法按需加载。新增功能只能在同一个文件末尾追加，维护成本线性增长。

**问题 2：搜索质量天花板** — v0.3 的搜索本质是"将用户原话传给 Google"，即上一代关键词匹配思维。Google AI Mode（udm=50）本身具备语义理解能力，但我们没有充分利用。用户输入"怎么优化 React 性能"时就原样搜索，而不是提取高信息量关键词如"React 19 Server Components streaming SSR"。

**问题 3：缺乏搜索方法论** — v0.3 没有指导 Claude 如何设计搜索查询，全靠 Claude 自己猜测。需要一个系统化的搜索思维框架。

### 2.2 核心机会 (Opportunity)

- **Plugin 架构**：模块化后每个命令/技能独立文件，AI 按需读取，维护成本大幅降低
- **香农信息论指导**：将快速搜索策略.md 的理念编码为可执行的搜索技能，让每次搜索都"经过思考"
- **零新依赖**：底层引擎全部复用 v0.3，变更仅限插件层和搜索策略层
- **统一模式**：不做 Quick/Deep 分离，不做多阶段流水线，保持简单

---

## 3. 目标与范围 (Goals & Non-Goals)

### 3.1 目标 (Goals)

- **[G1]**: 从单 SKILL.md 升级为 Claude Code Plugin（plugin.json + 模块化 commands/skills/hooks），AI 按需读取文件
- **[G2]**: 引入香农提示词工程 Skill，指导 Claude 将用户查询转化为高信息量搜索提示词
- **[G3]**: 统一搜索入口 `/zerosearch`，一次搜索完成，不分离 Quick/Deep 模式
- **[G4]**: v0.3 底层引擎（BrowserEngine/ContentExtractor/MarkdownConverter）完整复用，零回归
- **[G5]**: 配置命令 `/zerosearch-config` 负责默认搜索工具注册。Chrome Profile 固定使用独立 Profile（`~/.cache/zerosearch/chrome_profile/`），无需用户选择

### 3.2 非目标 (Non-Goals)

- **[NG1]**: 不做 Quick Search / Deep Search 模式分离
- **[NG2]**: 不做两阶段搜索流水线（先搜索→再阅读）
- **[NG3]**: 不做自动多轮迭代搜索（贝叶斯更新由用户手动触发，AI 可建议但不自动执行）
- **[NG4]**: 不做 WebFetch / PDF 自动下载阅读
- **[NG5]**: 不做 Deep Research（多轮自动深度研究）
- **[NG6]**: 不做 Citation Crawler 引用爬取
- **[NG7]**: 不修改 v0.3 底层引擎代码（纯迁移，不动逻辑）

---

## 4. 用户故事与需求清单 (User Stories)

### 4.1 架构层 — Plugin 化

#### US-020: Plugin 脚手架替换 SKILL.md [REQ-020] (优先级: P0)

- **故事描述**: 作为一个开发者，我想要 ZeroSearch 从单 SKILL.md 升级为标准 Claude Code Plugin 结构，以便各模块独立维护，AI 按需读取。
- **用户价值**: 模块化 = 低耦合 = 易维护 + AI 不会读到多余文件
- **独立可测性**: 执行 `anws plugin validate` 验证 plugin.json 结构合法性
- **涉及系统**: Plugin 框架
- **验收标准**:
    - [ ] **Given** v0.3 只有 SKILL.md，**When** 升级到 v0.4，**Then** 产出标准 Plugin 目录结构（plugin.json + commands/ + skills/ + hooks/ + src/）
    - [ ] **Given** Plugin 已安装，**When** 用户输入搜索请求，**Then** AI 只读取 `/zerosearch` 命令文件和香农策略 Skill，不读取配置文件等其他模块

---

#### US-021: 模块化命令分离 [REQ-021] (优先级: P0)

- **故事描述**: 作为一个 AI Agent，我想要每个命令有独立的定义文件，以便我只读取需要的命令而不会被其他命令的指令污染上下文。
- **用户价值**: 精确的上下文控制，AI 不浪费 token 在无关指令上
- **独立可测性**: 分别触发 `/zerosearch` 和 `/zerosearch-config`，验证 AI 读取的文件集合不同
- **涉及系统**: Plugin 命令层
- **验收标准**:
    - [ ] `/zerosearch <query>` — 独立命令文件，只加载香农策略 + 搜索执行
    - [ ] `/zerosearch-config` — 独立命令文件，只加载配置逻辑
    - [ ] `/zerosearch-start` / `/zerosearch-stop` — 独立命令文件，只加载 Daemon 管理逻辑
    - [ ] `/zerosearch-stop` 关闭 Chrome 窗口 — 从 v0.3 行为继承

---

### 4.2 搜索策略层 — 香农提示词工程

#### US-022: 香农搜索策略 Skill [REQ-022] (优先级: P0)

- **故事描述**: 作为一个 Claude，我想要一个内建的香农搜索策略 Skill，指导我如何将用户的自然语言查询转化为高信息量的搜索提示词，以便 Google AI Mode 返回更精准的结果。
- **用户价值**: 搜索从"原样转发"升级为"经过信息论优化的意图表达"
- **独立可测性**: 对比同一查询在 v0.3（原样搜索）和 v0.4（香农策略优化后搜索）的结果精准度
- **涉及系统**: ShannonSearchSkill
- **验收标准**:
    - [ ] Skill 包含完整的香农信息论搜索指导原则（从快速搜索策略.md 提取）
    - [ ] Skill 指导 Claude 执行：①提取意图 ②选择高信息量关键词 ③组合独立维度词 ④匹配目标语言 ⑤构造最终搜索查询
    - [ ] Skill 提供关键词信息量评估框架：专业术语 > 具体数字 > 独特表述 >> 通用词
    - [ ] Skill 指导语言匹配：搜索日本内容用日语、英文内容用英语、中文内容用中文
    - [ ] Skill 指导容错思维：高信息量关键词即使有偏差也优于低信息量精准关键词

---

#### US-023: Google AI Mode 执行 Skill [REQ-023] (优先级: P0)

- **故事描述**: 作为一个 Claude，我想要一个 Google AI Mode 执行 Skill，负责实际调用浏览器引擎完成搜索并返回结构化结果。
- **用户价值**: 搜索执行与搜索策略分离，各司其职
- **独立可测性**: 通过 CLI 直接调用搜索执行逻辑，验证端到端搜索功能
- **涉及系统**: GoogleAIModeSkill, BrowserEngine, ContentExtractor, MarkdownConverter
- **验收标准**:
    - [ ] Skill 调用 BrowserEngine（复用 v0.3 Chrome Daemon）
    - [ ] Skill 调用 ContentExtractor 提取 AI 回答 + 引用（复用 v0.3）
    - [ ] Skill 调用 MarkdownConverter 格式化输出（复用 v0.3）
    - [ ] 输出格式包含：AI 综合回答 + 引用脚注 + 搜索耗时
    - [ ] LRU 缓存正常工作（50条/5min TTL）— 保持 v0.3 行为
    - [ ] 6 级退出码正常工作（0/1/2/3/4/5/130）— 保持 v0.3 行为

---

### 4.3 用户体验层

#### US-024: 统一搜索入口 [REQ-024] (优先级: P0)

- **故事描述**: 作为一个用户，我想要一个统一的 `/zerosearch <query>` 命令，自动运用香农策略优化查询后执行搜索，一次调用完成。
- **用户价值**: 简单直接，不需要理解内部策略，输入想查什么就得到高质量结果
- **独立可测性**: 执行 `/zerosearch React 19 新特性`，验证自动优化查询后搜索质量优于直接搜索
- **涉及系统**: ZeroSearchCommand, ShannonSearchSkill, GoogleAIModeSkill
- **验收标准**:
    - [ ] **Given** 用户输入自然语言查询，**When** 执行 `/zerosearch <query>`，**Then** 自动经过香农策略优化查询 → Google AI Mode 搜索 → 返回结构化结果
    - [ ] **Given** Chrome Daemon 未运行，**When** 执行 `/zerosearch`，**Then** 自动冷启动 Chrome（~5s），行为与 v0.3 一致
    - [ ] **Given** Chrome Daemon 已运行，**When** 执行 `/zerosearch`，**Then** 热搜索 <1s，行为与 v0.3 一致
    - [ ] **Given** Chrome 被意外关闭，**When** 执行 `/zerosearch`，**Then** 自动检测并冷启动重建（幽灵连接恢复），行为与 v0.3 一致
    - [ ] 不做自动多轮迭代 — 一次搜索返回一次结果。Claude 可建议更优关键词供用户手动追问

---

#### US-025: 搜索配置管理 [REQ-025] (优先级: P1)

- **故事描述**: 作为一个用户，我想要通过 `/zerosearch-config` 将 ZeroSearch 设为默认搜索工具。Chrome 使用独立 Profile 自动管理，无需手动配置。
- **用户价值**: 统一配置入口，不需要记 CLI 参数
- **独立可测性**: 首次安装后执行 `/zerosearch-config`，验证 AskUserQuestion 三选项引导
- **涉及系统**: SearchConfigCommand
- **验收标准**:
    - [ ] AskUserQuestion 三选项引导（设为默认搜索工具：用户级/项目级/否）
    - [ ] 配置结果写入 `~/.cache/zerosearch/config.json`

---

#### US-026: Daemon 手动控制 [REQ-026] (优先级: P2)

- **故事描述**: 作为一个高级用户，我想要手动启停 Chrome Daemon。
- **用户价值**: 与 v0.3 行为完全一致，只是入口从 SKILL.md 迁移到独立命令文件
- **独立可测性**: 执行 `/zerosearch-start` 启动 Chrome，`/zerosearch-stop` 关闭，验证与 v0.3 行为一致
- **涉及系统**: DaemonCommand, BrowserEngine
- **验收标准**:
    - [ ] `/zerosearch-start`: Chrome 冷启动并保持打开（不搜索）— 与 v0.3 一致
    - [ ] `/zerosearch-stop`: 关闭 Chrome + 清理状态文件 — 与 v0.3 一致
    - [ ] 重复 start/stop 幂等 — 与 v0.3 一致

---

### 4.4 迁移层

#### US-027: v0.3 代码零破坏迁移 [REQ-027] (优先级: P0)

- **故事描述**: 作为一个开发者，我想要 v0.3 的底层引擎代码完整迁移到 Plugin 目录，不改动任何业务逻辑，以确保不引入回归。
- **用户价值**: 零风险迁移，45 个测试全部通过
- **独立可测性**: 迁移后运行全部 45 个测试，验证零失败
- **涉及系统**: BrowserEngine, SearchEngine, ContentExtractor, MarkdownConverter
- **验收标准**:
    - [ ] `src/browser/` → `<plugin>/src/browser/` (纯目录移动)
    - [ ] `src/search/` → `<plugin>/src/search/` (纯目录移动)
    - [ ] `src/extractor/` → `<plugin>/src/extractor/` (纯目录移动)
    - [ ] `src/converter/` → `<plugin>/src/converter/` (纯目录移动)
    - [ ] `tests/` → `<plugin>/tests/` (纯目录移动)
    - [ ] import 路径更新（如 `from src.browser` → 插件内相对导入）
    - [ ] 全部 45 个测试通过
    - [ ] CLI 入口 `run.py` 路径更新

---

## 5. 与 v0.3 的关系

| v0.3 保留（不动逻辑） | v0.3 变更 | v0.3 废弃 |
|----------------------|----------|----------|
| BrowserEngine (Chrome Daemon 全部) | SKILL.md → plugin.json + 模块化 commands/skills | SKILL.md 原文件 |
| ContentExtractor (全部) | 搜索入口：SKILL.md 触发 → `/zerosearch` 命令触发 | — |
| MarkdownConverter (全部) | 搜索策略：无 → 香农信息论 Skill | — |
| SearchEngine 编排逻辑 | 配置：ASK 引导 → `/zerosearch-config` 命令 | — |
| LRU 缓存 (50条/5min) | 文件位置：src/ → plugin/src/ | — |
| 6 级退出码 | import 路径更新 | — |
| setup.sh | setup.sh 更新安装 Plugin 步骤 | — |
| requirements.txt | requirements.txt 不变 | — |
| 45 个测试 | 测试路径 tests/ → plugin/tests/ | — |

---

## 6. 关键用户流程 (Key User Flows)

```
用户输入: /zerosearch React 19 Server Components 怎么优化性能

Step 1 — 香农策略 Skill
  ├─ 提取意图: React 19 Server Components 性能优化
  ├─ 选择高信息量词: "Server Components" "streaming SSR" "React 19" "performance"
  ├─ 去掉通用词: "怎么" "优化"
  ├─ 语言匹配: 中文查询 → 中英文混合关键词（目标内容为英文技术文档）
  └─ 构造最终查询: "React 19 Server Components streaming SSR performance optimization"

Step 2 — Google AI Mode Skill
  ├─ BrowserEngine: 检测 Daemon → 热搜索创建标签页
  ├─ 导航: Google AI Mode (udm=50) + 优化后的查询
  ├─ ContentExtractor: 等待 AI 完成 → 提取回答 + 引用
  ├─ MarkdownConverter: HTML→Markdown + 脚注
  └─ 返回: 结构化搜索结果

Step 3 — 可选追问（用户手动触发）
  └─ Claude 建议: "可尝试搜索 'React 19 RSC streaming partial prerendering' 获取更深信息"
     └─ 用户决定是否继续
```

---

## 7. 约束与限制 (Constraint Analysis)

### 7.1 技术约束

- **插件框架**: Claude Code Plugin 标准（plugin.json + commands/ + skills/ + hooks/）
- **Python**: ≥3.10 — 与 v0.3 一致
- **浏览器引擎**: Patchright (Chromium) ≥1.55,<2 — 与 v0.3 一致
- **平台**: macOS — 与 v0.3 一致
- **底层引擎**: 完整复用 v0.3，不修改业务逻辑
- **新依赖**: 零新 Python 依赖

### 7.2 安全与合规

- **数据安全**: 搜索查询经 Google 传输，不存储额外数据
- **进程隔离**: Chrome Daemon 使用独立 Profile（与 v0.3 一致）

---

## 8. 非功能需求

| 类别 | 需求 | 度量 |
|------|------|:--:|
| 搜索性能（冷启动） | 与 v0.3 持平 | ≤5s |
| 搜索性能（热搜索） | 与 v0.3 持平 | <1s |
| 搜索性能（缓存命中） | 与 v0.3 持平 | <1ms |
| 模块化 | AI 只读取当前命令相关的文件 | 交叉验证 |
| 测试回归 | 全部 45 个测试通过 | 零失败 |
| CAPTCHA 率（未登录） | 与 v0.3 持平 | <10% |
| CAPTCHA 率（已登录） | 与 v0.3 持平 | <1% |
| Token 效率 | 搜索结果输出 | 与 v0.3 一致 |

---

## 9. 完成标准 (Definition of Done)

- [ ] Plugin 结构合法（plugin.json 验证通过）
- [ ] 所有 commands 可独立触发
- [ ] 香农搜索策略 Skill 包含完整指导
- [ ] 全部 45 个 v0.3 测试通过（零回归）
- [ ] 新功能有对应测试覆盖
- [ ] setup.sh 更新为 Plugin 安装流程
- [ ] README 更新 v0.4 架构说明

---

## 10. 附录 (Appendix)

### 10.1 术语表 (Glossary)

- **Plugin**: Claude Code Plugin — 标准化的插件容器，包含 plugin.json + commands/ + skills/ + hooks/
- **香农信息论 (Shannon Information Theory)**: 信息量 I(x) = -log₂P(x)，低概率关键词携带高信息量，搜索更精准
- **提示词工程 (Prompt Engineering)**: 将香农信息论原则编码为可执行的搜索查询构造策略
- **贝叶斯更新 (Bayesian Updating)**: 每轮搜索降低条件熵 H(目标|证据)，直到信息充分。由用户手动触发，非自动
- **Google AI Mode**: Google 搜索的 AI 模式 (udm=50)，自动综合 100+ 网站生成结构化回答
- **Chrome Daemon**: 常驻 Chrome 进程（v0.3 引入的机制），首次冷启动后保持存活
- **高信息量关键词**: P(词) 极低的词 — 专业术语、具体数字、独特表述、具体型号
- **通用词**: P(词) 极高的词 — "怎么"、"方法"、"优化"等，携带极低信息量

### 10.2 参考资料

- 香农搜索策略: `搜索策略/快速搜索策略.md` — 香农信息论 + Google AI Mode 实践验证
- v0.3 PRD: `.anws/v3/01_PRD.md`
- v0.3 架构: `.anws/v3/02_ARCHITECTURE_OVERVIEW.md`
- v0.3 概念模型: `.anws/v3/concept_model.json`
