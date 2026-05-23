# ADR-003: Plugin 化架构模式

**状态**: Accepted
**日期**: 2026-05-22
**决策者**: ZeroSearch v0.4 genesis
**影响范围**: 全部系统

---

## 背景

v0.3 使用单 SKILL.md 文件作为 Claude Code Skill 的唯一入口。所有交互逻辑、命令路由、搜索指导全部塞在一个文件中。随着功能增长（搜索、配置、Daemon 启停、纠错），单一文件模式暴露出问题：

1. AI 每次读取整个 SKILL.md，即使只需执行搜索也要加载配置和 Daemon 管理指令
2. 新增功能只能在文件末尾追加，结构越来越松散
3. 无法利用 Claude Code Plugin 的模块化能力（commands/ + skills/ + hooks/ + agents/）

---

## 决策

**采用 Claude Code Plugin 架构，替换 v0.3 单 SKILL.md。**

### 方案对比

| 维度 | A: 保持单 SKILL.md | B: Plugin 化 (选择) |
|------|:--:|:--:|
| AI 上下文效率 | ❌ 读全部内容 (~500行) | ✅ 按需读取 (~100行/次) |
| 可维护性 | ❌ 追加式增长 | ✅ 独立文件，模块化 |
| 扩展性 | ❌ 新增功能靠追加 | ✅ 新增命令/技能文件 |
| 迁移成本 | ✅ 零成本 | ⚠️ 需重组目录结构 |
| 团队协作 | ❌ 单文件冲突 | ✅ 多文件并行 |
| Claude Code 规范 | ❌ 非标准 | ✅ 标准 Plugin 规范 |

### Plugin 结构

```text
plugin.json                  # Plugin 声明元数据
commands/
  zerosearch.md              # /zerosearch 命令 (Search + Shannon)
  zerosearch-config.md       # /zerosearch-config 命令
  zerosearch-start.md        # /zerosearch-start 命令
  zerosearch-stop.md         # /zerosearch-stop 命令
skills/
  shannon-strategy.md        # 香农搜索策略 (纯文本)
  search-execution.md        # 搜索执行 (编排引擎)
hooks/
  post-install.md            # 首次安装引导
src/                         # Python 引擎 (从 v0.3 完整迁移)
```

---

## 影响分析

### 正面影响
- AI 上下文精准控制：执行搜索时只读 `zerosearch.md` + `shannon-strategy.md` + `search-execution.md`，不需要加载配置/Daemon 管理文件
- CLI 兼容性：Python 引擎保持在 `src/`，CLI 入口 `run.py` 不变
- 标准化：符合 Claude Code Plugin 规范，可被 Plugin 生态识别和安装

### 负面影响
- 迁移成本：需要重组目录结构，更新 import 路径和 setup.sh
- 学习曲线：开发者需要理解 Plugin 规范

### 缓解措施
- 底层 Python 引擎代码零修改（纯路径移动），45 个测试确保零回归
- plugin.json 遵循 Claude Code Plugin 标准模板
- setup.sh 更新为 Plugin 安装路径

---

## 关联 ADR
- ADR-001 (v2): 技术栈选型（Plugin 不改变任何技术选型）
- ADR-002 (v3): Chrome Daemon CDP（Daemon 命令作为独立命令文件）
