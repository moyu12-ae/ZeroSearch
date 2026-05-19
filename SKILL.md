---
name: zerosearch
description: Use this skill whenever the user needs current information, documentation, coding examples, or web research beyond the knowledge cutoff. Uses Camoufox (Firefox anti-fingerprinting browser) to query Google AI Mode (udm=50) for AI-synthesized overviews from 100+ sources with citations. Returns structured markdown with source citations. Trigger when user mentions web research, current events, latest docs, API references, technical comparisons, "search for", "look up", or asks about anything post-2025.
---

# ZeroSearch

Camoufox-powered web research skill. Uses Firefox anti-fingerprinting browser to query Google AI Mode (`udm=50`) for AI-synthesized overviews with source citations.

## When to Use This Skill

**Always trigger** when the user needs information you don't have or can't verify from training data alone:

- Current information beyond your knowledge cutoff
- Documentation or API references for libraries/frameworks (especially latest versions)
- Coding examples or implementation patterns you're unsure about
- Technical comparisons requiring real benchmark data
- Research requiring verifiable citations and sources
- Any question where "I think" isn't good enough — verify against live sources

## How It Works

ZeroSearch launches Camoufox (Firefox v135+ with anti-fingerprinting) for each search, navigates to Google AI Mode (`udm=50`), extracts the AI-synthesized overview and source citations, converts to structured markdown, then shuts down the browser.

```
Camoufox Firefox → Google AI Mode (udm=50) → AI Content Extraction → Markdown + Footnotes
```

For research that doesn't need Google's AI synthesis (official docs, GitHub repos, regulatory texts), prefer **WebFetch** or direct navigation to authoritative sources.

## CLI Usage

```bash
python src/search/run.py --query "your optimized query" --save --debug
```

| Flag | Required | Description |
|------|:--:|------|
| `--query`, `-q` | Yes | Search query string |
| `--save` | No | Save results to `results/` directory |
| `--debug` | No | Print per-stage timing breakdown |
| `--show-browser` | No | Show browser window for manual CAPTCHA solving |

```bash
python src/search/run.py --query "React hooks 2026" --save --debug
python src/search/run.py --query "some query" --show-browser  # For CAPTCHA solving
```

## Query Optimization

Always optimize queries before executing search. Specificity determines result quality.

**Template**: `[Technology/Topic] [Version] [Year] ([Aspect 1], [Aspect 2], [Aspect 3]). [Output format request].`

| User Query | Optimized Query |
|-----------|----------------|
| "React hooks" | "React hooks best practices 2026 (useState, useEffect, custom hooks, common pitfalls). Provide code examples." |
| "Bun vs Node speed" | "Bun vs Node.js performance comparison 2026 (cold start time, HTTP throughput req/s, memory usage). Provide benchmark data and sources." |
| "EU AI rules" | "EU AI Act requirements 2026 for SaaS startups (risk classification, compliance steps, penalties). Include official EU sources." |

## First-Time Setup

The project uses a Camoufox git submodule. Clone with:

```bash
git clone --recurse-submodules https://github.com/moyu12-ae/ZeroSearch.git ~/.claude/skills/zerosearch
cd ~/.claude/skills/zerosearch
./setup.sh
```

Or after a normal clone:
```bash
git submodule update --init --recursive
./setup.sh
```

**Technical Requirements**: Python 3.8+, Camoufox v135+ (Firefox-based, auto-installed via `python -m camoufox fetch`).

## CAPTCHA Handling

Camoufox's anti-fingerprinting + persistent browser Profile minimizes CAPTCHAs. If triggered:

- **Headless mode**: Script returns exit code 2 with CAPTCHA_REQUIRED message
- **Manual solve**: Re-run with `--show-browser`, solve CAPTCHA in the browser window
- **After first solve**: Persistent Profile preserves session, future searches skip CAPTCHA
- **If persistent**: Delete `~/.cache/zerosearch/firefox_profile/` to reset

## Output Format

Structured markdown with inline citations:

```markdown
React 19 introduces Server Components for zero-bundle-size server rendering[1],
and Server Actions for type-safe client-server communication[2].

---

## Sources:

[1] React Server Components Documentation
https://react.dev/reference/rsc/server-components

[2] Server Actions and Mutations
https://react.dev/reference/rsc/server-actions
```

## Troubleshooting

| Issue | Solution |
|-------|----------|
| `libs/camoufox/` empty | `git submodule update --init --recursive` |
| Camoufox not found | `python -m camoufox fetch` |
| AI Mode not available | Your region doesn't support Google AI Mode. Use VPN to US/UK, or fall back to WebFetch for direct source access |
| Profile corrupted | Delete `~/.cache/zerosearch/firefox_profile/` |
| CAPTCHA every search | Profile may be stale — delete and re-solve once with `--show-browser` |

**Exit Codes:**
- `0` — Success
- `1` — General error
- `2` — CAPTCHA required (use `--show-browser`)
- `3` — Browser closed by user
- `4` — AI Mode unavailable in region
- `130` — User interrupted

## Best Practices

1. **Optimize queries before search** — specificity = quality
2. **Cross-verify across sources** — never rely on a single page
3. **Preserve source URLs** — every claim must be traceable
4. **Be transparent about limitations** — note when information couldn't be verified
5. **Use `--debug` for performance issues** — reveals which stage is slow
6. **Clone with `--recurse-submodules`** — avoids missing Camoufox dependency
7. **Fall back to WebFetch** — when Google AI Mode is unavailable, navigate directly to official docs
