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
5. **版本命名规范**: anws 架构版本号 (.anws/v1, v2, v3) 与产品版本号 (v0.1, v0.2, v0.3) 是两套独立体系。目录名/路径引用用 anws 版本号，文档内容中提软件时用产品版本号。

   | anws 架构版 | 产品版 | 说明 |
   |:--:|:--:|------|
   | `.anws/v1/` | ZeroSearch v0.1 | Camoufox Firefox 引擎 |
   | `.anws/v2/` | ZeroSearch v0.2 | Patchright Chromium 迁移 |
   | `.anws/v3/` | ZeroSearch v0.3 | Chrome Daemon 常驻进程 |

---
## 🔄 项目状态保留区

<!-- AUTO:BEGIN — 项目状态保留区（升级时唯一保留的部分，请勿手动修改区块边界） -->

## 📍 当前状态 (由 Workflow 自动更新)

- **最新架构版本**: `.anws/v3`
- **活动任务清单**: [05_TASKS.md](.anws/v3/05_TASKS.md) — 13 任务, 2 Sprint
- **待办任务数**: 0 (13/13 全部完成)
- **最近一次更新**: `2026-05-21`

### 🌊 Wave 1 ✅ — S1: Daemon 核心 (全部完成)
T1.0.1, T1.1.1, T1.1.2, T1.2.1, T1.2.2, T1.3.1, T1.4.1, INT-S1

### 🌊 Wave 2 ✅ — S2: 系统集成 (全部完成)
T2.1.1, T2.2.1, T2.2.2, T0.1.1, INT-S2

---

## 🌳 项目结构 (Project Tree)

```text
zerosearch/                        # 仓库根 = Skill 部署位置
├── SKILL.md                       # Claude Code Skill 定义
├── README.md                      # 项目说明
├── AGENTS.md                      # AI 协作协议
├── LICENSE                        # MIT 许可证
├── setup.sh                       # 首次安装脚本 (pip + patchright install chrome)
├── requirements.txt               # Python 依赖 (patchright>=1.55,<2)
├── .gitignore
├── src/
│   ├── browser/                   # BrowserEngine (Patchright + Chrome Daemon)
│   ├── search/                    # SearchEngine
│   ├── extractor/                 # ContentExtractor
│   └── converter/                 # MarkdownConverter
├── tests/                         # pytest 单元测试
├── results/                       # 搜索结果 (--save, 惰性创建)
├── .anws/v3/                      # 架构文档 (当前版本)
└── .claude/                       # Claude Code 工作流
```

---

## 🧭 导航指南 (Navigation Guide)

- **架构总览**: `.anws/v3/02_ARCHITECTURE_OVERVIEW.md`
- **ADR**: `.anws/v3/03_ADR/` (跨系统决策的唯一记录源)
- **详细设计**: 待 `/design-system` 执行后更新 (将填充 `.anws/v3/04_SYSTEM_DESIGN/`)
- **任务清单**: 待 `/blueprint` 执行后更新 (将生成 `.anws/v3/05_TASKS.md`)

### ADR ↔ SYSTEM_DESIGN 关系
- **ADR** 记录跨系统决策 (如技术栈、认证方式)
- **SYSTEM_DESIGN** §8 Trade-offs 引用 ADR,不复制决策内容
- 修改 ADR 时,检查"影响范围"章节,确认引用该 ADR 的系统

---

### 技术栈决策
- 语言: Python ≥3.10
- 浏览器引擎: Patchright (Chromium undetected fork)，pip 安装
- 反检测: CDP 协议级 (Runtime.enable / Console.enable 补丁)
- HTML 解析: BeautifulSoup4
- Markdown 转换: html-to-markdown (主) → markdownify (备) → html2text (保底)
- 缓存: collections.OrderedDict + TTL
- Daemon 连接: connect_over_cdp (CDP WebSocket)，0 新依赖

### 系统边界
- **BrowserEngine**: Patchright Chrome 生命周期、Daemon 状态文件管理、冷启动/热连接双路径、反检测配置、系统代理自动继承
- **SearchEngine**: 搜索全流程编排、Daemon 状态检测分支、LRU 缓存、分级错误降级
- **ContentExtractor**: AI 完成检测、多语言引用提取、DOM 清洗、AI 原生精简
- **MarkdownConverter**: HTML→Markdown、脚注格式化、文件保存

### 活跃 ADR
- **ADR-001 (v2)**: 浏览器引擎选型 — Patchright + 真 Chrome (227/240 vs Camoufox 141/240)
- **ADR-002 (v3)**: Chrome Daemon CDP 连接策略 — connect_over_cdp (233/240 vs Python Daemon 165/240)

### 当前任务状态
- 任务清单: .anws/v3/05_TASKS.md
- 总任务数: 13, P0: 6, P1: 4, P2: 1 — ✅ 全部完成 (45 tests pass)
- Sprint 数: 2
- Wave 1 建议: T1.0.1 (Spike), T1.1.1, T1.1.2, T1.2.1
- 最近更新: 2026-05-21

<!-- AUTO:END -->

---
> **状态自检**: /genesis Step 6 完成！运行 `/design-system` 或 `/blueprint` 继续。
