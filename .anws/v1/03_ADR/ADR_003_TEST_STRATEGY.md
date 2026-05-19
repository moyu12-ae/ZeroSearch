# ADR-003: 测试策略

## 状态
**Accepted**

## 背景
原项目无自动化测试。本次重构涉及底层引擎替换和性能优化，需要建立测试体系确保质量。

## 决策
采用 **E2E 集成测试为主 + 单元测试为辅** 的策略，无 CI 门禁（本地 Skill 场景不适合 CI）。

## 测试分层

| 层级 | 覆盖范围 | 工具 | 频率 |
|------|---------|------|------|
| **E2E 冒烟** | 真实 Google 搜索 → Markdown 输出 | `--debug` 日志 + 手动验证 | 每次 Camoufox 更新 |
| **集成测试** | BrowserEngine 启动/导航、ContentExtractor 提取 | pytest + mock Page | 每次代码提交 |
| **单元测试** | MarkdownConverter、CacheManager、CitationExtractor | pytest | 每次代码提交 |

## 权衡点
- **不做真实 Google E2E 自动化** — Google 搜索易触发 CAPTCHA，自动化 E2E 不稳定。改为手动冒烟 + `--debug` 日志验证。
- **集成测试用 mock Page** — 不依赖真实浏览器，快速验证提取逻辑。

## 测试门禁
- **无 CI**: 本地 Skill，不需要 GitHub Actions
- **Pre-commit**: 单元测试 + 集成测试通过后提交
- **Pre-submodule-update**: Camoufox 更新后跑 E2E 冒烟

## 后果
### 正面
- 核心逻辑（转换、缓存、提取）有 pytest 覆盖
- 引擎变更时有自动化回归测试

### 负面
- 无自动化 E2E — 依赖开发者手动验证
- 测试覆盖率预计 > 70%（BrowserEngine 难测拉低总覆盖率，其余模块目标 > 80%）

### 后续行动
- 在 `src/` 各子目录添加 `tests/` 目录
- setup.sh 添加 `pytest` 到依赖
- README 记录测试运行方法

## 影响范围
- **所有系统**: 各自 `tests/` 目录
- **项目根**: `pytest.ini` 或 `pyproject.toml`
