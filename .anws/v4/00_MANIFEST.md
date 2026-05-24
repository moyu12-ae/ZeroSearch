# .anws v4 - 版本清单

**创建日期**: 2026-05-22
**状态**: Active
**前序版本**: v3 (ZeroSearch v0.3 — Chrome Daemon)

## 版本目标

ZeroSearch v0.4：从单 SKILL.md 升级为 Claude Code Plugin，引入基于香农信息论的提示词工程，让搜索从"关键词匹配"升级为"意图导向的 AI 搜索"。

## 主要变更

- **Plugin 化**: 从单 SKILL.md 升级为 Claude Code Plugin（commands/skills/agents/hooks 模块化分离），AI 只读取需要的文件
- **香农提示词工程**: 基于香农信息论（I(x) = -log₂P(x)）的搜索查询构造策略，用高信息量关键词明确表达搜索意图
- **统一搜索模式**: 不做 Quick/Deep 分离，不做两阶段流水线，不做自动二次阅读。一次搜索完成
- **模块化命令**: /zerosearch（搜索）、/zerosearch-config（配置）、/zerosearch-start/stop（Daemon 管理）
- **底层引擎全部复用**: BrowserEngine、ContentExtractor、MarkdownConverter 从 v0.3 完整继承

## 文档清单

- [x] 00_MANIFEST.md (本文件)
- [x] 01_PRD.md
- [x] 02_ARCHITECTURE_OVERVIEW.md
- [x] 03_ADR/
- [ ] 04_SYSTEM_DESIGN/
- [x] 05_TASKS.md (已生成 + 已增加 S4 反检测任务)
- [x] 06_CHANGELOG.md
- [x] 07_CHALLENGE_REPORT.md (Round 5 反检测文档同步审计)
