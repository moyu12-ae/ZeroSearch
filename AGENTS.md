# AGENTS.md - AI 协作协议

> **"如果你正在阅读此文档，你就是那个智能体 (The Intelligence)。"**
> 
> 这个文件是你的**锚点 (Anchor)**。它定义了项目的法则、领地的地图，以及记忆协议。
> 当你唤醒（开始新会话）时，**请首先阅读此文件**。

---

## 🧠 30秒恢复协议 (Quick Recovery)

**当你开始新会话或感到"迷失"时，立即执行**:

1. **读取根目录的 AGENTS.md** → 获取项目地图
2. **查看下方"当前状态"** → 找到最新架构版本
3. **读取 `.anws/v{N}/05_TASKS.md`** → 了解当前待办
4. **开始工作**

---

## 🗺️ 地图 (领地感知)

以下是这个项目的组织方式：

| 路径 | 描述 | 访问协议 |
|------|------|----------|
| `src/` | **实现层**。实际的代码库。 | 通过 Task 读/写。 |
| `.anws/` | **统一架构根目录**。包含版本化架构状态与升级记录。 | **只读**(旧版) / **写一次**(新版) / `changelog` 由 CLI 维护。 |
| `.anws/v{N}/` | **当前真理**。最新的架构定义。 | 永远寻找最大的 `v{N}`。 |
| `.anws/changelog/` | **升级记录**。`anws update` 生成的变更记录。 | 由 CLI 自动维护，请勿删除。 |
| `target-specific workflow projection` | **工作流**。`/genesis`, `/blueprint` 等。 | 读取当前 target 对应的原生投影文件。 |
| `target-specific skill projection` | **技能库**。原子能力。 | 调用当前 target 对应的原生投影文件。 |
| `.nexus-map/` | **知识库**。代码库结构映射。 | 由 nexus-mapper 生成。 |

## 🛠️ 工作流注册表

> [!IMPORTANT]
> **工作流优先原则**：当任务匹配某个工作流，或你判断当前任务**明显符合、基本符合、甚至只是疑似符合**某个工作流的适用场景时，**都必须先读取相应文件**，并严格遵循其中的步骤执行。工作流是经过精心设计的协议，而非可选参考。
>
> **触发流程**：
> 1. 用户提及工作流名称，或你判断当前任务明显符合、基本符合、甚至只是疑似符合某个工作流的适用场景时，都必须先读取相应文件
> 2. **立即读取** 相应工作流文件
> 3. **严格遵循**工作流中的步骤执行
> 4. 在检查点暂停等待用户确认

| 工作流 | 触发时机 | 产出 |
|--------|---------|------|
| `/quickstart` | 新用户入口 / 不知道从哪开始 | 编排其他工作流 |
| `/genesis` | 新项目 / 重大重构 | PRD, Architecture, ADRs |
| `/probe` | 变更前 / 接手项目 | `.anws/v{N}/00_PROBE_REPORT.md` |
| `/design-system` | genesis 后 | 04_SYSTEM_DESIGN/*.md |
| `/blueprint` | genesis 后 | 05_TASKS.md + AGENTS.md 初始 Wave |
| `/change` | 进入 forge 编码后的任务局部修订 | 更新 TASKS + SYSTEM_DESIGN (仅修改) + CHANGELOG |
| `/explore` | 调研时 | 探索报告 |
| `/challenge` | 决策前质疑 | 07_CHALLENGE_REPORT.md (含问题总览目录) |
| `/forge` | 编码执行 | 代码 + 更新 AGENTS.md Wave 块 |
| `/craft` | 创建工作流/技能/提示词 | Workflow / Skill / Prompt 文档 |
| `/upgrade` | `anws update` 后做升级编排 | 判断 Minor / Major，并路由到 `/change` 或 `/genesis` |

---

## 📜 宪法 (The Constitution)

1. **版本即法律**: 不"修补"架构文档，只"演进"。变更必须创建新版本。
2. **显式上下文**: 决策写入 ADR，不留在"聊天记忆"里。
3. **交叉验证**: 编码前对照 `05_TASKS.md`。我在做计划好的事吗？
4. **美学**: 文档应该是美的。善用 Markdown 和 Emoji。

---
## 🔄 项目状态保留区

<!-- AUTO:BEGIN — 项目状态保留区（升级时唯一保留的部分，请勿手动修改区块边界） -->

## 📍 当前状态 (由 Workflow 自动更新)

- **最新架构版本**: `.anws/v1`
- **活动任务清单**: [05_TASKS.md](.anws/v1/05_TASKS.md) ✅ 23 任务, 4 Sprints
- **待办任务数**: 23
- **最近一次更新**: `2026-05-19`

### 🌊 Wave 1 ✅ — 项目骨架 + 独立模块
T1.1.1, T1.1.2, T3.1.3, T4.1.1, T4.1.2, T4.1.3

---

## 🌳 项目结构 (Project Tree)

```text
google-ai-mode-skill/              # 仓库根 = Skill 部署位置
├── SKILL.md                       # Claude Code Skill 定义
├── README.md
├── requirements.txt
├── libs/
│   └── camoufox/                  # Camoufox (Git Submodule)
├── src/
│   ├── browser/                   # BrowserEngine
│   ├── search/                    # SearchEngine
│   ├── extractor/                 # ContentExtractor
│   └── converter/                 # MarkdownConverter
├── results/                       # 搜索结果
├── .cache/                        # 本地缓存 + 浏览器 Profile
├── .anws/v1/                      # 架构文档 (当前版本)
└── .claude/                       # Claude Code 工作流
```

---

## 🧭 导航指南 (Navigation Guide)

- **架构总览**: `.anws/v1/02_ARCHITECTURE_OVERVIEW.md`
- **ADR**: `.anws/v1/03_ADR/` (跨系统决策的唯一记录源)
- **详细设计**: `.anws/v1/04_SYSTEM_DESIGN/` ✅ (4 系统已完成)
- **任务清单**: 待 `/blueprint` 执行 (将生成 `.anws/v1/05_TASKS.md`)
- **BrowserEngine**: 源码 `src/browser/` → 设计 [browser-engine.md](.anws/v1/04_SYSTEM_DESIGN/browser-engine.md) ✅
- **SearchEngine**: 源码 `src/search/` → 设计 [search-engine.md](.anws/v1/04_SYSTEM_DESIGN/search-engine.md) ✅
- **ContentExtractor**: 源码 `src/extractor/` → 设计 [content-extractor.md](.anws/v1/04_SYSTEM_DESIGN/content-extractor.md) ✅
- **MarkdownConverter**: 源码 `src/converter/` → 设计 [markdown-converter.md](.anws/v1/04_SYSTEM_DESIGN/markdown-converter.md) ✅

---

### 技术栈决策
- 语言: Python 3.8+
- 浏览器引擎: Camoufox (Firefox 133+)，Git Submodule 管理
- HTML 解析: BeautifulSoup4
- Markdown 转换: html-to-markdown
- 缓存: collections.OrderedDict + TTL

### 系统边界
- **BrowserEngine**: Camoufox 浏览器生命周期、Profile 持久化、反检测配置
- **SearchEngine**: 搜索全流程编排、LRU 缓存、分级错误降级
- **ContentExtractor**: AI 完成检测、多语言引用提取、DOM 清洗
- **MarkdownConverter**: HTML→Markdown、脚注格式化、文件保存

### 活跃 ADR
- **ADR-001**: 浏览器引擎选型 — Camoufox (总分 51/60 vs Patchright 36/60)
- **ADR-002**: Camoufox 集成方式 — Git Submodule (精确版本锁定 + 即时上游更新)
- **ADR-003**: 测试策略 — E2E 集成测试为主 + 单元测试为辅，无 CI

### 当前任务状态
- [由 blueprint/forge 自动更新]

<!-- AUTO:END -->

---
> **状态自检**: /genesis 完成！运行 `/design-system` 或 `/blueprint` 继续。
