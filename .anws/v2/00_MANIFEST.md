# .anws v2 - 版本清单

**创建日期**: 2026-05-20
**状态**: Active
**前序版本**: v1 (Camoufox/Firefox)

## 版本目标

底层引擎从 Camoufox (Firefox) 迁移到 Patchright (Chromium)，实现 Chromium 原生代理继承、CDP 级反检测、更快的冷启动速度。

## 主要变更

- 浏览器引擎：Camoufox (Firefox v135) → Patchright (Chromium undetected)
- 代理策略：手动系统代理检测 → Chromium 原生继承系统代理
- 反检测：浏览器层指纹随机化 → CDP 协议级反检测（Runtime.enable / Console.enable 补丁）
- 依赖管理：Git Submodule (camoufox) → pip 安装 (patchright)
- 安装流程：`git submodule update + camoufox fetch` → `pip install patchright && playwright install chromium`
- 性能目标：冷启动 ≤5s（原版 ~8s），缓存命中 <1ms

## 文档清单

- [x] 00_MANIFEST.md (本文件)
- [x] 01_PRD.md
- [x] 02_ARCHITECTURE_OVERVIEW.md
- [x] 03_ADR/
- [ ] 04_SYSTEM_DESIGN/ (BrowserEngine 待 /design-system)
- [x] 05_TASKS.md (由 /blueprint 生成)
- [x] 06_CHANGELOG.md
