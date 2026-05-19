---
name: zerosearch
description: Use this skill when the user requests current information, documentation, coding examples, or web research beyond the knowledge cutoff. Queries Google's AI Search mode to retrieve comprehensive AI-generated overviews with source citations from 100+ websites. Returns markdown with inline footnoted references [1][2][3]. You will receive a detailed Markdown file with references and information summarized directly from Google's AI search. Ideal for you to get new information and clues for further research.
---

# ZeroSearch

Query Google's AI Search mode to retrieve comprehensive, source-grounded answers from across the web. Powered by Camoufox (Firefox-based) with anti-fingerprinting for stealth browsing.

## When to Use This Skill

Trigger this skill when the user:
- Requests current information beyond the knowledge cutoff (post-January 2025)
- Needs documentation or API references for libraries and frameworks
- Asks for coding examples or implementation patterns
- Wants technical comparisons or best practices
- Requires research with citations and sources
- Mentions "Google AI search", "Google AI mode", or "web research"

## How It Works

1. **Camoufox Firefox Engine**: Uses Camoufox (Firefox v135+) with built-in anti-fingerprinting -- evades Google's bot detection far more reliably than Chromium-based alternatives
2. **Warm-Keep Persistent Context**: Reuses `BrowserContext` across searches at `~/.cache/zerosearch/camoufox_profile`, preserving cookies and session state to avoid repeated CAPTCHAs
3. **LRU In-Memory Cache**: Query results cached with TTL of 5 minutes. Repeated queries return instantly from memory -- no browser launch, no network round-trip
4. **AI Content Detection**: Waits for Google AI Overview to render on page
5. **Citation Extraction**: Injects JavaScript to extract source links from the AI response
6. **Markdown Conversion**: Converts HTML to markdown with inline citations [1][2][3]
7. **Performance Target**: End-to-end search completes in <=3 seconds (cached) or ~5-7 seconds (cold)

## CLI Flags

### Essential Flags

**`--query`** (required)
```bash
python src/search/run.py --query "Your search query"
```

**`--debug`** - Enable performance logging
```bash
python src/search/run.py --query "..." --debug
```
- Logs timing breakdown: browser launch, page load, AI content wait, citation extraction
- Essential for diagnosing slow searches or engine issues

**`--save`** - Save results to results/ folder
```bash
python src/search/run.py --query "..." --save
```
- Saves markdown to `results/YYYY-MM-DD_HH-MM-SS_Query_Name.md`
- Timestamped filename for organized storage

**Combined usage** (recommended for debugging):
```bash
python src/search/run.py --query "..." --save --debug
```

### Other Flags

**`--show-browser`** - Show browser window (for CAPTCHA solving)
```bash
python src/search/run.py --query "..." --show-browser
```

## Query Optimization Strategy

**CRITICAL**: Always optimize user queries before execution. Google AI Mode's quality depends on query precision.

### Optimization Template

```
[Technology/Topic] [Version] [Year] ([Specific Aspect 1], [Aspect 2], [Aspect 3]). [Output format request].
```

### Optimization Rules

1. **Include Current Year (2026)** for up-to-date results
2. **Use parentheses** to list specific aspects needed
3. **Request structured output** (tables, comparisons, categorized lists)
4. **Include version numbers** for library/framework queries

### Examples

| User Query | Optimized Query |
|-----------|----------------|
| "React hooks" | "React hooks best practices 2026 (useState, useEffect, custom hooks, common pitfalls). Provide code examples." |
| "What's new in Rust?" | "Rust 1.75 new features 2026 (async traits, impl Trait improvements, const generics, stabilized APIs). Include migration guide and code examples." |
| "PostgreSQL vs MySQL performance?" | "PostgreSQL vs MySQL performance comparison 2026 (query optimization, indexing strategies, concurrent writes, JSON handling, scaling patterns). Provide benchmark data and use case recommendations." |
| "How to handle errors in Go?" | "Go error handling patterns 2026 (error wrapping, custom errors, sentinel errors, panic vs error, testing error cases). Provide code examples and best practices comparison." |
| "Learn FastAPI basics" | "FastAPI tutorial 2026 (routing, dependency injection, async endpoints, request validation with Pydantic, OpenAPI documentation, testing). Include step-by-step implementation guide." |

**Note:** If user provides an already detailed query with version numbers and requirements, use it as-is.

### Workflow

1. Receive user request
2. Optimize query using template above
3. Inform user: "Searching for: '[optimized query]'"
4. Execute search with `--save --debug` flags
5. Return results with inline citations [1][2][3]

## Script Execution

The `run.py` wrapper automatically:
- Creates `.venv` on first run
- Initializes Camoufox git submodule (`git submodule update --init --recursive`)
- Installs `camoufox>=0.5.0`, `beautifulsoup4`, `markdownify`, and other dependencies
- Installs Camoufox Firefox browser (`python -m camoufox install`)
- Executes the search script with all forwarded arguments

### Basic Search

```bash
python src/search/run.py --query "Your search query"
```

### Recommended Usage

```bash
python src/search/run.py --query "..." --save --debug
```

### First-Time Setup

The project uses a Camoufox git submodule. Clone with:

```bash
git clone --recurse-submodules <repo-url>
```

Or after a normal clone, run:

```bash
./setup.sh
```

### Technical Requirements

- **Python**: 3.8+
- **Browser Engine**: Camoufox v135+ (Firefox-based, installed automatically by `run.py`)
- **Anti-Fingerprinting**: Built into Camoufox -- no separate stealth plugin needed

## CAPTCHA Handling

Camoufox's anti-fingerprinting combined with persistent browser context makes CAPTCHAs extremely rare.

1. **Detection**: Multi-layer check (URL `/sorry/index`, page text, content length)
2. **Automatic Handling**: If CAPTCHA detected in headless mode, script returns `CAPTCHA_REQUIRED` error
3. **Manual Solution**: Re-run with `--show-browser` flag, solve CAPTCHA in browser, script continues automatically

**Note**: After CAPTCHA is solved once, persistent context preserves the session -- future searches won't require CAPTCHA.

## Output Format

Returns markdown with inline citations and source list. Example:

```markdown
React 18 introduces concurrent features including Suspense for data fetching[1],
automatic batching for state updates[2], and transitions for non-urgent updates[3].

---

## Sources:

[1] React 18 Release Notes
https://react.dev/blog/2022/03/29/react-v18

[2] Automatic Batching Explained
https://github.com/reactwg/react-18/discussions/21

[3] Transitions API Documentation
https://react.dev/reference/react/useTransition
```

## Common Use Cases

### Finding Library Documentation
```bash
python src/search/run.py --query "Prisma ORM 2026 (schema definition, migrations, client API, relation queries, transactions). Include TypeScript examples." --save --debug
```

### Getting Coding Examples
```bash
python src/search/run.py --query "WebSocket implementation Node.js 2026 (server setup, client connection, message handling, authentication, reconnection logic). Production-ready code examples." --save
```

### Technical Comparisons
```bash
python src/search/run.py --query "GraphQL vs REST API 2026 (performance, caching, tooling, type safety, learning curve). Comparison table with use case recommendations." --save
```

### Best Practices Research
```bash
python src/search/run.py --query "Microservices security patterns 2026 (API gateway authentication, service mesh, mutual TLS, secret management, observability). Architecture diagrams and implementation guide." --save --debug
```

## Troubleshooting

| Issue | Solution |
|-------|----------|
| `ModuleNotFoundError: No module named 'camoufox'` | Use `run.py` wrapper -- never execute scripts directly. The wrapper auto-installs dependencies. |
| Camoufox initialization failed | Run `python -m camoufox install` manually to install the Firefox browser binary |
| `libs/camoufox/README.md` not found | Submodule not initialized: run `git submodule update --init --recursive` |
| Profile directory corrupted | Delete `~/.cache/zerosearch/camoufox_profile/` and re-run -- a fresh profile will be created |
| CAPTCHA every time | Profile may be corrupted or cookie jar stale. Delete profile (see above) and solve CAPTCHA once with `--show-browser` |
| No AI overview found | Rephrase query with more specificity using the optimization template above |
| Browser fails to start | Verify internet connection and that Camoufox browser is installed (`python -m camoufox install`) |
| Need performance details | Use `--debug` flag for timing breakdown of each search phase |
| AI Mode not available | Your region/country doesn't support Google AI Mode. Use a proxy/VPN to access from supported regions (US, UK, Germany, etc.) |

**Exit Codes:**
- `0` - Success
- `1` - General error
- `2` - CAPTCHA required (retry with `--show-browser`)
- `3` - Browser closed by user
- `4` - AI Mode not available in region (use proxy/VPN)
- `130` - User interrupted (Ctrl+C)

## Best Practices

1. **Always optimize queries** - Specificity determines result quality
2. **Use `--save --debug` for important searches** - Preserves results and provides performance audit
3. **Include version numbers** for library/framework queries
4. **Request structured output** - Tables and comparisons improve usability
5. **Solve CAPTCHA once** - Persistent Camoufox context eliminates future CAPTCHAs
6. **Verify citations** - Check provided sources for accuracy
7. **Clone with `--recurse-submodules`** - Avoids missing Camoufox engine dependency
