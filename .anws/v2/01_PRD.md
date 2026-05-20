# ZeroSearch v0.2 — 产品需求文档 (PRD)

**创建日期**: 2026-05-20
**关联概念模型**: `.anws/v2/concept_model.json`

---

## 1. 产品目标

ZeroSearch v0.2 将底层浏览器引擎从 Camoufox (Firefox) 迁移到 Patchright (Chromium)，实现：
- **更快**：冷启动 ≤5s（v0.1 ~8s，原版 ~10s）
- **更隐蔽**：CDP 协议级反检测 + 真 Chrome + 默认有头模式
- **更易维护**：pip 安装替代 Git Submodule，一键升级
- **AI 原生输出**：精简 Markdown，去噪、省 token、结构化引用

---

## 2. 用户画像

| 角色 | 描述 |
|------|------|
| **AI Agent** (主用户) | Claude Code 等 AI 助手，通过 `/zerosearch` 触发搜索，消费结构化结果 |
| **开发者** (间接用户) | 安装、配置、升级 ZeroSearch 技能 |

---

## 3. User Stories

### [REQ-001] P0 — 浏览器冷启动与搜索

**As a** AI Agent, **I want** to trigger a search that launches a visible Chrome browser, navigates to Google AI Mode, extracts results, and closes the browser, **so that** I can get current web information without manual browser management.

**验收标准**：
- **Given** 用户通过 `/zerosearch` 或 CLI 传入查询字符串
- **When** 引擎执行搜索
- **Then** 弹出可见 Chrome 窗口，导航到 `https://www.google.com/search?q=<query>&udm=50`
- **And** 冷启动到导航完成总耗时 ≤5s
- **And** 搜索完成后浏览器窗口自动关闭，无残留进程

**错误场景**：
- 网络不通 → exit code 1，stderr 输出 `[ERROR] 网络连接失败`
- CAPTCHA 触发 → 窗口保持打开，stderr 提示用户手动验证，等待 Ctrl+C 后继续

**涉及系统**: BrowserEngine, SearchEngine

---

### [REQ-002] P0 — Patchright CDP 级反检测

**As a** AI Agent, **I want** the browser to use Patchright with CDP-level anti-detection patches, **so that** Google does not trigger CAPTCHA under normal conditions.

**验收标准**：
- **Given** 浏览器启动配置包含 Patchright 的 undetected 补丁
- **When** 导航到 Google
- **Then** `navigator.webdriver` 为 `false`
- **And** `Runtime.enable` CDP 命令不被 Google 检测
- **And** 正常搜索（美国 IP）下 CAPTCHA 触发率 <10%

**边界情况**：
- 即使 CAPTCHA 触发，可见窗口允许用户手动解决
- Profile 持久化确保一次解决后长期免验证

**涉及系统**: BrowserEngine

---

### [REQ-003] P0 — AI 原生精简输出

**As a** AI Agent, **I want** search results in compact, token-efficient Markdown with citations, **so that** I can consume the information without parsing noisy HTML or Google UI elements.

**验收标准**：
- **Given** Google AI Mode 返回完整 HTML 页面
- **When** ContentExtractor + MarkdownConverter 处理
- **Then** 输出仅包含 AI Overview 正文 + 编号脚注 ([1], [2]...)
- **And** 不包含 Google 导航栏、页脚、搜索框、侧边栏、CSS、JS 等噪音
- **And** 单个搜索结果 token 数 ≤ 原版 google-ai-mode-skill 的 80%

**边界情况**：
- AI Overview 无内容 → 输出 `[AI Mode 未返回结果]`
- 引用链接失效 → 保留链接文本，标记 `[链接不可用]`

**涉及系统**: ContentExtractor, MarkdownConverter

---

### [REQ-004] P1 — 系统代理自动继承

**As a** 开发者, **I want** the browser to automatically use macOS system proxy settings (Shadowrocket/ClashX), **so that** no manual proxy configuration is needed.

**验收标准**：
- **Given** macOS 系统代理已配置（如 Shadowrocket 127.0.0.1:1082）
- **When** 浏览器启动
- **Then** Chromium 自动通过系统代理访问 Google
- **And** 配置文件中不包含任何代理配置代码

**边界情况**：
- 系统代理未配置 → 直连，若不可达则报网络错误
- 代理节点切换 → 自动跟随系统代理

**涉及系统**: BrowserEngine

---

### [REQ-005] P1 — pip 安装与一键升级

**As a** 开发者, **I want** to install and upgrade ZeroSearch dependencies via pip, **so that** maintaining the skill is simple and reproducible.

**验收标准**：
- **Given** 项目 `requirements.txt` 包含 `patchright>=1.55,<2`
- **When** 执行 `setup.sh`
- **Then** `pip install -r requirements.txt` 安装 Patchright
- **And** `patchright install chrome` 安装 Chrome for Testing
- **And** 不再需要 `git submodule update` 或 `camoufox fetch`
- **And** `pip install --upgrade patchright` 可升级底层引擎

**边界情况**：
- Patchright API 小版本升级不破坏现有代码（API 兼容约束）
- Chrome 已安装 → 跳过下载

**涉及系统**: 项目基础设施

---

### [REQ-008] P0 — 首次运行交互式 Profile 选择（AskUserQuestion）

**As a** 开发者, **I want** to choose on first run whether to use my real Chrome profile or a fresh one, via Claude Code's native AskUserQuestion interface, **so that** I have control over privacy vs convenience with a polished UX.

**验收标准**：
- **Given** 首次使用 `/zerosearch` 或首次运行搜索
- **When** SKILL.md 检测到 Profile 配置文件不存在
- **Then** Claude 调用 `AskUserQuestion` 显示选项：
  - **Header**: "浏览器 Profile"
  - **A) 复用 Chrome Profile** (推荐) — 继承 Google 登录，CAPTCHA 几乎零触发
  - **B) 独立空白 Profile** — 与日常隔离，隐私安全
- **And** 用户选择后，结果写入 `~/.cache/zerosearch/profile_config.json`
- **And** 后续调用直接读取配置，不再询问
- **And** `/zerosearch --reconfigure` 可重新触发选择

**实现说明**：
- SKILL.md 中描述 Profile 选择流程
- Python CLI 接受 `--profile <path>` 参数（由 SKILL.md 传递）
- 不在 Python 代码中实现交互式选择

**选项说明**：

| 选项 | Profile 路径 | 优势 | 劣势 |
|------|-------------|------|------|
| **A: 复用 Chrome** | `~/Library/Application Support/Google/Chrome/` | 已登录 Google，CAPTCHA ≈ 0 | 需关闭正在运行的 Chrome |
| **B: 独立 Profile** | `~/.cache/zerosearch/chrome_profile/` | 与日常隔离 | 首次需手动登录/过 CAPTCHA |

**边界情况**：
- 选 A 但 Chrome 正在运行 → 提示"请先关闭 Chrome"并重试
- 选 A 但 Chrome 未安装 → 自动降级到 B
- 选 B → 首次搜索弹出 Chrome 窗口，用户可手动登录 Google

**涉及系统**: SKILL.md, BrowserEngine

---

### [REQ-009] P1 — 工作区自动注册为默认搜索工具

**As a** 开发者, **I want** setup.sh to automatically register ZeroSearch as the preferred search tool in the workspace's CLAUDE.md/AGENTS.md, **so that** the AI agent always uses ZeroSearch first for web research without manual configuration.

**验收标准**：
- **Given** 执行 `setup.sh`
- **When** 安装完成
- **Then** 检测当前工作区的 `CLAUDE.md`（项目级）或 `~/.claude/CLAUDE.md`（用户级）
- **And** 在文件中追加搜索策略区块：
  ```markdown
  ## 搜索策略
  
  - **首选搜索引擎**: ZeroSearch（触发 `/zerosearch` 或关键词：搜索、search、查一下、最新、文档）
  - 当需要网页信息、实时数据、最新文档、技术对比时，优先使用 ZeroSearch 的 Google AI Mode
  - ZeroSearch 配置目录: ~/.cache/zerosearch/
  ```
- **And** 如果 CLAUDE.md 已存在搜索策略，提示用户手动合并而非覆盖
- **And** 提供 `--no-register` flag 跳过注册

**CLAUDE.md 检测逻辑**：
1. 优先写项目级 `CLAUDE.md`（当前工作区根目录），若无则写 `~/.claude/CLAUDE.md`
2. 用 `grep -q "ZeroSearch" CLAUDE.md` 检测是否已注册
3. 如 CLAUDE.md 包含 `<!-- AUTO:BEGIN -->` 区块，搜索策略写入区块外（区块由 Anws 维护）
4. 追加内容在文件末尾，保留原有内容不变
5. 追加前先备份：`cp CLAUDE.md CLAUDE.md.bak`

**边界情况**：
- CLAUDE.md 不存在 → 创建文件并写入搜索策略
- 已有 ZeroSearch 注册 → 跳过，提示"搜索策略已存在，跳过注册"
- 权限不足 → 提示手动添加内容（打印待添加的 Markdown 文本）
- 备份失败 → 仍尝试写入（非阻塞）

**涉及系统**: setup.sh, 项目基础设施

---

### [REQ-006] P1 — Profile 持久化与 CAPTCHA 记忆

**As a** AI Agent, **I want** the browser profile (cookies, session) to persist across searches, **so that** once authenticated, subsequent searches skip verification.

**验收标准**：
- **Given** 用户已通过 REQ-008 选择了 Profile 模式
- **When** 每次搜索启动浏览器
- **Then** 使用相同的 Profile 目录（配置中记录的路径）
- **And** Google 登录状态/Cookie 跨搜索保持有效

**边界情况**：
- Profile 损坏 → 自动重建，重新触发 REQ-008 初始化选择
- 用户主动重置 → `rm -rf ~/.cache/zerosearch/`

---

### [REQ-007] P2 — 人类行为模拟

**As a** AI Agent, **I want** the browser to perform human-like delays and interactions, **so that** automated behavior patterns are further disguised.

**验收标准**：
- **Given** 引擎执行页面交互（可选，未来搜索流程优化）
- **When** 需要等待或输入
- **Then** 操作间有 100-500ms 随机延迟
- **And** 键盘输入模拟字符间延迟（25-75ms）

**边界情况**：
- 仅在非性能关键环节使用（如 CAPTCHA 后的额外等待）
- 默认不增加搜索延迟

**涉及系统**: BrowserEngine

---

## 4. Non-Goals（明确不做）

| # | 内容 | 原因 |
|---|------|------|
| 1 | 多标签页搜索 | 单标签足够，增加复杂度无收益 |
| 2 | 非 Google 搜索引擎 | Google AI Mode 是核心价值 |
| 3 | 持久化浏览器 daemon | 用户明确选择每次冷启动 |
| 4 | 视觉截图输出 | 文本 Markdown 对 AI 更高效 |
| 5 | 并发搜索 | 单用户单任务场景，无需并发 |
| 6 | Windows/Linux 支持 | 仅 macOS，用户环境 |
| 7 | headless 模式 | 用户明确要求始终有头 |

---

## 5. 非功能需求

| 类别 | 需求 | 度量 |
|------|------|:--:|
| 性能 | 冷启动到导航完成 | ≤5s |
| 性能 | 搜索全流程（启动→输出） | ≤15s |
| 性能 | 缓存命中 | <1ms |
| 可靠性 | CAPTCHA 触发率 — Option A (真实 Chrome, 已登录) | <1% |
| 可靠性 | CAPTCHA 触发率 — Option B (独立 Profile, 未登录) | <10% |
| 可靠性 | 崩溃恢复 | 下次搜索自动重建 Profile |
| 可维护性 | 底层升级命令 | `pip install --upgrade patchright` |
| 可维护性 | 安装命令数 | ≤3 步（clone → setup.sh 一条龙） |
| 安全 | 无外部网络依赖（除 Google + 系统代理） | 无 |
| Token 效率 | 单次搜索输出 | ≤原版 80% token |
| 兼容性 | Python 版本 | ≥3.10 |

---

## 6. 与 v0.1 的关系

| v0.1 保留 | v0.1 移除 |
|-----------|----------|
| SearchEngine 管线 | Camoufox submodule |
| ContentExtractor | `detect_system_proxy()` |
| MarkdownConverter | `camoufox fetch` 命令 |
| LRU 缓存 | Firefox UA 配置 |
| 错误处理框架 | BrowserFactory (Camoufox API) |
| CLI 入口 (cli.py/run.py) | — (全部保留) |
| 4 阶段 AI 完成检测 | — (逻辑不变，与浏览器引擎无关) |
| 17 选择器引用提取 | — (逻辑不变) |
| DOM 清洗 | — (逻辑不变，增加 AI 原生精简优化) |

---

## 7. v1 → v2 迁移指南

如果已有 v0.1 安装，升级步骤：

```bash
cd ~/.claude/skills/zerosearch
git pull origin main            # 拉取 v0.2 代码
rm -rf libs/camoufox            # 移除旧 Camoufox submodule
rm -rf .venv                    # 清理旧 venv
bash setup.sh                   # 重新安装（pip + patchright + Chrome）
rm -rf ~/.cache/zerosearch/firefox_profile  # 可选：清理旧 Firefox Profile
```

首次运行 `/zerosearch` 时触发 REQ-008 Profile 选择（AskUserQuestion）。

---

## 8. 验收测试清单

### 单元测试

- [ ] 现有 17 个 pytest 全部通过（Cache + DOM Cleaner + Footnote）
- [ ] 新增 `test_browser_factory.py`:
  - [ ] Patchright 导入成功
  - [ ] BrowserFactory 创建 context
  - [ ] Profile 路径选择逻辑（Option A/B）

### 集成测试

- [ ] `setup.sh` 执行成功，仅需 `pip install + patchright install chrome`
- [ ] `python src/search/run.py --query "test"` 弹出 Chrome 窗口并返回 Markdown
- [ ] `python -c "from patchright.sync_api import sync_playwright; p = sync_playwright().start(); p.chromium.launch(channel='chrome', headless=False); p.stop()"` 验证 Chrome 可启动
- [ ] macOS 系统代理自动生效（不需配置）
- [ ] `navigator.webdriver === false`（Patchright 反检测生效）

### E2E 测试

- [ ] Profile 目录在首次搜索后创建
- [ ] 冷启动到导航完成 ≤5s
- [ ] 输出不包含 Google UI 元素（导航栏/页脚/搜索框）
- [ ] CAPTCHA 触发时浏览器窗口保持打开，等待用户操作
- [ ] Google AI Mode 正常返回结果 + 引用
