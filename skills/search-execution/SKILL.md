---
name: search-execution
description: Google AI Mode 搜索执行引擎。调用 Chrome Daemon 完成搜索、内容提取、Markdown 转换。被 /zerosearch 命令调用。
allowed-tools: Bash
---

# 搜索执行引擎

你是 ZeroSearch 的搜索执行层。当你被调用时，搜索查询已经由 Shannon Strategy Skill 优化过（高信息量关键词 + 语言匹配）。

## Rate Limiting

Google AI Mode (`udm=50`) 内部调用多个 AI 推理后端，相比普通搜索有更严格的频率限制。

- **连续搜索间隔至少 3 秒** — 降低 CAPTCHA 触发风险
- **LRU 缓存**: 50 条缓存 + 5 分钟 TTL — 相同查询自动去重，不重复请求 Google
- 缓存命中时返回结果 <1ms，不创建浏览器标签页

## 执行流程

### 1. 检查 LRU 缓存

检查是否有相同查询的缓存结果（`scripts/cache.py` 或内存缓存）。命中则直接返回，不创建浏览器标签页。

### 2. 检测 Chrome Daemon 状态

检查 `~/.cache/zerosearch/daemon.json`：
- **状态文件存在 + PID 存活** → 热搜索路径（CDP 连接已有 Chrome）
- **状态文件不存在 或 PID 已死** → 冷启动路径（创建新 Chrome 进程）

### 3. 执行搜索

使用 Bash 工具运行 Python 引擎：

```bash
python "${CLAUDE_PLUGIN_ROOT}/src/search/run.py" --query "<香农优化后的查询>"
```

引擎内部流程：
```
BrowserEngine: CDP 连接 → 创建标签页 → 导航 Google AI Mode (udm=50)
ContentExtractor: 等待 AI 完成 → 提取回答 + 引用 → 90+ 模式去噪
MarkdownConverter: HTML→MD (3库Fallback) → 紧凑脚注格式化
```

### 4. 错误处理

按 6 级退出码处理：

| 退出码 | 含义 | 处理 |
|:--:|------|------|
| 0 | 成功 | 返回结构化结果 |
| 1 | 通用错误 | 报告错误信息，建议重试 |
| 2 | CAPTCHA 触发 | 提示用户手动验证后重试。**浏览器窗口保持打开**，用户在最前面可见的 Chrome 窗口中完成人机验证，然后在终端按 `Ctrl+C` 继续提取结果。验证通过后 Chrome Profile 记住登录状态，后续搜索几乎不再触发 CAPTCHA |
| 3 | 浏览器关闭 | 自动冷启动重建（幽灵连接恢复） |
| 4 | AI Mode 不可用 | 提示地区限制 |
| 5 | Chrome Profile 锁定 | 提示关闭其他 Chrome 窗口 |
| 130 | 用户中断 | 优雅退出 |

### 5. 返回结果

以结构化 Markdown 返回。**输出格式示例**：

```markdown
React 19 引入 Server Components 实现零打包体积渲染[1]，
以及 Server Actions 实现类型安全的客户端-服务端通信[2]。
流式 SSR 通过 partial prerendering 进一步优化首屏加载[3]。

---
## Sources
[1] React Server Components — https://react.dev/reference/rsc/server-components
[2] Server Actions — https://react.dev/reference/rsc/server-actions
[3] Partial Prerendering — https://nextjs.org/docs/app/building-your-application/rendering/partial-prerendering
```

返回内容包含：
- 搜索耗时（冷启动 ~5s / 热搜索 <1s / 缓存命中 <1ms）
- AI 综合回答正文（紧凑、token-efficient）
- 引用来源（紧凑脚注 [1], [2], ...）
- 缓存状态标识（如有）
