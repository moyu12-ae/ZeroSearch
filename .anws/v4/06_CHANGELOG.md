# 变更日志 - .anws v4

> 此文件记录本版本迭代过程中的变更。

---

## 2026-05-24 — v0.42: 反检测全面加固

### 反检测增强
- **[ADD]** Daemon 反检测配置补全：`ignore_default_args` + `locale/viewport/geolocation/headers`
- **[ADD]** BROWSER_ARGS 6→14：后台服务抑制、Keychain 绕过、IPC 抑制、disable-features 合并
- **[ADD]** StealthUtils.get_init_script()：9 类 JS API 覆盖 (plugins/permissions/hwConcurrency/WebGL/chrome.runtime/Canvas/AudioContext/deviceMemory/screen)
- **[ADD]** 视口随机化：每次 StealthConfig 实例化 1024-1920 × 768-1080
- **[ADD]** 搜索间 jitter：500-2000ms 随机间隔
- **[ADD]** init_script 注入到搜索流水线 (page.add_init_script)

### Bug 修复
- **[FIX]** CAPTCHA 等待循环：page.is_closed() 检测 + 自动重检 + 600s→60s
- **[FIX]** hwConcurrency 模块加载时固化 → 每次调用随机
- **[FIX]** navigator.plugins 创建后未赋值到 navigator 对象
- **[FIX]** Permissions 覆盖无存在性守卫
- **[FIX]** WebGL2RenderingContext 未覆盖
- **[FIX]** StealthUtils 在 search() 中作用域错误
- **[FIX]** 步骤编号重复 (Step 5×2)

### 测试 (97→126)
- **[ADD]** TestDaemonRunnerStealthParity (2 tests)
- **[ADD]** TestCaptchaWaitResilience (3 tests)
- **[ADD]** TestBrowserArgsCompleteness (6 tests)
- **[ADD]** TestViewportRandomization 重写 (3 tests)
- **[ADD]** TestFingerprintScriptInjection (11 tests)
- **[ADD]** TestSearchJitter (2 tests)
- **[ADD]** Bug 检测测试 (5 tests)
- **[ADD]** P0 覆盖测试: Canvas/AudioContext/deviceMemory/screen (4 tests)

### 文档
- **[ADD]** PRD NG7 修正、测试数 45→126、CAPTCHA 目标更新
- **[ADD]** Architecture 反检测层次表 (19 行)
- **[ADD]** 05_TASKS Sprint 4 (9 tasks)
- **[ADD]** 07_CHALLENGE_REPORT Round 5
- **[ADD]** README v0.42 更新

---

## 2026-05-23 — v0.4 初始发布
- [ADD] Claude Code Plugin 化：4 commands + 2 skills + hooks
- [ADD] 香农信息论提示词工程
- [ADD] 孤儿 Chrome 恢复（端口扫描 + 自动重连）
- [ADD] Challenge 审计 4 轮

## 2026-05-21 - 初始化
- [ADD] 创建 `.anws` v4 版本，目标 v0.4：Plugin 化 + 香农提示词工程
