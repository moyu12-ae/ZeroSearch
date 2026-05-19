# ADR-001: 浏览器引擎选型 — Camoufox

## 状态
**Accepted**

## 背景
google-ai-mode-skill 当前使用 Patchright (Playwright/Chromium 变体) 驱动浏览器查询 Google AI Mode。Patchright 存在以下问题：
- Chrome 冷启动慢（~2s），内存占用高
- 反检测依赖手动 stealth 配置（UA 伪装、自动化标记移除），效果不稳定
- Patchright 是 Playwright 的 niche fork，社区和上游维护不确定性高

需要选择一个浏览器引擎，满足 PRD [REQ-001] 的反检测能力和 [REQ-005] ≤3s 性能目标。

## 决策
**选择 Camoufox (daijro/camoufox)** 作为浏览器自动化引擎，通过 Git Submodule + pip 管理。

## 候选方案对比

| 维度 | 权重 | Camoufox | Patchright | Playwright 原生 |
|------|:--:|:--:|:--:|:--:|
| 反检测能力 | ★★★★★ | **5** — 原生 Firefox 反指纹 | 3 — 手动 stealth | 2 — 无任何反检测 |
| 性能 (≤3s) | ★★★★ | **4** — Firefox 轻量 + 预热 | 3 — Chrome 较重 | 3 — 无优化 |
| 上游维护 | ★★★ | **4** — 活跃开源 | 2 — niche fork | 5 — Microsoft 维护 |
| 集成能力 | ★★★ | **5** — Git Submodule | 2 — 无标准化管理 | 3 — pip install |
| API 兼容性 | ★★★★ | 4 — 兼容 Playwright API | 4 — Playwright fork | 5 — 官方标准 |
| 开发速度 | ★★★★ | 4 — API 熟悉，迁移快 | 4 — 无需学习 | 5 — 文档最全 |
| **加权总分** | | **51/60** | 36/60 | 43/60 |

## 权衡点

1. **Camoufox 社区 < Playwright**: Camoufox 社区较小，但项目需求简单（导航→提取），不需要复杂 API。Camoufox 的 Playwright 兼容 API 确保学习成本低。

2. **Firefox 冷启动速度 ≈ Chrome**: 通过 [REQ-002] 预热常驻策略，浏览器实例保持 alive，后续搜索免冷启动，差异可忽略。

3. **Submodule 增加 clone 复杂度**: 用户 clone 后需执行 `git submodule update --init`，但换来上游一键更新能力，性价比高。

4. **反检测是 killer feature**: Google 主动检测自动化工具，Patchright 的手动 stealth 随 Google 反自动化策略更新而失效更快。Camoufox 在浏览器内核层做反指纹，对抗能力更强。

## 后果

### 正面
- 反检测内建于浏览器层，CAPTCHA 率预期 < 5%
- Firefox 内存占用比 Chrome 低约 30%
- Git Submodule 管理，上游更新 `git submodule update --remote`
- Playwright 兼容 API，迁移成本可控

### 负面
- Firefox 引擎与 Chrome 在部分 CSS/JS 渲染存在差异，但 Google AI Mode 页面属简单 DOM，影响极小
- 首次 clone 需额外 `--recurse-submodules` 或手动 init
- Camoufox 上游 breaking change 需人工验证兼容性

### 后续行动
- 验证 Camoufox 对 Google AI Mode (`udm=50`) 页面的渲染兼容性
- 建立 Camoufox 版本兼容性测试（E2E 冒烟）
- 在 AGENTS.md 中记录 `git submodule update` 维护流程

---

## 影响范围
- **BrowserEngine** (直接依赖): 所有浏览器启动/导航/Profile 代码
- **SearchEngine** (间接): 通过 BrowserEngine 抽象层，无直接 API 变化
- **项目根**: 新增 `.gitmodules`、`libs/camoufox/` 目录
