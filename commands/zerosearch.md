---
name: zerosearch
description: 基于香农信息论的 Google AI Mode 搜索。输入任意查询，自动运用高信息量关键词策略优化搜索，返回 AI 综合回答 + 引用来源。
argument-hint: <搜索查询>
allowed-tools: Read, Bash, WebFetch, Skill
---

# /zerosearch — 香农搜索

你是 ZeroSearch 的统一搜索入口。

## How It Works

ZeroSearch 使用 **Chrome Daemon**（常驻浏览器进程）：

- **首次搜索 (~5s)**: 自动冷启动 Chrome 窗口 → 会话期间保持打开
- **后续搜索 (<1s)**: 复用已有 Chrome 实例，只创建新标签页并关闭
- **停止 Daemon**: `/zerosearch-stop` 或直接关闭 Chrome 窗口
- **Chrome 崩溃恢复**: 下次搜索自动检测并冷启动重建（幽灵连接恢复）
- 独立 Chrome Profile (`~/.cache/zerosearch/chrome_profile/`)，与日常 Chrome 隔离

收到用户的搜索查询后，执行以下流程：

## 首次运行检测

搜索前检查 `~/.cache/zerosearch/config.json` 是否存在：

- **不存在** → 首次运行。引导用户执行 `/zerosearch:zerosearch-config` 配置 Profile 和默认搜索工具
- **存在** → 继续正常搜索流程

## 执行步骤

### Step 1: 加载香农搜索策略

调用 `Skill` 工具加载 `shannon-strategy` 技能，获取香农信息论搜索指导。

### Step 2: 优化搜索查询

根据香农策略 Skill 的指导，将用户的自然语言查询转化为高信息量搜索查询：

1. **提取核心意图** — 用户真正想查什么？
2. **去除通用词** — 删除 "怎么""方法""优化""如何" 等低信息量词
3. **选择高信息量关键词** — 优先使用：专业术语、版本号、具体数字、独特表述
4. **组合独立维度词** — 3-5 个不同维度的词组合
5. **匹配目标语言** — 查日本内容用日语，查英文文档用英语，查中文内容用中文

### Step 3: 执行搜索

使用 Bash 工具执行 Python CLI：

```bash
python ${CLAUDE_PLUGIN_ROOT}/src/search/run.py --query "<优化后的查询>"
```

引擎自动处理：
- Chrome Daemon 检测与热连接（冷启动 ~5s，热搜索 <1s）
- Google AI Mode (udm=50) 导航
- AI 回答提取 + 引用
- Markdown 格式化输出
- LRU 缓存命中检测

### Step 4: 输出结果

以结构化 Markdown 格式返回给用户：
- AI 综合回答（正文）
- 引用来源（紧凑脚注）
- （建议）若用户可能想深入，推荐 1-2 个更高信息量的关键词供手动追问

### Step 5: 可选追问

搜索完成后，可建议：
> 如需更深入，可尝试搜索：`<更精准的高信息量关键词组合>`

由用户决定是否继续。

## 快捷触发

用户直接说 "搜索 xxx" 或 "查一下 xxx" 即可触发，无需显式输入 `/zerosearch`。
