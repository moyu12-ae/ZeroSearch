# Google AI Mode Skill 质疑报告 (Challenge Report)

> **审查日期**: 2026-05-19
> **审查范围**: `.anws/v1/` 全部设计文档 + `src/` 全部实现代码
> **累计轮次**: 1

---

## 问题总览

### 第1轮（当前活跃）

| 严重度 | 数量 | 摘要 | 状态 |
|--------|:--:|------|:--:|
| Critical | 1 | 性能承诺严重失实：PRD ≤3s vs 实测 10.4s | ⏳ |
| High | 2 | 引用提取挂零 + 零自动化测试 | ⏳ |
| Medium | 3 | wait_for_ai 重复实现、浏览器非真正持久化、广泛异常吞噬 | ⏳ |
| Low | 1 | 消息输出杂乱（Camoufox patch 警告混入用户输出） | ⏳ |

---

## 审查摘要

**审查模式**: `FULL`
**整体判断**: 🟡 需先修复高优先问题
**高信号结论**: 管道通了但性能承诺不闭合（3x 差距）、引用提取选择器与实际 DOM 不匹配、零测试覆盖与 ADR-003 矛盾。这三个问题必须在进一步工作前修复。

| 指标 | 数值 |
|------|:--:|
| Critical | 1 |
| High | 2 |
| Medium | 3 |
| Low | 1 |
| Total Findings | 7 |

| 证据来源 | 结论 |
|----------|------|
| design-reviewer | 基于架构文档交叉验证 |
| task-reviewer | 跳过（tasks 覆盖完整） |
| Pre-Mortem | 性能承诺是系统最脆弱链路 |
| 承诺闭合检查 | Partial — 性能承诺未闭合 |

---

## 核心发现清单

| ID | 类别 | 严重度 | 契约/Pass | 位置 | 发现 | 影响 | 建议 |
|----|------|--------|-----------|------|------|------|------|
| CH-01 | 承诺失真 | 🔴 Critical | 性能承诺 | PRD §3.1 G1: ≤3s | 实测端到端 10.4s（导航 2.7s + AI 等待 7.3s + 转换 0.4s），超预算 3.5x | 用户等待时间远超预期，Skill 核心价值（快速搜索）受损 | 优化 AI 检测超时策略（7.3s 的 4 阶段检测是瓶颈），缩短阶段 3 稳定性检查间隔 |
| CH-02 | 接口失真 | 🟠 High | 结果承诺 | PRD §4 US-001 AC2 / DOM 实际结构 | E2E 测试中 citations=0，17 个选择器全部未命中 Google 当前 DOM | 引用提取不工作，输出缺少来源链接，违反核心功能承诺 | 用真实 Google AI Mode 页面 dump DOM，比对选择器与实际 HTML 结构 |
| CH-03 | 任务承接 | 🟠 High | ADR-003 | `05_TASKS.md` T6.2.2 / `src/` | ADR-003 承诺 pytest 覆盖率 >70%，但 `pytest src/` 显示 "no tests ran"，零测试文件 | 无回归测试保障，引擎变更时无法自动验证 | 补充至少 converter/ 和 cache.py 的 pytest 用例（这两个系统最容易测试） |
| CH-04 | 实现重复 | 🟡 Medium | 运行承诺 | `context_manager.py` L95 vs `ai_detector.py` | `BrowserContext.wait_for_ai()` 实现了简易版 AI 检测（3 个选择器），`ai_detector.py` 实现了完整 4 阶段策略。SearchEngine 使用后者但 BrowserContext 也暴露了前者 | 调用方可能误用简易版导致检测不准确 | 废弃 context_manager 中的 wait_for_ai，统一使用 ai_detector.detect_ai_completion |
| CH-05 | 状态承诺 | 🟡 Medium | 状态承诺 | PRD §4 US-002 / `BrowserContext` 实现 | 浏览器"预热常驻"仅在单次 CLI 调用内有效。每次 `python run.py --query` 启动新 Python 进程，BrowserContext 重新创建。无法跨 CLI 调用复用 | 首次搜索仍需 10s+，用户每次新查询都等于冷启动 | 短期：文档说明当前局限；长期：实现守护进程模式或 Unix socket 复用 |
| CH-06 | 错误承诺 | 🟡 Medium | 错误契约 | `src/` 30 处 `except Exception` | 广泛使用裸 `except Exception` 吞噬所有错误，不记录异常类型或堆栈 | 故障排查困难，CAPTCHA/网络/解析错误被统一吞噬 | 至少对关键路径（navigate、extract、convert）添加 `logger.exception()` 记录完整堆栈 |
| CH-07 | 观测承诺 | 🟢 Low | 审计承诺 | Camoufox 输出到 stdout | `Skipping unknown patch audio:seed` 等 Camoufox 内部日志直接打印到 stdout，污染用户可见输出 | 用户体验差，输出含无关技术噪声 | 重定向 Camoufox 日志到 stderr 或关闭 verbose |

---

## Pre-Mortem 分析

> 6 个月后，项目失败了。为什么？

### 失败场景 1: 性能优化进入死胡同
**Root Cause**: AI 完成检测的 4 阶段策略本质上是轮询 Google 页面 DOM，等待时间取决于 Google 服务器响应速度而非代码优化。阶段 3 需要等待文本"长度>200 且 1s 稳定"，Google 流式生成 AI 回答时这个等待无法缩短。
**违背契约**: PRD G1 ≤3s
**证据**: 实测 AI 等待 7.3s 占端到端 70%。这 7.3s 是 Google 生成 AI 回答的固有延迟，代码层面优化空间有限。
**概率**: 高 | **影响**: 如果无法接近 3s，整个 Skill 的"快"卖点崩溃

### 失败场景 2: Google DOM 漂移
**Root Cause**: Google 频繁 A/B 测试和地区化导致 AI Mode 页面 DOM 结构持续变化。17 个硬编码选择器随时间失效。
**违背契约**: PRD US-001 AC2（引用提取）
**证据**: 首次 E2E 测试 citations=0，选择器未匹配当前 DOM。
**概率**: 高 | **影响**: 引用提取持续不工作，输出缺少来源

### 失败场景 3: Camoufox 上游断裂
**Root Cause**: Camoufox 依赖 Firefox 特定版本 + Playwright patch 版本。任一上游 breaking change 导致整个 Skill 不可用。
**违背契约**: ADR-001 依赖链
**证据**: Camoufox v0.5.0 依赖 Firefox v135 特定 beta 版本，非标准发行版。
**概率**: 中 | **影响**: 用户无法使用 Skill 直到上游修复或本地降级

---

## 承诺闭合验证

| 项目 | 结论 | 证据 | 对应问题 |
|------|------|------|----------|
| **重复态** (缓存幂等) | ✅ Pass | LRUCache 命中直接返回，不重复搜索 | — |
| **失败态** (错误降级) | ⚠️ Partial | ErrorHandler 框架完整，但 30 处裸 except 使错误不可观测 | CH-06 |
| **默认态** (框架路径) | ✅ Pass | CLI 退出码完整，SearchEngine 缺省参数合理 | — |
| **运行态** (长运行) | ❌ Fail | 浏览器非真正持久化，每次 CLI 新建进程 | CH-05 |
| **并发态** | ✅ Pass | 单用户单查询设计，无并发需求 | — |
| **观测态** | ⚠️ Partial | --debug 模式有日志，但 Camoufox 噪声污染 stdout | CH-07 |

---

## 建议行动清单

### P0 - 立即处理
1. **[CH-01]** 优化 AI 检测超时策略：阶段 3 稳定性检查从 1s 缩减到 300ms，阶段 1 超时从 3s 缩减到 1s，总超时从 15s 缩减到 8s
2. **[CH-02]** Dump Google AI Mode 页面真实 DOM：用 `--save --debug` 保存 `page.content()` 到文件，人工比对 17 选择器

### P1 - 近期处理
3. **[CH-03]** 补充 pytest 测试：至少 `tests/test_cache.py`、`tests/test_converter.py`、`tests/test_dom_cleaner.py`
4. **[CH-05]** 文档说明跨 CLI 调用限制，规划守护进程模式

### P2 - 持续改进
5. **[CH-04]** 统一 AI 检测入口，废弃 BrowserContext.wait_for_ai()
6. **[CH-06]** 关键路径异常加 `logger.exception()` 记录堆栈
7. **[CH-07]** 重定向 Camoufox 日志到 stderr

---

## 🚦 最终判断

- [ ] 🟢 项目可继续，风险可控
- [x] 🟡 项目可继续，但需先解决 P0 问题
- [ ] 🔴 项目需要重新评估

**判断依据**: 管道已通，架构合理，但 CH-01（性能 3x 差距）和 CH-02（引用提取不工作）是两个核心功能承诺失实。修复这两项后项目进入可用状态，其余 Medium 问题可在迭代中解决。
