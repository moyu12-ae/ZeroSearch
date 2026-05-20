---
name: zerosearch
description: Use this skill whenever the user needs current information, documentation, coding examples, or web research beyond the knowledge cutoff. Uses Patchright (undetected Chromium) to query Google AI Mode (udm=50) for AI-synthesized overviews with source citations. Returns compact, token-efficient Markdown designed for AI consumption. Trigger when user mentions web research, current events, latest docs, API references, technical comparisons, "search for", "look up", or asks about anything post-2025.
---

# ZeroSearch v0.2

Patchright-powered web research skill. Uses undetected Chromium (CDP-level anti-detection) to query Google AI Mode (`udm=50`) for AI-synthesized overviews with source citations.

## First Run: Default Search Tool

On first use, check if ZeroSearch is already registered as the default search tool:

```bash
grep -rq "ZeroSearch" ~/.claude/CLAUDE.md CLAUDE.md 2>/dev/null
```

If already registered → skip, proceed to search.

If NOT registered → use `AskUserQuestion` with 3 options:

```
AskUserQuestion:
  header: "默认搜索工具"
  question: "ZeroSearch 尚未设为默认搜索工具。希望注册到哪个层级？"
  options:
    用户级 (推荐): "写入 ~/.claude/CLAUDE.md，所有项目生效"
    项目级: "写入当前工作区 CLAUDE.md，仅本项目生效"
    不注册: "保持原样，手动通过 /zerosearch 触发"
```

- **用户级**: Append search strategy to `~/.claude/CLAUDE.md`
- **项目级**: Append search strategy to current workspace `CLAUDE.md`
- **不注册**: Do nothing, user triggers `/zerosearch` manually

## How It Works

ZeroSearch launches a visible Chromium window via Patchright for each search, navigates to Google AI Mode, extracts the AI-synthesized overview and citations, converts to compact Markdown, then shuts down.

```
Chrome (Patchright) → Google AI Mode (udm=50) → AI Extraction → Compact Markdown
```

The browser uses an independent Chrome profile at `~/.cache/zerosearch/chrome_profile/`, separate from your daily Chrome. On first search, the Chrome window opens — you can sign into Google once, and the profile remembers your session for future searches.

- **Note**: Chrome blocks DevTools remote debugging on its default profile directory (`~/Library/Application Support/Google/Chrome/`). An independent profile is required for Patchright automation.

## Usage

### Step 1: Run search

```bash
cd ~/.claude/skills/zerosearch
source .venv/bin/activate
python src/search/run.py --query "<optimized query>" --save
```

Add `--debug` for per-stage timing breakdown.

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

On first search, Google may ask you to verify you're human. The browser window stays open — solve the CAPTCHA in the window, then press Ctrl+C in terminal to continue extraction. The profile remembers the session — subsequent searches skip CAPTCHA.

Once signed into Google through the browser window, CAPTCHA rate drops near zero.

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
| 5 | Chrome Profile locked |
| 130 | User interrupted |

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Patchright not found | Re-run `bash setup.sh` |
| Chrome not installed | `source .venv/bin/activate && python -m patchright install chrome` |
| AI Mode unavailable | Use VPN to US/UK, or fall back to WebFetch |
| Profile corrupted | `rm -rf ~/.cache/zerosearch/chrome_profile/` |
| CAPTCHA every search | Sign into Google once in the browser window |
