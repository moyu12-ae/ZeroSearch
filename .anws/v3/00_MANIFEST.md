# .anws v3 - 版本清单

**创建日期**: 2026-05-21
**状态**: Active
**前序版本**: v2 (Patchright Chromium 迁移)

## 版本目标

v0.3 引入 Chrome Daemon（会话级浏览器常驻进程），首次搜索后 Chrome 保持存活，后续搜索只创建新标签页，将重复搜索耗时从 ~5s 降至 <1s。

## 主要变更

- **Chrome Daemon**: 首次冷启动后 Chrome 不关闭，后续搜索复用同一浏览器实例（只关标签页），后续搜索 <1s
- **手动启停**: `/zerosearch-start` / `/zerosearch-stop` 命令 + 关闭窗口即停止
- **存活检测与降级**: Chrome 被关闭后下次搜索自动冷启动重建

> **推迟到后续版本**: Plugin 化、Deep Research（多轮深度搜索）、Citation Crawler（引用爬取 + 本地剪藏）

## 文档清单

- [x] 00_MANIFEST.md (本文件)
- [x] 01_PRD.md
- [x] 02_ARCHITECTURE_OVERVIEW.md
- [x] 03_ADR/
- [ ] 04_SYSTEM_DESIGN/
- [ ] 05_TASKS.md (由 /blueprint 生成)
- [x] 06_CHANGELOG.md
