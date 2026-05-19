# Google AI Mode Skill 质疑报告 (Challenge Report)

> **审查日期**: 2026-05-19
> **审查范围**: `.anws/v1/` 全部设计文档 + `src/` 全部实现代码
> **累计轮次**: 2

---

## 问题总览

### 第1轮 — ✅ 全部修复 (已归档)

| CH1-01~07 | 7项 | 性能/引用/测试/去重/持久化/异常/噪声 | ✅ 全部修复 |

### 第2轮（当前活跃 — 深度代码审计）

| 严重度 | 数量 | 摘要 | 状态 |
|--------|:--:|------|:--:|
| Critical | 3 | 绝对导入崩溃 + 阶段3误检 + try/except缩进导致NoneType | ⏳ |
| High | 5 | 时间基准混用 + udm14重试 + handle_timeout未调用 + 测试<10% + 内存缩容未实现 | ⏳ |
| Medium | 3 | Citation重复定义 + ExtractionResult缺字段 + ConvertResult未实现 | ⏳ |
| Low | 3 | docstring不一致 + geoip字段名 + 版本号未在报错展示 | ⏳ |

---

## 审查摘要

**审查模式**: `FULL` (第2轮: 代码逐行审计 + 设计文档交叉验证)
**整体判断**: 🟡 需先修复 Critical 问题
**高信号结论**: 第1轮 7 问题已全修复。第2轮深度审计通过 2 个并行 Explore agent 发现 14 个新问题，其中 3 个 Critical 会导致运行时崩溃。

| 指标 | 数值 |
|------|:--:|
| Critical | 3 |
| High | 5 |
| Medium | 3 |
| Low | 3 |
| Total Findings | 14 |

---

## 🔍 核心发现清单

| ID | 严重度 | 文件:行号 | 发现 | 影响 | 建议 |
|----|--------|------|------|------|------|
| R2-C1 | 🔴 Critical | `cli.py:123` | `from src.search.engine import SearchEngine` 绝对导入在子进程和直接执行时均失败（`ModuleNotFoundError: No module named 'src'`） | CLI 入口完全不可用 | 改为相对导入或添加 `sys.path` hack |
| R2-C2 | 🔴 Critical | `ai_detector.py:162` | 阶段3稳定性检查用 `_check_stage()` 而非文本相等对比 — 只要长度>200就标记稳定，不验证内容是否真正不变 | AI 生成中途被截断，输出不完整 | 改为 `_get_page_text(page) == stable_text` |
| R2-C3 | 🔴 Critical | `citation_extractor.py:202-214` | CSS回退的 try/except 缩进在 for 循环内部，`elements` 为 None 时 `for el in elements` 抛出 `TypeError` 无法被捕获 | CSS回退完全崩溃 | 修复缩进，加 None 保护 |
| R2-H1 | 🟠 High | `cache.py:54` vs `engine.py:82` | `time.monotonic()` (cache) 与 `time.time()` (engine) 混用 — 系统时间调整导致 TTL 计算错误 | 缓存永不过期或过早过期 | 统一使用 `time.monotonic()` |
| R2-H2 | 🟠 High | `error_handler.py:214` | `handle_timeout` 重试用 `udm=14` 而非 `udm=50` — 导航到普通搜索而非 AI Mode | 超时重试永远得不到 AI 结果 | 改为 `udm=50` |
| R2-H3 | 🟠 High | `error_handler.py:176-219` + `engine.py:93-148` | `handle_timeout` 方法体完整但从未被 SearchEngine 调用 | 超时重试功能完全失效 | 在 `_run_search_pipeline` 中调用 |
| R2-H4 | 🟠 High | `tests/` vs `ADR-003` | 测试覆盖率 < 10%（3个测试文件），ADR-003 承诺 > 70%，T6.2.2 标记完成但远未达标 | 无回归保护 | 补充核心模块 pytest |
| R2-H5 | 🟠 High | `engine.py` + US-003 AC4 | PRD 承诺"内存不足时缓存自动缩容" — 代码无 `psutil` / `resource` 检测，无 `shrink()` 方法 | OOM 风险无防护 | 添加简单缩容或更新 PRD |
| R2-M1 | 🟡 Medium | `citation_extractor.py:22` + `footnote_formatter.py:16` | `Citation` 在两个模块中独立定义，字段不同步风险 | 字段变更时类型不一致 | 抽取到 `src/types.py` |
| R2-M2 | 🟡 Medium | `extractor.py:17` vs `content-extractor.md:257` | `ExtractionResult` 缺少设计定义的 `selector_hits` 字段 | 性能监控数据丢失 | 添加字段 |
| R2-M3 | 🟡 Medium | `engine.py:128` vs `markdown-converter.md:199` | 设计定义 `convert() -> ConvertResult` 单一入口，实际拆为两个函数，`ConvertResult`/`ConvertStats` 未实现 | 转换统计丢失 | 至少记录 fallback_used |
| R2-L1 | 🟢 Low | `dom_cleaner.py:123-129` | docstring 声明 raise ValueError 但实际 return "" | 文档欺骗 | 修 docstring |
| R2-L2 | 🟢 Low | `stealth.py:51` vs `browser-engine.md:340` | 字段名 `geoip`(设计) → `geolocation`(代码) | 命名不一致 | 统一命名 |
| R2-L3 | 🟢 Low | `browser_factory.py:84` vs US-006 AC3 | 报错不含 Camoufox 版本号 | 排查困难 | 添加 `camoufox.__version__` |

---

## 建议行动清单

### P0 - 立即处理 (阻塞)
1. **[R2-C1]** 修复 `cli.py` 导入路径
2. **[R2-C2]** 修正阶段3稳定性检查逻辑
3. **[R2-C3]** 修复 citation_extractor CSS回退缩进 + None保护

### P1 - 近期处理 (重要)
4. **[R2-H1]** 统一时间基准为 `time.monotonic()`
5. **[R2-H2]** 超时重试 URL 改为 `udm=50`
6. **[R2-H3]** Engine 中调用 `handle_timeout`
7. **[R2-H4]** 补充核心模块测试
8. **[R2-H5]** 实现缓存缩容或更新 PRD 承诺

### P2 - 持续改进
9. **[R2-M1~M3]** 统一 Citation 定义、补 ExtractionResult 字段、补转换统计
10. **[R2-L1~L3]** 修正 docstring、命名、版本号

---

## 🚦 最终判断

- [ ] 🟢 项目可继续，风险可控
- [x] 🟡 项目可继续，但需先解决 P0 问题
- [ ] 🔴 项目需要重新评估

**判断依据**: R2-C1 (CLI 不可用) 和 R2-C3 (CSS回退崩溃) 是运行时阻断性 bug，必须立即修复。
