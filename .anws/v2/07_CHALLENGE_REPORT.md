# ZeroSearch v0.2 质疑报告 (Challenge Report)

> **审查日期**: 2026-05-20
> **审查范围**: `.anws/v2/` 全部设计文档 + 全量源代码
> **累计轮次**: R3（R1 已归档，R2 为 Wave 审计）

---

## 📋 问题总览

### 第 R1 轮 ✅ 已归档
| 编号 | 严重度 | 摘要 |
|------|:----:|------|
| R1-C1 | 🔴 | SKILL.md 设计缺失 |
| R1-H1 ~ H4 | 🟠 | 版本约束 / Profile 路径 / AI 检测 / Chrome 锁定 (4 项) |
| R1-M1 ~ M4 | 🟡 | CAPTCHA 率 / CLAUDE.md / CLI flags / 迁移 (4 项) |
| R1-L1 | 🟢 | 测试计划 |

> **全部已修复** (详见 [06_CHANGELOG.md](06_CHANGELOG.md) 2026-05-20 — Challenge R1 修复)

### 第 R3 轮（当前活跃 — 代码审查）

| ID | 严重度 | 摘要 | 状态 |
|----|:------:|------|:--:|
| R3-C1 | 🔴 | run.py 仍包含功能性 Camoufox 代码 | ✅ 已修复 |
| R3-H1 | 🟠 | README.md 仍描述 v0.1 Camoufox/Firefox | ⏳ |
| R3-M1 | 🟡 | 多个文件 docstring 残留 "Camoufox" 字样 | ⏳ |
| R3-M2 | 🟡 | cli.py argparse description 仍写 "Camoufox 浏览器" | ⏳ |

---

## 📊 审查摘要

**审查模式**: `FULL`（代码审查 + 设计 + 测试验证）
**整体判断**: 🟢 代码可行性通过，测试全绿，1 个 Critical 已修复
**高信号结论**: v0.2 核心代码迁移完整（BrowserEngine Patchright 化、Profile 双模式、AI 优化、测试 29 项全通）。唯一的功能性遗漏 run.py 已修复。残留文档引用（README/docstring）不影响运行但应更新。

| 指标 | 数值 |
|------|------|
| Critical | 1 (已修复) |
| High | 1 |
| Medium | 2 |
| Low | 0 |
| Total | 4 |

| 证据来源 | 结论 |
|----------|------|
| 编译检查 | ✅ 15/15 模块 |
| 单元测试 | ✅ 29/29 全部通过 |
| 集成检查 | ✅ 7/7 核心链路 |
| Camoufox 引用扫描 | ⚠️ docstring 残留 |

---

## 🔍 核心发现清单

### R3-C1 🔴 Critical — run.py 仍包含功能性 Camoufox 代码 ✅ 已修复

**位置**: `src/search/run.py:90,148-164`
**契约**: PRD REQ-005 — pip 安装替代 Git Submodule
**Pass 模式**: 业务契约违背

`_needs_install()` 检查 `import camoufox`（应检查 `import patchright`），`_install_deps()` 尝试初始化 `libs/camoufox/` submodule 并安装 `camoufox/pythonlib`。Camoufox submodule 已删除，当 venv 不存在时安装会失败。

**v1 对比**: 类似 v1 "setup.sh 和多个文件在重写中被遗漏"——关键功能文件在 Sprint 2/3 重写时未被覆盖。

**修复**: 重写 `_needs_install` 检查 `patchright`，简化 `_install_deps` 移除所有 submodule 逻辑。

**验证**: `python -c "from src.search.run import _needs_install; assert 'patchright' in inspect.getsource(_needs_install)"`

---

### R3-H1 🟠 High — README.md 仍描述 v0.1

**位置**: `README.md` 全文
**契约**: 文档契约（README 描述的项目应匹配实际代码）
**Pass 模式**: 文档契约违背

README.md 仍包含完整的 v0.1 Camoufox/Firefox 描述：
- "Powered by Camoufox (Firefox-based)"
- Camoufox badge（v0.5.0）
- ".gitmodules / libs/camoufox/ 目录结构"
- "Camoufox 替代 Patchright"
- "git submodule update --remote"

这些信息与 v0.2 实际实现（Patchright + Chrome + pip 安装）完全矛盾。新用户按 README 操作会找不到 `libs/camoufox/`。

**影响**: 新用户文档引导错误，但代码本身不受影响（setup.sh 和 SKILL.md 是正确的）。

**建议**: 更新 README.md 为 v0.2 内容（Patchright + Chrome + pip 安装 + 双 Profile 模式）。

---

### R3-M1 🟡 Medium — 多个文件 docstring 残留 Camoufox 字样

**位置**: 
- `src/extractor/citation_extractor.py:169` — "page : Camoufox Page 对象"
- `src/extractor/ai_detector.py:9` — "输入: Camoufox Page 对象"
- `src/extractor/extractor.py:38` — "page: Camoufox 渲染完成的 Page 对象"
- `src/search/error_handler.py:140,210,257,322` — docstring 仍写 "Camoufox/Playwright"
- `src/search/cli.py:42` — argparse description "通过 Camoufox 浏览器..."
- `src/browser/browser_factory.py:4` — 注释 "替代 Camoufox"（这行 OK，说明迁移关系）

**影响**: 不影响运行，但会误导未来维护者。cli.py 的 argparse description 是面向用户的，应修正。

**建议**: 批量替换 docstring 中的 "Camoufox" → "Patchright" （保留 browser_factory.py 的迁移说明注释）。

---

### R3-M2 🟡 Medium — cli.py argparse description 向用户展示错误信息

**位置**: `src/search/cli.py:42`
**契约**: 文档契约

```python
description="Google AI Mode Search — 通过 Camoufox 浏览器执行 Google AI Mode 搜索"
```

这是 `--help` 输出给用户的文本，写的是 "Camoufox 浏览器" 但实际用的是 Patchright Chrome。

**建议**: 改为 "ZeroSearch — Patchright Chromium Google AI Mode 搜索"。

---

## 🚦 最终判断

- [x] 🟢 项目可继续，风险可控

**判断依据**: 4 个发现中 1 个 Critical 已修复（run.py），剩余 3 个为文档级别问题（README + docstring），不影响代码运行。29 测试全绿，15 模块全编译，7 项集成检查通过。核心迁移（Camoufox → Patchright）在代码层面完整。

---

## 附录：完整验证证据

### A. 测试结果
```
29 passed in 0.13s
- 17 原有测试 (Cache + DOM Cleaner + Footnote)
- 12 新增测试 (StealthConfig + Profile + AI Optimization)
```

### B. 模块编译
```
✅ 15/15 模块全部可导入 (browser ×4 + search ×4 + extractor ×4 + converter ×3)
```

### C. Camoufox 引用扫描
```
src/search/run.py: ❌ functional Camoufox code → FIXED
src/extractor/: ⚠️ docstring only (no functional impact)
src/search/error_handler.py: ⚠️ docstring only
src/search/cli.py: ⚠️ argparse description
README.md: ❌ full v0.1 content
```

### D. 集成检查
| # | 检查项 | 结果 |
|---|--------|:--:|
| 1 | EXIT_PROFILE_LOCKED = 5 | ✅ |
| 2 | PROFILE_CONFIG_PATH correct | ✅ |
| 3 | StealthUtils.random_delay works | ✅ |
| 4 | dom_cleaner strips Google UI noise | ✅ |
| 5 | footnote compact format [1] Title — URL | ✅ |
| 6 | LRUCache works (with auto-timestamp) | ✅ |
| 7 | Profile resolve with explicit/fresh path | ✅ |

### E. v1 已知错误预防验证

| v1 错误 | v0.2 状态 |
|---------|----------|
| `_setup_import_path()` 死代码 | ✅ 已在 main() 中调用 (cli.py:136) |
| `camoufox install` 错误命令 | ✅ 改用 `patchright install chrome` + venv python |
| Chrome UA on Firefox | ✅ 真 Chrome, UA 自动匹配 |
| `detect_system_proxy()` 需要 | ✅ 已移除, Chromium 自动继承 |
| `input()` EOFError | ✅ 改为 AskUserQuestion (SKILL.md 层) |
| CAPTCHA 检测关键词太窄 | ✅ 4 关键词 + wait + title 检测 |
| Profile path 文档不一致 | ✅ Architecture 列出 Option A/B |
| requirements.txt 缺依赖 | ✅ patchright>=1.55,<2 |
| setup.sh 使用系统 python3 | ✅ 已修复为 "$VENV_DIR/bin/python" |
| README 描述与代码矛盾 | ❌ **复现**——README.md 仍描述 v0.1 |
| 关键文件在重写中被遗漏 | ❌ **复现**——run.py 未更新 → 已修复 |
