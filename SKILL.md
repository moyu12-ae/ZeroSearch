---
name: zerosearch
description: Use this skill whenever the user needs current information, documentation, coding examples, or web research beyond the knowledge cutoff. Queries Google's AI Search mode via Camoufox engine, or falls back to Chrome DevTools browser for direct official source access. Returns structured markdown with source citations. Ideal for you to get new information and clues for further research. Trigger when user mentions web research, current events, latest docs, API references, technical comparisons, "search for", "look up", or asks about anything post-2025.
---

# ZeroSearch

Two-tier web research skill. **Primary**: Chrome DevTools MCP browser navigation to official sources for real-time, verifiable information. **Secondary**: Camoufox Python engine for Google AI Mode search (when regional/browser conditions permit).

## When to Use This Skill

**Always trigger** when the user needs information you don't have or can't verify from training data alone:

- Current information beyond your knowledge cutoff
- Documentation or API references for libraries/frameworks (especially latest versions)
- Coding examples or implementation patterns you're unsure about
- Technical comparisons requiring real benchmark data
- Research requiring verifiable citations and sources
- Any question where "I think" isn't good enough — verify against live sources

## Two-Tier Research Strategy

### Tier 1: Chrome DevTools MCP Browser Research (Primary)

When Chrome DevTools MCP is available, use it to navigate directly to official sources. This is the fastest and most reliable approach — no dependencies, no CAPTCHA, no regional restrictions.

```
1. Identify the authoritative source (e.g. react.dev, nextjs.org, eur-lex.europa.eu)
2. Navigate to the page with Chrome DevTools MCP
3. Use evaluate_script to extract headings, code samples, key data
4. Take snapshot for full page content
5. Visit multiple sources to cross-verify claims
```

**Best for**: Official documentation, EU/regulatory texts, GitHub repos, any site with stable URLs.

### Tier 2: Camoufox Python Engine (Secondary)

The Python search pipeline uses Camoufox (Firefox v135+ with anti-fingerprinting) to query Google AI Mode (`udm=50`). Use this when you need Google's AI-synthesized overview from 100+ sources.

```bash
python src/search/run.py --query "your optimized query" --save --debug
```

**Available when**: Camoufox submodule is initialized, Google AI Mode is accessible from your region.

### Fallback Decision Tree

```
User needs web research
  │
  ├─ Chrome DevTools MCP available?
  │   └─ YES → Navigate official sources directly (Tier 1)
  │
  └─ Need Google AI synthesis?
      └─ Try `python src/search/run.py`
          ├─ Success → Use AI Overview + citations
          ├─ CAPTCHA → Tell user "Run with --show-browser to solve CAPTCHA"
          └─ AI Mode unavailable → Fall back to Tier 1 or WebFetch
```

## Chrome DevTools MCP Research Methodology

When using the browser for research, follow this rigorous approach:

1. **Identify authoritative sources first** — don't guess URLs, navigate to known official domains
2. **Extract data programmatically** — use `evaluate_script` to pull headings, code blocks, and structured data
3. **Cross-verify across sources** — visit at least 2 independent sources before presenting findings
4. **Preserve source URLs** — every claim must link to the exact page you visited
5. **Note what you couldn't verify** — be transparent about information gaps

### Example: Researching a new library feature

```javascript
// Use evaluate_script to extract structured content
() => {
  const article = document.querySelector('article, main');
  const headings = article.querySelectorAll('h1, h2, h3');
  const codeBlocks = article.querySelectorAll('pre code');
  return {
    title: document.title,
    url: location.href,
    headings: Array.from(headings).map(h => ({tag: h.tagName, text: h.textContent.trim()})),
    codeSamples: Array.from(codeBlocks).slice(0, 6).map(c => c.textContent.substring(0, 600))
  };
}
```

## CLI Flags (Python Engine)

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

## First-Time Setup (Python Engine)

The project uses a Camoufox git submodule. Clone with:

```bash
git clone --recurse-submodules <repo-url>
cd zerosearch
./setup.sh
```

Or after a normal clone:
```bash
git submodule update --init --recursive
./setup.sh
```

**Technical Requirements**: Python 3.8+, Camoufox v135+ (Firefox-based, auto-installed).

## CAPTCHA Handling

Camoufox's anti-fingerprinting + persistent browser context minimizes CAPTCHAs. If triggered:

- **Headless mode**: Script returns exit code 2 with CAPTCHA_REQUIRED message
- **Manual solve**: Re-run with `--show-browser`, solve CAPTCHA in the browser window
- **After first solve**: Persistent context preserves session, future searches skip CAPTCHA
- **If persistent**: Delete `~/.cache/zerosearch/camoufox_profile/` to reset

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
| Chrome DevTools MCP not connected | Run Tier 2 Python script instead, or use WebFetch |
| `libs/camoufox/` empty | `git submodule update --init --recursive` |
| Camoufox not found | `python -m camoufox install` |
| AI Mode not available | Your region doesn't support Google AI Mode. Use Tier 1 browser research or VPN to US/UK |
| Profile corrupted | Delete `~/.cache/zerosearch/camoufox_profile/` |
| CAPTCHA every search | Profile may be stale — delete and re-solve once with `--show-browser` |

**Exit Codes (Python Engine):**
- `0` — Success
- `1` — General error
- `2` — CAPTCHA required (use `--show-browser`)
- `3` — Browser closed by user
- `4` — AI Mode unavailable in region
- `130` — User interrupted

## Best Practices

1. **Prefer Tier 1 when MCP is available** — faster, more reliable, no CAPTCHA
2. **Optimize queries before search** — specificity = quality
3. **Cross-verify across sources** — never rely on a single page
4. **Preserve source URLs** — every claim must be traceable
5. **Be transparent about limitations** — note when information couldn't be verified
6. **Use `--debug` for performance issues** — reveals which stage is slow
7. **Clone with `--recurse-submodules`** — avoids missing Camoufox dependency
