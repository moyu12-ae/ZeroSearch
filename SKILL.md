---
name: zerosearch
description: Use this skill whenever the user needs current information, documentation, coding examples, or web research beyond the knowledge cutoff. Uses Patchright (undetected Chromium) to query Google AI Mode (udm=50) for AI-synthesized overviews with source citations. Returns compact, token-efficient Markdown designed for AI consumption. Trigger when user mentions web research, current events, latest docs, API references, technical comparisons, "search for", "look up", or asks about anything post-2025.
---

# ZeroSearch v0.2

Patchright-powered web research skill. Uses undetected Chromium (CDP-level anti-detection) to query Google AI Mode (`udm=50`) for AI-synthesized overviews with source citations.

## First Run: Profile Setup

On first use, ZeroSearch checks if `~/.cache/zerosearch/profile_config.json` exists. If not, run two `AskUserQuestion` dialogs:

### Question 1: Profile Mode

```
AskUserQuestion:
  header: "浏览器 Profile"
  question: "选择浏览器 Profile 模式"
  options:
    A (推荐): "复用 Chrome Profile — 继承 Google 登录，CAPTCHA 几乎零触发（如 Chrome 正在运行会自动关闭）"
    B: "独立空白 Profile — 与日常隔离，隐私安全"
```

- **Option A**: Save `{"profile": "chrome"}` to `~/.cache/zerosearch/profile_config.json`
  - 启动前自动关闭正在运行的 Chrome（通过 `osascript -e 'quit app "Google Chrome"'`）
- **Option B**: Save `{"profile": "fresh"}` to `~/.cache/zerosearch/profile_config.json`

### Question 2: Default Search Tool

```
AskUserQuestion:
  header: "默认搜索"
  question: "是否将 ZeroSearch 设为默认搜索工具？"
  options:
    Yes: "写入 CLAUDE.md/AGENTS.md 搜索策略，AI 优先使用 ZeroSearch"
    No: "不修改配置，手动触发搜索"
```

- **Yes**: 在 CLAUDE.md 中注册 ZeroSearch 搜索策略（同 setup.sh REQ-009 逻辑）
- **No**: 跳过注册

Use `--reconfigure` to re-trigger both choices at any time.

## How It Works

ZeroSearch launches a visible Chromium window via Patchright for each search, navigates to Google AI Mode, extracts the AI-synthesized overview and citations, converts to compact Markdown, then shuts down.

```
AskUserQuestion (first run) → Chrome + Patchright → Google AI Mode (udm=50) → Extraction → Compact Markdown
```

## Usage

### Step 1: Read profile config

```bash
cat ~/.cache/zerosearch/profile_config.json 2>/dev/null || echo "not found"
```

If "not found" → trigger AskUserQuestion flow above. Profile path mapping:

| Config value | Path |
|-------------|------|
| `{"profile": "chrome"}` | `~/Library/Application Support/Google/Chrome/` |
| `{"profile": "fresh"}` | `~/.cache/zerosearch/chrome_profile/` |

### Step 2: Run search

```bash
cd ~/.claude/skills/zerosearch
source .venv/bin/activate
python src/search/run.py --query "<optimized query>" --profile <profile_path> --save
```

Add `--debug` for per-stage timing breakdown.

Add `--reconfigure` to re-trigger Profile setup.

### Profile Locking

If using real Chrome Profile and Chrome is already running → Patchright fails with exit code 5. Tell the user: "Chrome 正在运行，请先关闭 Chrome 再重试。" Suggest switching to Option B with `--fresh-profile`.

## Query Optimization

Always optimize queries before executing. Specificity determines result quality.

**Template**: `[Topic] [Key aspects]. [Output preference].`

| User Query | Optimized Query |
|-----------|----------------|
| "React hooks" | "React hooks best practices 2026 (useState, useEffect, custom hooks). Code examples." |
| "Bun vs Node" | "Bun vs Node.js performance 2026 (cold start, throughput, memory). With benchmarks." |

## First-Time Setup

```bash
git clone https://github.com/moyu12-ae/ZeroSearch.git ~/.claude/skills/zerosearch
cd ~/.claude/skills/zerosearch
bash setup.sh
```

**Requirements**: Python ≥3.10, macOS (Chrome auto-inherits system proxy).

## CAPTCHA Handling

With real Chrome Profile (Option A) + Google login → CAPTCHA rate <1%.

If CAPTCHA appears:
- Browser window stays open → manually solve in the window
- After solving, press Ctrl+C in terminal to continue extraction
- Profile remembers the session, subsequent searches skip CAPTCHA

## Output Format

Compact, token-efficient Markdown with inline citations:

```markdown
React 19 introduces Server Components for zero-bundle-size rendering[1],
and Server Actions for type-safe client-server communication[2].

---
## Sources
[1] React Server Components — https://react.dev/reference/rsc/server-components
[2] Server Actions — https://react.dev/reference/rsc/server-actions
```

## Exit Codes

| Code | Meaning |
|:----:|---------|
| 0 | Success |
| 1 | General error |
| 2 | CAPTCHA triggered |
| 3 | Browser closed |
| 4 | AI Mode unavailable |
| 5 | Chrome Profile locked (close Chrome first) |
| 130 | User interrupted |

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Patchright not found | Re-run `bash setup.sh` |
| Chrome not installed | `source .venv/bin/activate && python -m patchright install chrome` |
| AI Mode unavailable | Use VPN to US/UK, or fall back to WebFetch |
| Chrome Profile locked | Close all Chrome windows and retry; or use `--fresh-profile` |
| Profile corrupted | `rm -rf ~/.cache/zerosearch/chrome_profile/` |
| CAPTCHA every search | Switch to Option A (real Chrome Profile) via `--reconfigure` |
