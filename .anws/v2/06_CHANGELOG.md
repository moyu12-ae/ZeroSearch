# 变更日志 - .anws v2

> 此文件记录本版本迭代过程中的微调变更（由 /change 处理）。新增功能/任务需创建新版本（由 /genesis 处理）。

## 格式说明
- **[CHANGE]** 微调已有任务（由 /change 处理）
- **[FIX]** 修复问题
- **[REMOVE]** 移除内容

---

## 2026-05-20 - 初始化
- [ADD] 创建 `.anws` v2 版本
- [ADD] 底层引擎迁移：Camoufox → Patchright
- [CHANGE] PRD REQ-006: Profile 策略更新 — 默认复用真实 Chrome Profile，继承 Google 登录状态
- [CHANGE] ADR-001: 补充 Chrome Profile 复用正面影响
- [ADD] PRD REQ-008: 首次运行 Profile 选择 — 使用 AskUserQuestion 工具交互
- [ADD] PRD REQ-009: 工作区自动注册 — setup.sh 写入 CLAUDE.md 搜索策略

## 2026-05-20 — Challenge R1 修复

- [FIX] R1-C1: Architecture Overview 新增 System 0 (SKILL.md 技能入口与 AskUserQuestion 交互协议)
- [FIX] R1-H1: 统一 version constraint 为 `patchright>=1.55,<2` (PRD + ADR)
- [FIX] R1-H2: Architecture §2.1 列出两个 Profile 路径 (Option A/B) 并标注来源
- [FIX] R1-H3: PRD §6 删除"简化为 Patchright 方案"，明确 AI 检测逻辑不变
- [FIX] R1-H4: ADR + Architecture 定义 Chrome Profile 锁定处理协议 (exit code 5)
- [FIX] R1-M1: PRD §5 CAPTCHA 率分层定义 (Option A <1%, Option B <10%)
- [FIX] R1-M2: PRD REQ-009 明确 CLAUDE.md 检测逻辑 (grep ZeroSearch, 备份, 路径优先级)
- [FIX] R1-M3: Architecture §2.2 更新 CLI flags 完整列表 + 退出码表
- [FIX] R1-M4: PRD §7 增加 v0.1→v0.2 迁移步骤
- [FIX] R1-L1: PRD §8 增加 BrowserEngine 集成测试计划 (test_browser_factory.py)

## 2026-05-20 — Challenge R4 修复（层间一致性同步）

- [FIX] R4-C1: PRD/Architecture/ADR 同步至单 Profile 模式（移除 Option A/B 描述）
- [FIX] R4-H1: README "快速开始" 更新为单 AskUserQuestion 描述
- [FIX] R4-M1: PRD CAPTCHA 率统一（移除 Option A/B 分开定义）
