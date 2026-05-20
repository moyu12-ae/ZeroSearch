# ADR-001: 浏览器引擎选型 — Patchright + 真 Chrome

## 状态

Accepted

## 背景

ZeroSearch v0.1 使用 Camoufox (Firefox + Playwright wrapper) 作为浏览器引擎，遇到三大问题：

1. **CAPTCHA 频繁触发**：Google 检测到自动化标记（CDP 协议泄露）
2. **系统代理不继承**：Firefox 不读取 macOS 系统代理设置，需手动写 `detect_system_proxy()`
3. **维护成本高**：需 Git Submodule + `camoufox fetch`，安装流程 4 步

v0.2 需选型一个新的浏览器引擎，满足：CDP 级反检测、自动代理继承、pip 安装、冷启动 ≤5s。

## 决策

选择 **Patchright + 真 Chrome**（`channel="chrome"`）替代 Camoufox Firefox。

核心理由：
- Patchright 修复了 Playwright 的 CDP 协议泄露（Runtime.enable / Console.enable），这是 Google 检测自动化的主要手段
- 真 Chrome 自动继承 macOS 系统代理，消除 `detect_system_proxy()` 代码
- pip 安装，`pip install --upgrade patchright` 一键升级
- 原版 google-ai-mode-skill 已验证此方案可行

## 候选方案对比

| 候选 | 总分 | 反检测 | 代理 | 安装 | 性能 | 结论 |
|------|:------:|:--:|:--:|:--:|:--:|------|
| **A: Patchright + Chrome** | **227/240** | CDP 级 | 自动继承 | pip | ≤5s | ✅ 选定 |
| B: 纯 Playwright + Chromium | 168/240 | 无 | 自动继承 | pip | ≤5s | ❌ 反检测弱 |
| C: Camoufox + Firefox | 141/240 | 浏览器层 | 需手动 | submodule | ~8s | ❌ 多项不满足 |

### 关键维度对比

| 维度 | A (Patchright) | C (Camoufox) | 差异 |
|------|:--:|:--:|------|
| navigator.webdriver | false ✅ | false ✅ | 平手 |
| CDP Runtime.enable 泄露 | 已修复 ✅ | 未处理 ❌ | **A 胜** |
| CDP Console.enable 泄露 | 已修复 ✅ | 未处理 ❌ | **A 胜** |
| 通过 Cloudflare 检测 | ✅ | ⚠️ 未知 | **A 胜** |
| 代理继承 | Chromium 原生 ✅ | 需手动代码 ❌ | **A 胜** |
| 安装复杂度 | pip install ✅ | pip + submodule + fetch ❌ | **A 胜** |
| 冷启动速度 | ~3-5s ✅ | ~8s ❌ | **A 胜** |

## 权衡点

| 权衡 | 分析 |
|------|------|
| **Patchright 社区 < Playwright** | Patchright 3.2K stars vs Playwright 70K+。但它追踪 Playwright 上游，API 100% 兼容，降级成本低 |
| **真 Chrome 需系统安装** | `patchright install chrome` 自动管理 Chrome for Testing，开发者无感 |
| **CDP 补丁跟随上游** | 小版本升级 (patch) 不破坏 API。主版本需跑测试后升级。可锁定 `>=1.55,<2` |

## 后果

**正面**:
- 反检测能力显著提升（CDP 协议级 vs 浏览器指纹级）
- 系统代理零配置，降低 20+ 行检测代码
- 安装从 4 步减为 2 步（`setup.sh` 内 `pip install + patchright install chrome`）
- 冷启动从 ~8s 降到 ~3-5s
- 复用用户真实 Chrome Profile → 继承 Google 登录状态 → **CAPTCHA 几乎零触发**
- 保留现有 SearchEngine/ContentExtractor/MarkdownConverter 管线

**负面**:
- Patchright 社区小，遇到深度 bug 修复可能依赖上游 Playwright
- 真 Chrome 镜像下载 ~150MB，首次安装稍慢（仅一次）
- **Chrome Profile 锁定**: 若用户选择真实 Chrome Profile，且 Chrome 正在运行 → Patchright 启动失败（同一 Profile 不可被两个进程使用）。mitigation: 检测到锁定时返回 exit code 5 + 明确提示"请关闭 Chrome 后重试"

**需要的后续行动**:
- 更新 `requirements.txt`: `patchright>=1.55,<2`
- 重写 `setup.sh`: 移除 Camoufox submodule/fetch
- 重写 `src/browser/browser_factory.py`: Patchright API
- 移除 `src/browser/stealth.py` 中的 `detect_system_proxy()`
- Profile 目录迁移: `firefox_profile` → `chrome_profile`

## 影响范围

| 系统 | 影响 |
|------|------|
| **BrowserEngine** | 🔴 重大变更 — 完整重写 factory + stealth + profile |
| **SearchEngine** | 🟡 微调 — API 适配，其余不变 |
| **ContentExtractor** | 🟢 不变 |
| **MarkdownConverter** | 🟢 不变 |
| **setup.sh / requirements.txt** | 🔴 重写 — 移除 Camoufox 依赖 |
