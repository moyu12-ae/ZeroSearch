# ZeroSearch - Zero-Cost Web Search for Trae

<div align="center">

### Zero-Token Web Research with Real Chrome

Transform your Trae agent into a research powerhouse with ZeroSearch—zero token overhead, real Chrome browsing, and clickable citations.

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![GitHub Workflow Status](https://img.shields.io/github/actions/workflow/status/moyu12-ae/ZeroSearch/ci.svg)](https://github.com/moyu12-ae/ZeroSearch/actions)
[![Version](https://img.shields.io/badge/Version-6.4.0-blue.svg)](https://github.com/moyu12-ae/ZeroSearch/releases)
[![GitHub stars](https://img.shields.io/github/stars/moyu12-ae/ZeroSearch.svg)](https://github.com/moyu12-ae/ZeroSearch/stargazers)
[![GitHub forks](https://img.shields.io/github/forks/moyu12-ae/ZeroSearch.svg)](https://github.com/moyu12-ae/ZeroSearch/network)
[![中文版](https://img.shields.io/badge/中文版-点击切换-red.svg)](README.md)

**For: Trae IDE users on macOS, Linux, or Windows (WSL)**

</div>

---

## Why ZeroSearch?

Most built-in web research consumes too many tokens. ZeroSearch gives Trae **professional-grade research** by connecting to your real Chrome browser—zero token overhead, no CAPTCHA, and full login session reuse.

### Example Results

```
"Next.js 15 App Router best practices 2026"
→ [Next.js Documentation](https://nextjs.org) - Comprehensive guide with server components
→ [Vercel Blog](https://vercel.com/blog) - Production deployment patterns

"Compare PostgreSQL vs MySQL JSON performance 2026"
→ [PostgreSQL Wiki](https://wiki.postgresql.org) - JSONB benchmarks
→ [MySQL Blog](https://dev.mysql.com/blog) - JSON functions comparison

"EU AI regulations 2026 impact on startups"
→ [European Commission](https://commission.europa.eu) - Official documentation
→ [TechCrunch](https://techcrunch.com) - Industry analysis
```

**Result:** Research on **ANY topic**—coding, tech comparisons, legal, products, health, finance. Cited answers. Token-efficient.

---

## Features

| Feature | Description |
|---------|-------------|
| **Zero Token Overhead** | Uses real Chrome with CDP, minimal token consumption |
| **No CAPTCHA** | Uses your existing Google login |
| **Clickable Citations** | Every claim linked to source with `[Context](URL)` format |
| **Multi-Language** | Auto-detects EN/DE/ZH/ES/FR/IT/NL browser locale |
| **Session Persistence** | Persistent browser profile reduces CAPTCHAs |
| **Error Recovery** | Automatic retry with exponential backoff |

---

## Installation

### Prerequisites

- macOS, Linux, or Windows with WSL
- Python 3.8+
- Git

### Quick Install

```bash
# Clone the repository
git clone <repository-url>
cd ZeroSearch

# Run setup script (installs agent-browser CLI and dependencies)
./setup.sh
```

The setup script automatically:
- Installs `agent-browser` CLI (Vercel's AI-native browser automation)
- Creates Python virtual environment
- Installs dependencies (beautifulsoup4)
- Sets up persistent browser profile

### Manual Install

```bash
# Install agent-browser CLI
npm install -g agent-browser
agent-browser install

# Install Python dependencies
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

---

## Quick Start

### Python API

```python
from scripts import SearchEngine

# Initialize search engine
engine = SearchEngine(profile="research")

# Perform search
result = engine.search("Your search query")

# Get Markdown output with citations
print(result.markdown_output)
```

### Output Example

```markdown
## Next.js 15 App Router Best Practices 2026

Next.js 15 introduces improved Server Components and streaming patterns. Key improvements include:

- **Server Actions** now support [optimistic updates](https://nextjs.org/docs/app/building-your-application/data-fetching/forms-and-mutations) for better UX
- **Streaming** enables [progressive rendering](https://react.dev/reference/react Suspense) with Suspense boundaries
- **Caching** has been [redesigned](https://nextjs.org/docs/app/building-your-application/caching) with fetch-level controls

**Sources:**

- [Next.js Documentation](https://nextjs.org)
- [React Documentation](https://react.dev)
- [Vercel Blog](https://vercel.com/blog)
```

---

## Real Chrome Connection (Recommended)

Connect to your real Chrome browser to use your existing Google login, avoiding CAPTCHA:

```python
from scripts import SearchEngine

# Use saved authentication state (fastest)
engine = SearchEngine(state_path="~/.agent-browser/states/google.json")

# Or connect via CDP port
engine = SearchEngine(cdp_port=9222)

# Search without CAPTCHA
result = engine.search("EVA 终 日本评价")
print(result.markdown_output)
```

### Setup Authentication State

```bash
# 1. Launch Chrome with debugging and login
python scripts/state_manager.py setup --name google

# 2. Save authentication state
python scripts/state_manager.py save --name google

# 3. Test your search
python scripts/state_manager.py test --name google --query "your search"
```

### Why Use Real Chrome?

| Feature | Headless Browser | Real Chrome |
|---------|-----------------|-------------|
| CAPTCHA | Frequent | None (logged in) |
| Setup | Immediate | One-time setup |
| Speed | Fast | Fast |
| Privacy | Good | Uses your browser data |

---

## Usage Examples

### Finding Library Documentation

```python
from scripts import SearchEngine

engine = SearchEngine(profile="docs")
result = engine.search(
    "Prisma ORM 2026 (schema definition, migrations, client API, relations). "
    "Include TypeScript examples."
)
print(result.markdown_output)
```

### Getting Coding Examples

```python
result = engine.search(
    "WebSocket implementation Node.js 2026 (server setup, client connection, "
    "authentication, reconnection logic). Production-ready code examples."
)
```

### Technical Comparisons

```python
result = engine.search(
    "GraphQL vs REST API 2026 (performance, caching, tooling, type safety). "
    "Comparison table with benchmark data."
)
```

### Best Practices Research

```python
result = engine.search(
    "Microservices security patterns 2026 (API gateway, mTLS, secrets management, "
    "observability). Architecture diagrams."
)
```

---

## Configuration

### Profile Management

```python
from scripts import ProfileManager

# Create persistent profile
profile_mgr = ProfileManager()
profile_path = profile_mgr.create(exist_ok=True)

# Use in search
engine = SearchEngine(profile=str(profile_path))

# Reset if corrupted
profile_mgr.reset()
```

### Language Selection

```python
from scripts import LanguageSelector, Language

# Auto-detect (default)
selector = LanguageSelector()

# Force specific language
selector = LanguageSelector(Language.GERMAN)

# Get selectors for current language
citations = selector.get_citation_selectors()
```

### Error Handling

```python
from scripts import ErrorHandler, RetryConfig

# Configure retry behavior
handler = ErrorHandler(
    RetryConfig(max_retries=2, base_delay=1.0, exponential_backoff=True)
)

# Detect errors in HTML
error = handler.detect_error(html_content)
if error:
    print(handler.format_error_message(error))
```

---

## Troubleshooting

### Common Issues

| Issue | Solution |
|-------|----------|
| `ModuleNotFoundError` | Run `./setup.sh` or `pip install -r requirements.txt` |
| CAPTCHA every time | First use: solve CAPTCHA once manually, profile persists |
| No AI overview found | Rephrase query with more specificity |
| Browser fails to start | Verify internet connection and Chrome installation |
| AI Mode not available | Region not supported. Use VPN from US/UK/DE |
| Profile corrupted | Run `ProfileManager().reset()` to recreate |

### CAPTCHA Handling

If CAPTCHA is detected:

1. Use `--show-browser` flag to see the browser
2. Complete the CAPTCHA manually
3. Profile persists for future searches

### Network Issues

```python
from scripts import ErrorHandler, RetryConfig

# Increase retry count for unstable connections
handler = ErrorHandler(RetryConfig(max_retries=5, base_delay=2.0))
```

---

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                     Trae IDE                            │
└─────────────────────────────────────────────────────────┘
                            │
┌─────────────────────────────────────────────────────────┐
│                    SKILL Layer                          │
│  (SKILL.md - User Interface, Query Templates)           │
└─────────────────────────────────────────────────────────┘
                            │
┌─────────────────────────────────────────────────────────┐
│                 Search Logic Layer                      │
│  ┌─────────────────┐  ┌─────────────────┐            │
│  │ CitationExtractor│  │ LanguageSelector │            │
│  └─────────────────┘  └─────────────────┘            │
│  ┌─────────────────┐                                  │
│  │  ErrorHandler   │                                  │
│  └─────────────────┘                                  │
└─────────────────────────────────────────────────────────┘
                            │
┌─────────────────────────────────────────────────────────┐
│                Agent Browser Layer                      │
│  ┌─────────────────┐  ┌─────────────────┐            │
│  │ BrowserManager  │  │ ProfileManager  │            │
│  └─────────────────┘  └─────────────────┘            │
└─────────────────────────────────────────────────────────┘
                            │
                    agent-browser CLI
                            │
                    Google Chrome
```

---

## API Reference

### SearchEngine

```python
class SearchEngine:
    def __init__(
        self,
        browser: Optional[BrowserManager] = None,
        profile: Optional[str] = None,
        wait_time: int = 2,
        max_retries: int = 2,
    )

    def search(self, query: str) -> SearchResult
```

### CitationExtractor

```python
class CitationExtractor:
    def __init__(self, max_citations: int = 20)
    def extract_from_html(self, html: str) -> List[ExtractedCitation]
    def to_markdown_list(self, citations: List[ExtractedCitation]) -> str
```

### LanguageSelector

```python
class LanguageSelector:
    def __init__(self, language: Optional[Language] = None)
    def detect_language() -> Language
    def get_citation_selectors() -> List[str]
```

### ErrorHandler

```python
class ErrorHandler:
    def __init__(self, retry_config: Optional[RetryConfig] = None)
    def detect_error(html: str) -> Optional[ErrorReport]
    def should_retry(error: ErrorReport) -> bool
```

---

## Exit Codes

| Code | Meaning |
|------|---------|
| `0` | Success |
| `1` | General error |
| `2` | CAPTCHA required |
| `3` | AI Mode unavailable |
| `4` | Network timeout |

---

## Contributing

Contributions welcome! Please read the [AGENTS.md](AGENTS.md) for the AI collaboration protocol.

## License

MIT License - see [LICENSE](LICENSE) file for details.

---

## Related Projects

- [agent-browser](https://github.com/vercel/agent-browser) - AI-native browser automation CLI
- [Google AI Mode MCP](https://github.com/PleasePrompto/google-ai-mode-mcp) - Claude Code MCP alternative

---

<div align="center">

**Built with ❤️ for the Trae community**

</div>
